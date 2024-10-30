#include "category.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <set>
#include <string>
#include <unordered_map>
#include <utility>

#include <TAxis.h>
#include <TCanvas.h>
#include <TDirectory.h>
#include <TH1.h>
#include <TH2.h>
#include <TString.h>

#include "analysis.hpp"
#include "analysishandler.hpp"
#include "binning.hpp"
#include "configuration.hpp"
#include "finder.hpp"
#include "inputshandler.hpp"
#include "outputhandler.hpp"
#include "properties.hpp"
#include "sample.hpp"
#include "sampleincategory.hpp"
#include "systematic.hpp"
#include "systematichandler.hpp"
#include "utility.hpp"

Category::Category(const Configuration& conf, PropertiesSet&& pset) :
    m_config(conf),
    m_properties(std::move(pset)),
    m_input(AnalysisHandler::analysis().inputsHandler(m_config, m_properties)),
    m_out(),
    m_hsob(nullptr),
    m_binHist(nullptr)
{
  if( Configuration::debug() ) {
    std::cout << "INFO::Category: Building new Category with given properties tag:" << std::endl;
    std::cout << name() << std::endl << std::endl;
  }
}

int Category::getIntProp(const Property p) const { return m_properties.getIntProp(p); }

TString Category::getStringProp(const Property p) const { return m_properties.getStringProp(p); }

int Category::requestIntProp(const Property p) const { return m_properties.requestIntProp(p); }

TString Category::requestStringProp(const Property p) const { return m_properties.requestStringProp(p); }

void Category::setIntProp(Property p, int i) { m_properties.setProp(p, i); }

void Category::setStringProp(Property p, const TString& s) { m_properties.setProp(p, s); }

TString Category::name() const
{
  TString res = "Region";
  res += m_properties.getPropertiesTag();
  return res;
}

bool Category::exists() { return m_input->exists(); }

void Category::tryAddSample(Sample& s)
{
  TH1* hist = m_input->getHist(s, "");
  if( hist == nullptr ) {
    // TODO add some logging
    return;
  }
  if( TString(hist->GetName()).Contains("correlation_histogram") )
    return;
  TH2* corr =
      (TH2*)m_input->getHist(Sample(Form("%s_correlation_histogram", hist->GetName()), Sample::Type::None, 0), "");
  if( Configuration::analysisType() == AnalysisType::VHbb ) {
    // FIXME
    // hack for bug in CorrsAndSysts. 6% scaling applied on Wl and Wcl is wrong.
    if( s.name() == "Wcl" || s.name() == "Wl" ) {
      if( getIntProp(Property::bin) < 2 && getIntProp(Property::nJet) == 3 ) {
        hist->Scale(0.94);
      }
    }
  }

  double err;
  float  sum = hist->IntegralAndError(1, hist->GetNbinsX(), err);

  //
  // Don't throw away any signal - for fit cross-checks
  // sometimes dummy signals with zero integral are needed. PR.
  //
  if( s.type() != SType::Data && sum < 1.e-9 && s.type() != SType::Sig ) {
    // TODO add some proper logging
    std::cout << "WARNING::Nominal rate very small: " << s.name() << std::endl;
    std::cout << "Ignoring this sample in this channel" << std::endl;
    return;
  }

  if( s.type() != SType::Data && fabs(err) > 1.01 * fabs(sum) &&
      Configuration::analysisType() != AnalysisType::AZh ) { // don't do this for AZh
    // TODO add some proper logging
    std::cout << "WARNING::Nominal rate compatible with 0 within MC stat error: " << s.name() << std::endl;
    std::cout << "Ignoring this sample in this channel" << std::endl;
    return;
  }

  // there is an histogram for this sample, so just use it
  // SampleInCategory sic(*this, s, hist);
  SampleInCategory sic(*this, s, hist, corr);
  auto             sicpair = samples().emplace(&s, std::move(sic));
  s.categories().emplace(this, &(sicpair.first->second)); // add pointer to the SiC in Sample s
}

