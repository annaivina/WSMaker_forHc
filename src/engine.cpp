#include "engine.hpp"

#include <RooAbsArg.h>
#include <RooAbsPdf.h>
#include <RooArgSet.h>
#include <RooConstVar.h>
#include <RooLinkedListIter.h>
#include <RooPoisson.h>
#include <RooRealSumPdf.h>
#include <RooRealVar.h>
#include <RooStats/ModelConfig.h>
#include <RooWorkspace.h>
#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <iterator>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include <TDirectory.h>
#include <TError.h>
#include <TFile.h>
#include <TH1.h>
#include <TIterator.h>
#include <TObject.h>
#include <TString.h>

#include "analysis.hpp"
#include "analysishandler.hpp"
#include "category.hpp"
#include "categoryhandler.hpp"
#include "configuration.hpp"
#include "outputhandler.hpp"
#include "postprocessing.hpp"
#include "properties.hpp"
#include "sample.hpp"
#include "samplehandler.hpp"
#include "sampleincategory.hpp"
#include "systematic.hpp"
#include "systematichandler.hpp"

class RooAbsData;

void Engine::MakeIt()
{

  gErrorIgnoreLevel = 1001;
  std::cout << "INFO::Engine::MakeIt:" << std::endl;
  std::cout << "  Starting." << std::endl;

  // first run through everything to get nominal histograms

  // add potentially user-defined vetos, i.e not use some samples for some categories
  // SysConfig objects can be used for that aim
  std::vector<SysConfig> vetos;
  // do not use multijet in 1 lepton inputs, but use multijetEl and multijetMu
  if( Configuration::analysisType() == AnalysisType::VHbb )
    vetos.emplace_back(SysConfig("multijet", {{Property::nLep, 1}}));
  // vetos.emplace_back(SysConfig("Sig", {{Property::nTag, 1}}));
  if( Configuration::analysisType() == AnalysisType::VHbbRun2 ||
      Configuration::analysisType() == AnalysisType::boostedVHbbRun2 ) {
    if( m_config.getValue("DataDrivenTTbar2L", false) ) {
      vetos.emplace_back(SysConfig("ttbar", {{Property::nLep, 2}}));
      vetos.emplace_back(SysConfig("stopt", {{Property::nLep, 2}}));
      vetos.emplace_back(SysConfig("stops", {{Property::nLep, 2}}));
      vetos.emplace_back(SysConfig("stopWt", {{Property::nLep, 2}}));
    }
  }

  for( auto& cat : m_categories ) {
    for( auto& spair : m_samples ) {
      Sample& s    = spair.second;
      bool    veto = std::any_of(std::begin(vetos), std::end(vetos), [&s, &cat](const SysConfig& v) {
        return SystematicHandler::match(s, v) && SystematicHandler::match(cat, v);
         });
      std::cout << "In: " << cat.name() << " - " << spair.second.name() << std::endl;
      if( m_config.debug() )
        std::cout << "INFO::Engine::MakeIt:In region " << cat.name() << " detect sample " << spair.second.name()
                  << std::endl;
      if( !veto && !s.isVetoedIn(cat) ) {
        if( m_config.debug() )
          std::cout << "                   not vetoed => try get" << std::endl;
        cat.tryAddSample(s);
      }
    }
  }

  std::cout << "INFO::Engine::MakeIt:" << std::endl;
  std::cout << "  All nominal samples are added." << std::endl;
  std::cout << "  Now will compute binning and some statistics." << std::endl;

  // setup things: compute rebinnings, and whatever values may be useful
  m_categories.finalizeNominal();
  m_samples.finalizeNominal();

  std::cout << "INFO::Engine::MakeIt:" << std::endl;
  std::cout << "  Binnings and statistics computed." << std::endl;
  std::cout << "  Now will make control plots." << std::endl;

  m_categories.makeControlPlots();

  std::cout << "INFO::Engine::MakeIt:" << std::endl;
  std::cout << "  Plots made." << std::endl;

  bool mergeSamples = m_config.getValue("MergeSamples", false);
  if( mergeSamples ) {
    std::cout << "  Now will prepare the merging of some samples." << std::endl;
    m_samples.declareSamplesToMerge();
    std::cout << "INFO::Engine::MakeIt:" << std::endl;
    std::cout << "  Preparation done.." << std::endl;
  }
  std::cout << "  Now will fill lists of systematics." << std::endl;

  bool useSysts         = m_config.getValue("UseSystematics", true);
  bool useFloatingNorms = m_config.getValue("UseFloatNorms", true);

  // now define all systematics we will need
  m_systematics.listAllHistoSystematics();
  // note the following one also defines the POIs
  m_systematics.listAllUserSystematics(useFloatingNorms);

  std::cout << "INFO::Engine::MakeIt:" << std::endl;
  std::cout << "  Systematics lists complete." << std::endl;
  if( useSysts ) {
    std::cout << "  Now will compute normalization factors for systs with \"normalize\" option." << std::endl;
    m_systematics.ComputeNormalizationFactors();
    std::cout << " All normalizing factor for systs are added." << std::endl;
    std::cout << "INFO::Engine::MakeIt:" << std::endl;
  }
  std::cout << "  Now will apply the POIs." << std::endl;
  std::set<TString> POIsNames;
  for( const auto& sysconfig : m_systematics.POIs() ) {
    auto poiNames = m_samples.addUserSyst(sysconfig.first, sysconfig.second);
    POIsNames.insert(poiNames.begin(), poiNames.end());
  }

  TString decorrSys = m_config.getValue("DecorrSys", "None");
  if( decorrSys != "None" ) {
    std::cout << "INFO: Trying to decorrelate systematic: " << decorrSys.Data() << std::endl;
    std::vector<TString>              decorrTypes = m_config.getStringList("DecorrTypes");
    std::vector<Properties::Property> props;
    for( auto& d : decorrTypes ) {
      props.push_back(Properties::props_from_names.at(d));
    }
    if( props.size() > 0 ) {
      m_systematics.decorrSysForCategories(decorrSys, props, false);
    } else {
      std::cout << "WARNING: No DecorrTypes filled to decorrelate systematic: " << decorrSys.Data() << std::endl;
    }
  }

  std::cout << "INFO::Engine::MakeIt:" << std::endl;
  std::cout << "  POIs have been applied to relevant samples." << std::endl;

  if( useSysts || useFloatingNorms ) {

    std::cout << "INFO::Engine::MakeIt:" << std::endl;
    std::cout << "  Now will apply user-defined systematics." << std::endl;

    // apply user-defined systematics
    for( const auto& sysconfig : m_systematics.userSysts() ) {
      const Systematic& sys = sysconfig.first;
      // if useFloatingNorms only, drop everything except flt systs
      if( useFloatingNorms && !useSysts && sys.type != SysType::flt ) {
        continue;
      }
      auto sysNames = m_samples.addUserSyst(sys, sysconfig.second);
      if( sys.isConst ) {
        auto& cNF = m_systematics.constNormFacts();
        cNF.insert(cNF.end(), sysNames.begin(), sysNames.end());
      }
    }

    std::cout << "INFO::Engine::MakeIt:" << std::endl;
    std::cout << "  User-defined systematics applied, except 3/2 ratios." << std::endl;

    if( useSysts ) {

      for( const auto& sysconfig : m_systematics.ratios32() ) {
        m_samples.add32Syst(sysconfig);
      }

      std::cout << "INFO::Engine::MakeIt:" << std::endl;
      std::cout << "  3/2 systematics applied." << std::endl;
    }
    // apply MC stat systematics
    for( auto& sysconfig : m_systematics.MCStatSysts() ) {
      m_samples.addMCStatSyst(sysconfig);
    }
    std::cout << "INFO::Engine::MakeIt:" << std::endl;
    std::cout << "  MC stat systematics applied." << std::endl;
  }

  std::cout << "INFO::Engine::MakeIt:" << std::endl;
  std::cout << "  Will now loop on categories." << std::endl;

  bool lumiWhenFloat = m_config.getValue("LumiForAll", true);
  bool skipUnknown   = m_config.getValue("SkipUnkownSysts", false);
  bool doShapePlots  = m_config.getValue("DoShapePlots", false);
  bool doPruneSyst   = m_config.getValue("DoPruneSyst", true);
  if( !useSysts ) {
    doPruneSyst = false;
  }
  bool pruneAfterMerge       = m_config.getValue("PruneAfterMerge", false);
  bool smoothAfterMerge      = m_config.getValue("SmoothAfterMerge", false);
  bool symmetriseAfterSmooth = m_config.getValue("SymmetriseAfterSmooth", false);

  for( auto& c : m_categories ) {
    std::cout << "INFO::Engine::MakeIt:" << std::endl;
    std::cout << "  In category " << c.name() << " ..." << std::endl;
    if( useSysts ) {
      std::cout << "INFO::Engine::MakeIt:" << std::endl;
      std::cout << "  Now will apply histo systematics." << std::endl;
      // apply histo systs
      c.applyHistoSysts(m_systematics, skipUnknown);

      // Loop over the samples in category and ...
      for( auto& sampleitr : c.samples() ) {
        SampleInCategory& sic = sampleitr.second;

        // remove lumi on floated samples if that is requested
        if( !lumiWhenFloat )
          sic.removeLumiWhenFloat();

        // Symmetrise and/or average systematics before smoothing
        if( !symmetriseAfterSmooth ) {
          sic.symmetriseAverageSysts();
        }

        // then smooth systs at this point if requested
        if( !smoothAfterMerge ) {
          sic.smoothSysts();
          if( symmetriseAfterSmooth ) {
            sic.symmetriseAverageSysts();
          }
        }
      }

      // apply pruning before merging if requested
      if( !pruneAfterMerge && doPruneSyst ) {
        ApplyPruning(c);
      }
    }

    std::cout << "INFO::Engine::MakeIt:" << std::endl;
    std::cout << "  Now will merge samples in this category." << std::endl;
    // then merging of samples
    m_samples.mergeSamplesInCategory(c);

    // Compute MC stat histograms after merging
    c.computeMCStatUncertHist();

    // smooth systs after merging if requested
    if( smoothAfterMerge ) {
      for( auto& sampleitr : c.samples() ) {
        SampleInCategory& sic = sampleitr.second;
        sic.smoothSysts();
        if( symmetriseAfterSmooth ) {
          sic.symmetriseAverageSysts();
        }
      }
    }

    // apply pruning after merging if requested
    if( pruneAfterMerge && doPruneSyst ) {
      ApplyPruning(c);
    }

    std::cout << "INFO::Engine::MakeIt:" << std::endl;
    std::cout << "  All systematics collected and pruned in category " << c.name() << "." << std::endl;
    if( Configuration::debug() ) {
      std::cout << "INFO::Engine::MakeIt:" << std::endl;
      std::cout << "  Dump of all systematics after pruning." << std::endl;
      // Some pretty print of all systs that remain
      for( auto& sampleitr : c.samples() ) {
        SampleInCategory& sic = sampleitr.second;
        sic.printSystematics();
      }
    }

    if( doShapePlots ) {
      std::cout << "INFO::Engine::MakeIt:" << std::endl;
      std::cout << "  Plotting of systematic shapes requested! So doing it..." << std::endl;
      std::cout << "  for category " << c.name() << std::endl;
      m_categories.makeSystShapePlots(c);
      std::cout << "INFO::Engine::MakeIt:" << std::endl;
      std::cout << "  Systematic shape plots done." << std::endl;
    } else if( m_config.getValue("SmoothingControlPlots", false) ) {
      std::cout << "INFO::Engine::MakeIt:" << std::endl;
      std::cout << "  Chi2 of sys vs. nom are being cached." << std::endl;
      m_categories.makeChi2TestsForSysts(c);
    }

    std::cout << "INFO::Engine::MakeIt:" << std::endl;
    std::cout << "  Check: do we have systematics with same-sign effect on the sum of backgrounds ?." << std::endl;
    c.checkSameSignSysts();

    std::cout << "INFO::Engine::MakeIt:" << std::endl;
    std::cout << "  Now will write all the stuff to XML and norm files." << std::endl;
    m_categories.writeNormAndXMLForCat(c);

    std::cout << "INFO::Engine::MakeIt:" << std::endl;
    std::cout << "  End of treatment for category " << c.name() << "." << std::endl;
    m_categories.clearSystHistos(c);
  } // Loop on categories

  m_samples.finishMerging();

  std::cout << "INFO::Engine::MakeIt:" << std::endl;
  std::cout << "  Done for all systematics." << std::endl;

  if( m_config.getValue("DoSystsPlots", false) ) {
    std::cout << "INFO::Engine::MakeIt:" << std::endl;
    std::cout << "  Now will print summary plots of systematics." << std::endl;
    m_categories.makeSystStatusPlots();
  }

  std::cout << "INFO::Engine::MakeIt:" << std::endl;
  std::cout << "  Plots made." << std::endl;
  std::cout << "  Now will collect the XML and write the driver file." << std::endl;

  // now save everything in norm file
  // and write XML at the same time
  // needs to delegate this to m_categories so that it produces a nice driver file
  auto driverAndWS = m_categories.writeNormAndXML(m_systematics.constNormFacts(), POIsNames);

  std::cout << "INFO::Engine::MakeIt:" << std::endl;
  std::cout << "  Writing done." << std::endl;
  std::cout << "  Now will call hist2workspace." << std::endl;

  std::system(("hist2workspace -standard_form " + driverAndWS.first +
               " | grep -v \"INFO\" |grep -v \"RooHistFunc\" | grep -v \"RooGaussian\" | sed -e \"/Making "
               "OverallSys/,+1D\"|sed -e \"/Making HistoSys/,+1D\"|grep -v \"Writing sample\" | sed -e\"/Getting "
               "histogram/,+1D\" ")
                  .Data());

  std::cout << "INFO::Engine::MakeIt:" << std::endl;
  std::cout << "  Workspace generated." << std::endl;
  std::cout << "  Now will do some modifications and move stuff around." << std::endl;

  auto pimped_WS = PimpMyWS(driverAndWS.second);
  PostProcessingTool::getInstance().process(pimped_WS);

  std::cout << "INFO::Engine::MakeIt:" << std::endl;
  std::cout << "  All Done !" << std::endl;
  std::cout << "  Now will clean our mess." << std::endl;

  // remove useless temporary root files in xml dir
  OutputConfig* outConf = OutputConfig::getInstance();
  std::system(("rm -rf " + outConf->xmlDir + "/*.root").Data());
}

