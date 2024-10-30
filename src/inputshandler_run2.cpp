#include "inputshandler_run2.hpp"

#include <iostream>
#include <map>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

#include <TFile.h>
#include <TH1.h>
#include <TString.h>

#include "configuration.hpp"
#include "properties.hpp"
#include "sample.hpp"

InputsHandlerRun2::InputsHandlerRun2(const Configuration& conf, const PropertiesSet& pset) : InputsHandlerPaper()
{
  TString fname = InputsHandlerRun2::forgeFileName(conf, pset);
  m_file        = std::unique_ptr<TFile>(TFile::Open(fname));
  if( !m_file ) {
    std::cout << "Error::InputHandler:: file " << fname << " does not exist => crash" << std::endl;
    throw;
  }
  findBaseDir();

  if( conf.getValue("Analysis", "") == "VprimeHVT" ) {
    mass = conf.getValue("MassPoint", "").Data();
  }
}

InputsHandlerRun2::~InputsHandlerRun2()
{
  if( m_file != nullptr )
    m_file->Close();
}

TString InputsHandlerRun2::forgeFileName(const Configuration& conf, const PropertiesSet& pset)
{
  std::map<int, std::string> cms{{2011, "7TeV_"},  {2012, "8TeV_"},  {2015, "13TeV_"},
                                 {4031, "13TeV_"}, {2016, "13TeVmc16a_"}, {2017, "13TeVmc16d_"},
                                 {2018, "13TeVmc16e_"}, {4033, "13TeV_"}, {6051, "13TeV_"}};
  std::map<int, std::string> typeTag{{0, "CUT_"}, {1, "MVA_"}};
  std::map<int, std::string> nLepName{{0, "ZeroLepton_"}, {1, "OneLepton_"}, {2, "TwoLepton_"}};
  std::map<int, std::string> lepFlavTag{{0, "Mu_"}, {1, "El_"}};

  using P = Property;

  // FIXME This is quite a hack
  // Need just a better naming scheme for next time

  bool fitMC16aMC16d = conf.getValue("FitMC16aMC16d", false);

  TString inputVer = conf.getValue("InputVersion", "10000");
  if( fitMC16aMC16d ) {
    if( pset[P::year] == 2016 ) {
      inputVer.ReplaceAll("XXXX", "mc16a");
    } else if( pset[P::year] == 2017 ) {
      inputVer.ReplaceAll("XXXX", "mc16d");
    } else {
      inputVer.ReplaceAll("XXXX", "mc16ad");
    }
  }

  std::stringstream ss;
  ss << "inputs/";
  ss << inputVer << "/";

  // year
  ss << cms[pset[P::year]];

  // channel

  if( pset.hasProperty(Property::spec) && pset(Property::spec).Contains("Tau") ) {
    ss << pset(Property::spec) << "_";
  } else {
    ss << nLepName[pset[P::nLep]];
  }
  if( pset.hasProperty(P::lepFlav) ) {
    ss << lepFlavTag[pset[P::lepFlav]];
  }
  if( pset.hasProperty(P::type) ) {
    bool isMVA = pset.getIntProp(P::type);
    ss << typeTag[isMVA];
  }

  if( pset.hasProperty(Property::spec) && pset(Property::spec).Contains("Tau") && pset.hasProperty(P::LTT) &&
      pset[P::LTT] ) {
    ss << "LTT_";
  }

  // tag
  ss << pset[P::nTag];
  if( pset.hasProperty(P::tagType) ) {
    const TString& tagType = pset(P::tagType);
    ss << tagType;
  }
  if( pset.hasProperty(P::incTag) ) {
    ss << "p";
  }
  ss << "tag";

  // jet
  if( pset.hasProperty(P::nFatJet) ) {
    ss << pset[P::nFatJet];
    if( pset.hasProperty(P::incFat) ) {
      ss << "p";
    }
    ss << "fat";
  };
  ss << pset[P::nJet];
  if( pset.hasProperty(P::incJet) ) {
    ss << "p";
  }
  ss << "jet";
  if( pset.hasProperty(P::ntau) ) {
    std::cout <<  pset[P::ntau];
    ss << pset[P::ntau];
    if (pset.hasProperty(P::inctau)){
      ss << "p";
    }
    ss << "taus_";
  } else{
    ss << "_";
  }



  // ptv
  ss << pset[P::binMin];
  if( pset.hasProperty(P::binMax) ) {
    ss << "_" << pset[P::binMax];
  }
  ss << "ptv_";

  // descr
  const TString& descr = pset(P::descr);
  if( descr.Length() ) {
    ss << descr << "_";
  }

  // additional track jet
  if( pset.hasProperty(P::nAddTag) ) {
    if( pset[P::nAddTag] ) {
      ss << "topaddbjetcr_";
    } else {
      ss << "noaddbjetsr_";
    }
  }

  // dist
  ss << pset(P::dist) << ".root";

  std::cout << "INFO::InputsHandlerRun2::forgeFileName:" << std::endl;
  std::cout << "filename = " << ss.str() << std::endl;

  return ss.str().c_str();
}

TH1* InputsHandlerRun2::getHist(const Sample& sample, const TString& systname)
{

  TH1* res = nullptr;
  TString Syst;
  if (Configuration::analysisType() == AnalysisType::VHqqRun2) Syst = systname;
  else Syst = "Systematics";
  if( !sample.hasSubsamples() )
    res = getHistByName(sample.name(), systname, Syst);
  else {
    for( const auto& subs : sample.subsamples() ) {
      TH1* tmp = getHistByName(subs, systname, Syst);
      if( res == nullptr ) {   // case of first subsample
        if( tmp != nullptr ) { // but ensure that the first subsample actually exists
          res = tmp;
          res->SetName(sample.name());
        }
      } else
        res->Add(tmp); // TODO add check for compatibility of binnings
    }
  }

  if( res == nullptr ) {
    std::cout << "WARNING::InputsHandlerRun2::getHist:" << std::endl
              << "Histo for sample " << sample.name() << " in systematic " << systname << std::endl
              << "does not exist in file " << m_file->GetName() << std::endl;
  }

  return res;
}