bool Category::match(const PropertiesSet& pset) const { return m_properties.match(pset); }

bool Category::hasSensitiveBinAbove(float thresh) const
{
  // compare max of S/B histo with thresh
  float maxSoB = getSoBHist()->GetBinContent(getSoBHist()->GetMaximumBin());
  return (maxSoB > thresh);
}

TH1* Category::getSigHist() const { return getHist(SType::Sig); }

TH1* Category::getBkgHist() const
{
  TH1* hbkg = getHist(SType::Bkg);
  TH1* hdd  = getHist(SType::DataDriven);
  if( hbkg != nullptr && hdd != nullptr ) {
    hbkg->Add(hdd);
    delete hdd;
    return hbkg;
  }
  if( hbkg == nullptr )
    return hdd;
  if( hdd == nullptr )
    return hbkg;
  return nullptr;
}

TH1* Category::getDataHist() const { return getHist(SType::Data); }

TH1* Category::getSoBHist() const
{
  if( m_hsob == nullptr ) {
    TH1* hsig = getSigHist();
    TH1* hbkg = getBkgHist();
    if( hbkg == nullptr ) {
      std::cout << "ERROR::Category::getSoBHist: Background is null !" << std::endl
                << "  That should not happen ! Will now exit. Please investigate the reason !" << std::endl;
    }
    if( hsig == nullptr ) {
      hbkg->Reset();
      const_cast<Category*>(this)->m_hsob = hbkg; // returns histo with 0 everywhere
    } else {
      hsig->Divide(hbkg);
      delete hbkg;
      const_cast<Category*>(this)->m_hsob = hsig;
    }
  }

  return m_hsob;
}

TH1* Category::getHist(const Sample& s, const TString& sysname) const
{
  TH1* hist = m_input->getHist(s, sysname);
  return hist;
}

TH1* Category::getHist(SType type) const
{
  TH1* hist = nullptr;
  if( !SampleIndex::has(type) ) {
    return hist;
  }
  const std::set<Sample*>& samples = SampleIndex::findAll(type);
  for( const auto& s : samples ) {
    const auto& pos = m_samples.find(s);
    if( pos == m_samples.end() ) { // this sample is not present for this category
      continue;
    }
    const SampleInCategory& sic = pos->second;
    if( hist == nullptr ) {
      hist = (TH1*)(sic.getNomHist()->Clone());
    } else {
      hist->Add(sic.getNomHist());
    }
  }
  return hist;
}

void Category::finalizeNominal()
{
  if( Configuration::debug() ) {
    std::cout << "INFO::Category: In category " << name() << std::endl << std::endl;
  }

  BinningTool& binning = BinningTool::getInstance();
  // adapt range
  for( auto& sample : m_samples ) {
    binning.changeRange(sample.second.getNomHist(), *this);
  }

  // then compute binning
  m_binning  = binning.getCategoryBinning(*this);
  m_binningF = binning.p_binningF;
  setBinningHist();

  // then apply it
  for( auto& sample : m_samples ) {
    binning.applyBinning(sample.second.getNomHist(), m_binning, sample.second.getCorrHist());
    binning.changeRangeAfter(sample.second.getNomHist(), *this);
    sample.second.computeBinningForSysts();
  }
}