TString Engine::PimpMyWS(const TString& wsfilename)
{
  using namespace RooStats;

  TFile* wsFile = TFile::Open(wsfilename);
  if( !wsFile || wsFile->IsZombie() ) {
    std::cout << "ERROR::Engine::PimpMyWS: Problem opening file " << wsfilename << std::endl;
    throw;
  }

  RooWorkspace* w = nullptr;
  wsFile->GetObject("combined", w);
  if( !w ) {
    std::cout << "ERROR::Engine::PimpMyWS: Cannot find RooWorkspace in " << wsfilename << std::endl;
    throw;
  }
  ModelConfig* mc = dynamic_cast<ModelConfig*>(w->obj("ModelConfig"));
  if( !mc ) {
    std::cout << "ERROR::Engine::PimpMyWS: Cannot find ModelConfig in " << wsfilename << std::endl;
    throw;
  }

  // make sure floating norms are at nominal value of 1
  const RooArgSet* list = mc->GetNuisanceParameters();
  if( list != nullptr ) {
    TIterator*  itr = list->createIterator();
    RooRealVar* arg = 0;
    while( (arg = (RooRealVar*)itr->Next()) ) {
      if( !arg )
        continue;
      if( TString(arg->GetName()).Contains("ATLAS_norm") ) {
        arg->setVal(1);
      }
      if( TString(arg->GetName()).Contains("gamma") ) {
        arg->setVal(1);
      }
      if( TString(arg->GetName()).Contains("DT4") ) {
        arg->setVal(1);
        arg->setConstant(kTRUE);
      }
    }
  }

  // make sure that ranges of protection gammas cover 1 sigma
  if( list != nullptr ) {
    TIterator*  itr = list->createIterator();
    RooRealVar* arg = 0;
    while( (arg = (RooRealVar*)itr->Next()) ) {
      std::string gamma_name = arg->GetName();
      if( gamma_name.find("gamma") != std::string::npos ) {
        RooAbsPdf* constraint_term = (RooAbsPdf*)w->pdf((gamma_name + "_constraint").c_str());
        if( constraint_term && typeid(*constraint_term) == typeid(RooPoisson) ) {
          RooConstVar* var_tau = (RooConstVar*)w->obj((gamma_name + "_tau").c_str());
          double       tau     = var_tau->getVal();
          if( tau < 0.9 ) {
            // This is a protection gamma
            arg->setMax(1. / tau); // <= -ln(exp(-tau*gamma)) = 1.0
          }
        }
      }
    }
  }

  // Activate binned likelihood calculation for binned models
  RooFIter   iter = w->components().fwdIterator();
  RooAbsArg* argu;
  while( (argu = iter.next()) ) {
    if( argu->IsA() == RooRealSumPdf::Class() ) {
      argu->setAttribute("BinnedLikelihood");
    }
  }

  // save snapshot before any fit has been done
  // TODO do we really need this ?
  RooAbsPdf*  simPdf = w->pdf("simPdf");
  RooAbsData* data   = w->data("obsData");
  RooArgSet*  params = simPdf->getParameters(*data);
  if( !w->loadSnapshot("snapshot_paramsVals_initial") ) {
    w->saveSnapshot("snapshot_paramsVals_initial", *params);
  }

  // write to file
  // TODO Is this still needed?
  gDirectory->RecursiveRemove(w);

  TString massPoint = m_config.getValue("MassPoint", "125");
  TString outFileName(OutputConfig::getInstance()->workspaceDir + "/" + massPoint + ".root");
  w->writeToFile(outFileName);

  wsFile->Close();

  TFile*      outFile = TFile::Open(outFileName, "UPDATE");
  TDirectory* binDir  = outFile->mkdir("binning");
  std::cout << "Write binning hists" << std::endl;
  for( auto& cat : m_categories ) {
    std::cout << "\t" << cat.name() << std::endl;
    cat.writeBinHist(binDir);
  }
  binDir->Write();
  outFile->Close();
  // delete binDir;
  // delete outFile;

  return outFileName;
}