void Category::setBinningHist()
{
  // only 1 number: using a simple Rebin - no need for this histo
  if( m_binning.size() <= 1 ) {
    return;
  }

  // default is to rebin right to left so need to reverse order
  // first we need to make a copy
  std::vector<int> binning = m_binning;
  // check first if necessary
  if( binning.size() > 1 && (binning.at(0) > binning.at(1)) ) {
    std::reverse(binning.begin(), binning.end());
  }
  // fill a vector of doubles containing the *low-edge* of each bin
  // should have n+1 elements to get a n bin histogram
  TH1* data = getDataHist();
  int  nbin(data->GetNbinsX());
  std::cout << "nbin " << nbin << std::endl;
  std::vector<Double_t> bins;
  for( auto& b : binning ) {
    bins.push_back(data->GetXaxis()->GetBinLowEdge(b));
  }
  Double_t* binarray = bins.data(); // make array from vector
  m_binHist          = data->Rebin(m_binning.size() - 1, TString("bins_" + this->name()), binarray);
  for( int i = 0; i < m_binHist->GetNbinsX() + 2; i++ ) {
    float width = m_binHist->GetBinWidth(i);
    if( width == 0 ) {
      continue;
    }
    m_binHist->SetBinContent(i, m_binHist->GetBinContent(i) / width);
    m_binHist->SetBinError(i, m_binHist->GetBinError(i) / width);
    // now need to do m_binHist->Integral("width") to get the correct integral
  }
  //  delete data;
  //  delete binarray;
}

void Category::writeBinHist(TDirectory* dir)
{
  if( m_binHist == nullptr ) {
    return;
  }
  dir->cd();
  m_binHist->Write();
}

void Category::applyHistoSysts(const SystematicHandler& systs, bool skipUnknown)
{
  std::vector<TString> systnames = m_input->listSystematics();
  // loop on the names of the TDirectories
  for( const auto& name : systnames ) {
    auto splitSysName = Systematic::interpretSysName(name);
    // check if some config is defined for that one
    if( skipUnknown && !systs.hasHistoSysConfig(splitSysName.first) ) {
      continue;
    }
    // getHistoSysConfig returns the configuration, and also the correct syst name
    // if there is a rule to correct for splitSysName.first (e.g typo in some input file)
    auto nameconfig = systs.getHistoSysConfig(splitSysName.first);
    // check if not skip, and if this category matches the requirements
    if( (nameconfig.second.treat != STreat::skip) && SystematicHandler::match(*this, nameconfig.second) ) {
      applyOneHistoSyst(nameconfig.first, splitSysName.second, name, nameconfig.second);
    }
  }

  // Spyros: this should also be put somewhere else - I comment it out for now
  // FIXME reintroduce it as a smoothing algorithm that the user can choose
  // then apply the 'smoothing' of MV1c distributions. Can be done only now that all individual
  // shapes have been added side after side
  // if(getStringProp(Property::dist).Contains("MV1c")) {
  //  for(auto& pairsample : m_samples) {
  //    SampleInCategory& sic = pairsample.second;
  //    sic.removeSameSignBinsSysts();
  //  }
  //}
}

void Category::applyOneHistoSyst(const TString& name, const Systematic::Side side, const TString& sysname,
                                 const SysConfig& conf)
{
  BinningTool& binning = BinningTool::getInstance();

  // loop on samples for that specific syst
  for( auto& pairsample : m_samples ) {
    Sample&           sample = *(pairsample.first);
    SampleInCategory& sic    = pairsample.second;
    // check that the sample matches the requirements
    if( sample.type() == SType::Data ) {
      continue;
    }
    if( !SystematicHandler::match(sample, conf) ) {
      continue;
    }
    // try to get the shifted hist
    TH1* hsys = m_input->getHist(sample, sysname);
    // if not exist, skip
    if( hsys == nullptr )
      continue;

    // hsys->SetDirectory(0); //VD: why isn't this done here?!?!?!?
    std::shared_ptr<TH1> hsys_unsmoothed;
    if( m_config.getValue("SmoothingControlPlots", false) ) {
      hsys_unsmoothed.reset((TH1*)hsys->Clone((hsys->GetName() + std::string("_unsmoothed")).c_str()));
      (hsys_unsmoothed.get())->SetDirectory(0);
    }

    // then rebin the histo for this category
    binning.changeRange(hsys, *this);
    // FIXME: JWH - should pass in correlation hist?
    binning.applyBinning(hsys, m_binning);
    binning.changeRangeAfter(hsys, *this);

    // we will do something here to reduce the histSys systematics
    bool ScaleSystematics = m_config.getValue("ScaleSystematics", false);
    if( ScaleSystematics ) {
      // double reducing_factor = 0.5;
      double reducing_factor = getSystematicScalingFactor(hsys->GetName());
      TH1*   nom_hist        = (TH1*)(sic.getNomHist()->Clone());
      if( nom_hist == nullptr ) {
        std::cout << "WARNING::Category::applyOneHistoSyst: the nominal hist not found for : " << hsys->GetName()
                  << std::endl;
      } else {
        int nBins_sys = hsys->GetNbinsX();
        int nBins_nom = nom_hist->GetNbinsX();
        // std::cout << "HistScale investigate: the nBins of the nom is : " << nBins_nom << std::endl;
        // std::cout << "HistScale investigate: the nBins of the sys is : " << nBins_sys << std::endl;
        if( nBins_sys != nBins_nom ) {
          std::cout
              << "ERROR::Category::applyOneHistoSyst: number of bins from nominal not equal to the one of systematics"
              << std::endl;
          exit(1);
        } else {
          for( int i = 1; i < nBins_nom + 1; ++i ) {
            double val_nom = nom_hist->GetBinContent(i);
            double val_sys = hsys->GetBinContent(i);
            val_sys        = val_nom + (val_sys - val_nom) * reducing_factor;
            hsys->SetBinContent(i, val_sys);
          }
        }
      }
    }

    const auto& pos = conf.normalizeRegionsFactors.find(&sic);
    if( pos != conf.normalizeRegionsFactors.end() ) {
      auto& integrals       = pos->second;
      float reducing_factor = 1.;
      std::cout << "INFO::Category::applyOneHistoSyst: Applying scaling factor to : " << sysname << " sample "
                << sample.name() << std::endl;
      if( side == Systematic::Side::up )
        reducing_factor = integrals.first;
      else
        reducing_factor = integrals.second;

      // now scale the hists
      hsys->Scale(1. / reducing_factor);
      if( hsys_unsmoothed )
        hsys_unsmoothed->Scale(1. / reducing_factor);
    }

    if( hsys_unsmoothed ) {
      binning.changeRange(hsys_unsmoothed.get(), *this);
      // FIXME: JWH - should pass in correlation hist?
      binning.applyBinning(hsys_unsmoothed.get(), m_binning);
      binning.changeRangeAfter(hsys_unsmoothed.get(), *this);
    }

    // We have a clean histo. Now the SiC knows how to translate it into proper systematics
    TString finalSysName = name + conf.getDecorrelationTag(m_properties, sample);

    sic.addSyst(finalSysName, side, conf.treat, hsys, conf.getSmoothingAlg(properties(), sample),
                conf.getSymAlg(properties(), sample), hsys_unsmoothed, conf.scaleFactor);
  }
}

TString Category::writeNormAndXML()
{
  std::cout << "INFO::Category::writeNormAndXML:" << std::endl;
  std::cout << "Will now write Norm and XML files for category: " << name() << std::endl;
  std::cout << "..." << name() << std::endl;
  m_out               = OutputHandler(*this);
  bool  useStatSysts  = m_config.getValue("UseStatSystematics", true);
  float statThreshold = m_config.getValue("StatThreshold", 0.05);
  // DTD is: data, then staterrorconfig, then other samples
  const std::set<Sample*>& vdata = SampleIndex::findAll(SType::Data);
  for( auto& d : vdata ) {
    m_samples.at(d).writeNormAndXML(m_out, useStatSysts);
  }

  if( useStatSysts ) {
    m_out.addMCStatThresh(statThreshold);
  }

  for( auto& sicpair : m_samples ) {
    if( !(sicpair.first->type() == SType::Data) ) {
      sicpair.second.writeNormAndXML(m_out, useStatSysts);
    }
  }
  std::cout << "Files written." << name() << std::endl;
  return m_out.closeFiles();
}