void Engine::ApplyPruning(Category& c)
{
  bool  htt_pruning           = m_config.getValue("HTauTauPruning", false);
  float shapePruningThreshold = 0.005;
  if( Configuration::analysisType() == AnalysisType::AZh )
    shapePruningThreshold = 0.01;
  else if( (Configuration::analysisType() == AnalysisType::VHbbRun2 ||
            Configuration::analysisType() == AnalysisType::VHqqRun2 ||
            Configuration::analysisType() == AnalysisType::boostedVHbbRun2) &&
           m_config.getValue("CutBasePostfit", false) )
    shapePruningThreshold = 0.01;
  float normPruningThreshold = 0.005;
  if( (Configuration::analysisType() == AnalysisType::VHbbRun2 ||
       Configuration::analysisType() == AnalysisType::VHqqRun2 ||
       Configuration::analysisType() == AnalysisType::boostedVHbbRun2) &&
      m_config.getValue("CutBasePostfit", false) )
    normPruningThreshold = 0.01;

  if( Configuration::analysisType() == AnalysisType::SemileptonicVBS ) {
    normPruningThreshold  = m_config.getValue("NormPruningThreshold", 0.01);
    shapePruningThreshold = m_config.getValue("ShapePruningThreshold", 0.01);
  }

  // First, simple pruning sample by sample
  std::cout << "INFO::Engine::MakeIt:" << std::endl;
  std::cout << "  Now will prune systematics for this category." << std::endl;
  if( Configuration::debug() ) {
    std::cout << "   * Starting with simple pruning sample by sample." << std::endl;
  }

  for( auto& sampleitr : c.samples() ) {
    SampleInCategory& sic = sampleitr.second;
    // Simple pruning
    sic.pruneSmallShapeSysts(shapePruningThreshold);
    sic.pruneOneSideShapeSysts();
    sic.pruneSmallNormSysts(normPruningThreshold);
    sic.pruneSameSignSysts();

    // sic.pruneSmallShapeSysts_chi2();
    sic.pruneSmallShapeSysts_chi2_samesign();
    sic.pruneSpecialTests();
  }
  // Then pruning at the cotegory level
  if( Configuration::debug() ) {
    std::cout << "   * Moving to category-level pruning." << std::endl;
  }
  if( Configuration::analysisType() == AnalysisType::VHbb || Configuration::analysisType() == AnalysisType::VHbbRun2 ||
      Configuration::analysisType() == AnalysisType::VHqqRun2 ||
      Configuration::analysisType() == AnalysisType::boostedVHbbRun2 ) {
    c.pruneSmallSysts_Yao();
  }
  if( htt_pruning ) {
    c.pruneSmallShapeSysts_Htautau();
  }
}

Engine::Engine(const TString& confFileName, const TString& version, std::unique_ptr<Analysis>&& ana) :
    m_config(confFileName, version),
    m_analysis(std::move(ana)),
    m_samples(m_config),
    m_categories(m_config),
    m_systematics(m_config)
{
  // initialize properly the binning tool once and for all
  AnalysisHandler::analysis().createBinningTool(m_config);
  // initialize the postprocessing tool
  AnalysisHandler::analysis().createPostProcessingTool(m_config);
  // ... and the output config
  OutputConfig::createInstance(m_config);

  // Because ROOT is stupid
  // Let's take care of deleting the TH1s ourselves
  // At least we won't spend ages in THashList::RecursiveRemove
  TH1::AddDirectory(false);
}

Engine::~Engine()
{
  // get rid of the singletons
  OutputConfig::destruct();
}