// Complex pruning schemes
// This one is based on studies by Yao.
// See the presentation: https://indico.cern.ch/event/266160/contributions/1602233/attachments/474839/657197/Yao_0922.pdf
// Remove systs for samples that are small wrt signal and small wrt other backgrounds.

void Category::pruneSmallSysts_Yao()
{
  TH1*             bkg(getBkgHist());
  TH1*             sig(getSigHist());
  float            threshold         = 0.02;
  bool             isSensitiveRegion = hasSensitiveBinAbove(threshold);
  std::vector<int> sensitiveBins;
  if( isSensitiveRegion ) {
    for( int i = 1; i < sig->GetNbinsX() + 1; ++i ) {
      if( sig->GetBinContent(i) > threshold * bkg->GetBinContent(i) ) {
        sensitiveBins.push_back(i);
      }
    }
  }

  for( auto& couple : m_samples ) {
    couple.second.pruneSmallSysts_Yao(sig, bkg, isSensitiveRegion, sensitiveBins);
  }

  delete bkg;
  delete sig;
}

void Category::pruneSmallShapeSysts_Htautau()
{
  TH1* bkg(getBkgHist());
  for( auto& couple : m_samples ) {
    couple.second.pruneSmallShapeSysts_Htautau(bkg);
  }
  delete bkg;
}

void Category::checkSameSignSysts() const
{
  OutputConfig* outconfig = OutputConfig::getInstance();
  system("mkdir -vp " + outconfig->plotDir + "/suspicious");
  TString plotsformat(m_config.getValue("PlotsFormat", "eps"));

  bool useAlsoRootFormat(m_config.getValue("CreateROOTfiles", false));

  bool doShapePlots = m_config.getValue("DoShapePlots", false);

  std::vector<const SampleInCategory*> sics{};

  for( auto& spair : m_samples ) {
    if( spair.first->type() == SType::Bkg || spair.first->type() == SType::DataDriven ) {
      sics.push_back(&(spair.second));
    }
  }

  // Ok. Now let's get the full list of systematics of these samples in this category
  std::set<TString> systs{};
  for( auto sic : sics ) {
    const auto shapesysts = sic->getUsedSysts(SysType::shape);
    const auto normsysts  = sic->getUsedSysts(SysType::norm);
    systs.insert(shapesysts.begin(), shapesysts.end());
    systs.insert(normsysts.begin(), normsysts.end());
  }

  // Get the nominal hist

  TH1* hnominal = getBkgHist();

  // And now the loop on systematics
  for( auto& s : systs ) {
    TH1* hup = (TH1*)(hnominal->Clone("hup"));
    hup->Reset();
    TH1* hdo = (TH1*)(hnominal->Clone("hdo"));
    hdo->Reset();

    for( auto sic : sics ) {
      TH1* hsicup = sic->getFullSystShape(s, Systematic::Side::up);
      hup->Add(hsicup);
      delete hsicup;
      TH1* hsicdo = sic->getFullSystShape(s, Systematic::Side::down);
      hdo->Add(hsicdo);
      delete hsicdo;
    }

    // Now we can check, and shout if there are problems
    bool hasSameSign = false;
    for( int i = 1; i < hnominal->GetNbinsX() + 1; i++ ) {
      float vnom = hnominal->GetBinContent(i);
      float vup  = hup->GetBinContent(i);
      float vdo  = hdo->GetBinContent(i);
      if( (vup - vnom) * (vdo - vnom) > 0 ) {
        std::cout << "    In category: " << name() << " Systematic: " << s << " has same-sign effect in bin: # " << i
                  << " with values (do:nom:up): " << vdo << ":" << vnom << ":" << vup << std::endl;
        hasSameSign = true;
      }
    }

    // In case there were problems, draw the histogram
    if( doShapePlots ) {
      TCanvas can(name() + "_" + s);
      hnominal->SetStats(0);
      hnominal->SetLineColor(1);
      hnominal->Draw("hist");
      hup->SetLineColor(4);
      hup->Draw("histsame");
      hdo->SetLineColor(2);
      hdo->Draw("histsame");
      if( hasSameSign ) {
        can.Print(outconfig->plotDir + "/suspicious/" + name() + "_" + s + "." + plotsformat);
        if( useAlsoRootFormat )
          can.Print(outconfig->plotDir + "/suspicious/" + name() + "_" + s + ".root");
      }
      can.Print(outconfig->plotDir + "/shapes/" + name() + "_" + s + "." + plotsformat);
      if( useAlsoRootFormat )
        can.Print(outconfig->plotDir + "/shapes/" + name() + "_" + s + ".root");

      TCanvas can2(name() + "_" + s + "_ratio");
      can2.SetGridy();
      hup->SetStats(0);
      hup->GetYaxis()->SetRangeUser(0.8, 1.2);
      hup->Divide(hnominal);
      hup->Draw("hist");
      hdo->Divide(hnominal);
      hdo->Draw("histsame");
      if( hasSameSign ) {
        can2.Print(outconfig->plotDir + "/suspicious/" + name() + "_" + s + "_ratio." + plotsformat);
      }
      can2.Print(outconfig->plotDir + "/shapes/" + name() + "_" + s + "_ratio." + plotsformat);
    }

    delete hup;
    delete hdo;
  }

  delete hnominal;
}

void Category::computeMCStatUncertHist()
{

  std::map<TString, std::vector<SampleInCategory*>> sics;
  std::map<TString, std::vector<const TH1*>>        nominals;
  std::map<TString, std::vector<const TH1*>>        errors;
  double                                            epsilon = 0.001;
  for( auto& sample : m_samples ) {

    if( !sample.second.getMCStatSys() )
      continue;
    TString npname = sample.second.getMCStatSys()->name;
    sics[npname].push_back(&sample.second); // should not move
    nominals[npname].push_back(sample.second.getNomHist());
    errors[npname].push_back((TH1*)sample.second.getMCStatSys()->mc_stat_error_absolute_sample.get());
    // protection
    TH1* nominal = sample.second.getNomHist();
    for( int ibin = 1; ibin <= nominal->GetNbinsX(); ++ibin ) {
      // std::cout << "computeMCStatUncertHist " << nominal->GetName() << " " << nominal->GetTitle() << "(" << nominal
      // <<  ") ibin:" << ibin << std::endl;
      if( fabs(nominal->GetBinContent(ibin)) < 0.0001 ) {
        // std::cout << "Apply protection" << std::endl;
        nominal->SetBinContent(ibin, epsilon);
      }
    }
  }
  for( auto& vsic : sics ) { // loop over gamma NP
    TString                 npname = vsic.first;
    std::vector<const TH1*> vnom   = nominals.at(npname);
    std::vector<const TH1*> verr   = errors.at(npname);
    std::shared_ptr<TH1>    relerr_final(Utils::GetSystRatioForQuadrature(vnom, verr));
    // protection
    for( int ibin = 1; ibin <= relerr_final->GetNbinsX(); ++ibin ) {
      if( fabs(relerr_final->GetBinContent(ibin)) < 0.0001 ) {
        relerr_final->SetBinContent(ibin, 1 / sqrt(epsilon));
      }
    }
    for( auto& sic : vsic.second ) {
      sic->getMCStatSys()->mc_stat_error_fractional_shared = relerr_final;
    }
  }
}

double Category::getSystematicScalingFactor(TString sysname)
{
  double factor = 1.;
  if( Configuration::analysisType() == AnalysisType::VHbbRun2 ) {
    if( sysname.Contains("B_0") )
      factor = 0.5;
    else if( sysname.Contains("JER") )
      factor = 0.8;
  }
  return factor;
}
