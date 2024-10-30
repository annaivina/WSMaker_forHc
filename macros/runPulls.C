// Author      : Stefan Gadatsch
// Email       : gadatsch@nikhef.nl
// Date        : 2013-04-24
// Description : Compute pulls and impact on the POI

#include <string>
#include <vector>

#include "RooArgSet.h"
#include "RooConstVar.h"
#include "RooDataSet.h"
#include "RooFitResult.h"
#include "RooGaussian.h"
#include "RooNLLVar.h"
#include "RooPoisson.h"
#include "RooRealVar.h"
#include "RooWorkspace.h"
#include "TFile.h"
#include "TH1D.h"
#include "TObjArray.h"
#include "TObjString.h"
#include "TPRegexp.h"
#include "TStopwatch.h"
#include "TString.h"
#include "findSigma.C"
#include "log.C"
#include "minimize.C"
#include "parseString.C"

#include "Math/MinimizerOptions.h"
#include "RooStats/ModelConfig.h"

using namespace std;
using namespace RooFit;
using namespace RooStats;

enum NPType { GammaPoisson, GammaGaussian, GammaProtection, Others, Unknown };
NPType                    getNPType(const RooWorkspace* ws, const RooRealVar* par);
std::pair<double, double> getPrefitErrorForGamma(const RooWorkspace* ws, const RooRealVar* par, NPType type);
// ____________________________________________________________________________|__________
// void runPulls() {
//    // for compiling only
//}

// ____________________________________________________________________________|__________
// compute pulls of the nuisance parameters and store them in text files. norm and syst parameters will be split among
// different files
void runPulls(const char* inFileName = "data_newbug.root", const char* wsName = "workspace",
              const char* modelConfigName = "modelSB", const char* dataName = "data",
              const char* folder = "data_newbug", unsigned int num_total_slices = 1, unsigned int num_slice = 1,
              const char* variable = NULL, double precision = 0.005, bool useMinos = 1, string loglevel = "DEBUG")
{
  cout << "start doing " << endl;
  TStopwatch* timer = new TStopwatch();
  timer->Start();

  cout << "Running job " << num_slice << " of " << num_total_slices << endl;

  // TStopwatch timer_pulls;
  // timer_pulls.Start();

  // DEBUG OUTPUT
  // - ERROR
  // - WARNING
  // - INFO
  // - DEBUG

  LOG::FromString(loglevel);

  cout << "start doing 1" << endl;

  // LOG::ReportingLevel() = LOG::FromString(loglevel);

  cout << "start doing 2" << endl;

  // some settings
  ROOT::Math::MinimizerOptions::SetDefaultMinimizer("Minuit2");
  ROOT::Math::MinimizerOptions::SetDefaultStrategy(2);
  if( loglevel == "DEBUG" ) {
    ROOT::Math::MinimizerOptions::SetDefaultPrintLevel(1);
  } else {
    ROOT::Math::MinimizerOptions::SetDefaultPrintLevel(-1);
    RooMsgService::instance().setGlobalKillBelow(RooFit::FATAL);
  }

  cout << "start doing 3" << endl;

  // loading the workspace etc.
  LOG(logINFO) << "Running over workspace: " << inFileName;
  cout << "start doing 3.1" << endl;
  system(("mkdir -vp output/" + string(folder) + "/root-files/pulls").c_str());

  TFile* file = new TFile(inFileName);

  RooWorkspace* ws = (RooWorkspace*)file->Get(wsName);
  if( !ws ) {
    LOG(logERROR) << "Workspace: " << wsName << " doesn't exist!";
    exit(1);
  }

  ModelConfig* mc = (ModelConfig*)ws->obj(modelConfigName);
  if( !mc ) {
    LOG(logERROR) << "ModelConfig: " << modelConfigName << " doesn't exist!";
    exit(1);
  }

  TString datastring(dataName);
  int     commaPos = datastring.Index(",");
  if( commaPos != TString::kNPOS ) {
    ws->loadSnapshot(TString(datastring(commaPos + 1, datastring.Length())));
    datastring = datastring(0, commaPos);
  }

  RooDataSet* data = (RooDataSet*)ws->data(datastring);
  if( !data ) {
    LOG(logERROR) << "Dataset: " << dataName << " doesn't exist!";
    exit(1);
  }

  cout << "start doing 4" << endl;

  vector<RooRealVar*> pois;
  /*
  for (unsigned int i = 0; i < parsed.size(); i++) {
      RooRealVar* poi = (RooRealVar*)ws->var(parsed[i].c_str());
      LOG(logINFO) << "Getting POI " << poi->GetName();
      if (!poi) {
          LOG(logERROR) << "POI: " << poi->GetName() << " doesn't exist!";
          exit(1);
      }
      poi->setVal(1);
      poi->setRange(-5.,5.);
      poi->setConstant(0);
      pois.push_back(poi);
  }
  */
  RooArgSet* POIS_detected = (RooArgSet*)mc->GetParametersOfInterest();
  TIterator* POI_itr       = POIS_detected->createIterator();
  TString    anaType       = std::getenv("ANALYSISTYPE");
  while( RooRealVar* poi = (RooRealVar*)POI_itr->Next() ) {
    LOG(logINFO) << "Getting POI " << poi->GetName();
    poi->setVal(1.0);
    if( anaType == "VHccRun2" ) {
      poi->setRange(-30., 30.);
    } else {
      poi->setRange(-10., 10.);
    }
    poi->setConstant(0);
    pois.push_back(poi);
  }
  cout << "start doing 5" << endl;

  RooArgSet* nuis = (RooArgSet*)mc->GetNuisanceParameters();
  if( !nuis ) {
    LOG(logERROR) << "Nuisance parameter set doesn't exist!";
    exit(1);
  }
  TIterator*  itr = nuis->createIterator();
  RooRealVar* var;

  RooArgSet* globs = (RooArgSet*)mc->GetGlobalObservables();
  if( !globs ) {
    LOG(logERROR) << "GetGlobal observables don't exist!";
    exit(1);
  }
  cout << "start doing 6" << endl;

  // collect nuisance parameters
  vector<string> vec_nuis;

  while( (var = (RooRealVar*)itr->Next()) ) {
    string varName(var->GetName());

    // skipping MC stat, lvlv pacman efficiencies
    // if (varName.find("gamma_stat") != string::npos && varName.find("alpha") == string::npos) {
    //     LOG(logDEBUG) << "Skipping " << varName;
    //     continue;
    // }

    if( varName.find("ATLAS_norm_All") != string::npos ) {
      LOG(logDEBUG) << "Skipping " << varName;
      continue;
    }

    // all remaining nuisance parameters
    LOG(logDEBUG) << "pushed back " << varName;
    vec_nuis.push_back(string(var->GetName()));
  }

  itr->Reset();
  unsigned int nrNuis = vec_nuis.size();

  cout << "start doing 7" << endl;

  // create nll and do unconditional fit
  // ws->loadSnapshot("ucmles");
  for( unsigned int i = 0; i < pois.size(); i++ ) {
    pois[i]->setConstant(0);
    if( anaType == "VHccRun2" ) {
      pois[i]->setRange(-30., 30.);
    } else {
      pois[i]->setRange(-10., 10.);
    }
    pois[i]->setVal(1.1); // kick !
  }

  // int numCPU = sysconf( _SC_NPROCESSORS_ONLN );
  int numCPU = 1;
  if( useMinos )
  std::cout<<"USE MINOS"<<std::endl;
    numCPU = 1; // Minos doesn't like our NLL with multiple cores
  RooNLLVar* nll = (RooNLLVar*)mc->GetPdf()->createNLL(*data, Constrain(*nuis), GlobalObservables(*globs), Offset(1),
                                                       NumCPU(numCPU, RooFit::Hybrid), Optimize(2));

  RooFitResult* fitresult = nullptr;
  Fits::minimize(nll);
  // it is good that first fit has decent estimate of the errors, so strategy 1 is good
  // for subsequent fits, we don't care, so go faster
  ROOT::Math::MinimizerOptions::SetDefaultStrategy(0);
  double         nll_hat = nll->getVal();
  vector<double> pois_hat;
  for( unsigned int i = 0; i < pois.size(); i++ ) {
    pois_hat.push_back(pois[i]->getVal());
  }

  // set all nuisance parameters floating and save snapshot
  while( (var = (RooRealVar*)itr->Next()) ) {
    string varName(var->GetName());
    if( varName.find("ATLAS_norm_All") != string::npos ) {
      var->setConstant(1);
    }
    var->setConstant(0);
  }
  itr->Reset();
  for( unsigned int i = 0; i < pois.size(); i++ ) {
    pois[i]->setConstant(0);
  }
  ws->saveSnapshot("tmp_snapshot", *mc->GetPdf()->getParameters(data));

  cout << "start doing 8" << endl;

  LOG(logDEBUG) << "Made unconditional snapshot";

  //---------------------------------------------------------BEGINNING FOR POI
  // RANKING-----------------------------------------------//

  //   ROOT::Math::MinimizerOptions::SetDefaultStrategy(2);
  for( unsigned int in = 0; in < pois.size(); in++ ) {

   // if( in % num_total_slices != num_slice )
   //   continue;

    ws->loadSnapshot("tmp_snapshot");

    double poi_errup;
    double poi_errdown;

    if( useMinos ) {
      Fits::minimize(nll);
      poi_errup   = pois[in]->getErrorHi();
      poi_errdown = pois[in]->getErrorLo();
    } else {
      ws->loadSnapshot("tmp_snapshot");
      poi_errup =
          findSigma(nll, nll_hat, pois[in], pois_hat[in] + fabs(pois[in]->getErrorHi()), pois_hat[in], +1, precision);
      ws->loadSnapshot("tmp_snapshot");
      poi_errdown =
          findSigma(nll, nll_hat, pois[in], pois_hat[in] - fabs(pois[in]->getErrorLo()), pois_hat[in], -1, precision);
    }
    LOG(logINFO) << pois[in]->GetName() << " = " << pois_hat[in] << " +" << fabs(poi_errup) << " /  -"
                 << fabs(poi_errdown);

    // fix theta at the MLE value +/- postfit uncertainty and minimize again to estimate the change in the POI
    ws->loadSnapshot("tmp_snapshot");
    pois[in]->setVal(pois_hat[in] + fabs(poi_errup));
    pois[in]->setConstant(1);
    Fits::minimize(nll);
    vector<double> pois_up;
    for( unsigned int i = 0; i < (pois.size()); i++ ) {
      if( in == i )
        pois_up.push_back(pois_hat[in]);
      else
        pois_up.push_back(pois[i]->getVal());
    }

    ws->loadSnapshot("tmp_snapshot");
    pois[in]->setVal(pois_hat[in] - fabs(poi_errdown));
    pois[in]->setConstant(1);
    Fits::minimize(nll);
    vector<double> pois_down;
    for( unsigned int i = 0; i < pois.size(); i++ ) {
      if( in == i )
        pois_down.push_back(pois_hat[in]);
      else
        pois_down.push_back(pois[i]->getVal());
    }

    // fix theta at the MLE value +/- postfit uncertainty and minimize again to estimate the change in the POI
    ws->loadSnapshot("tmp_snapshot");
    vector<double> pois_nom_up;
    for( unsigned int i = 0; i < pois.size(); i++ ) {
      pois_nom_up.push_back(pois[i]->getVal());
    }

    vector<double> pois_nom_down;
    for( unsigned int i = 0; i < pois.size(); i++ ) {
      pois_nom_down.push_back(pois[i]->getVal());
    }

    for( unsigned int i = 0; i < pois.size(); i++ ) {
      LOG(logINFO) << "Variation of " << pois[i]->GetName() << " = " << pois_up[i] << " (" << pois_nom_up[i] << ") / "
                   << pois_down[i] << " (" << pois_nom_down[i] << ")";
    }

    // store result in root file
    stringstream fileName;
    fileName << "output/" << folder << "/root-files/pulls/" << pois[in]->GetName() << ".root";
    TFile fout(fileName.str().c_str(), "recreate");

    TH1D* h_out = new TH1D((pois[in]->GetName()), (pois[in]->GetName()), 3 + 5 * pois.size(), 0, 3 + 5 * pois.size());

    h_out->SetBinContent(1, pois_hat[in]);
    h_out->SetBinContent(2, fabs(poi_errup));
    h_out->SetBinContent(3, fabs(poi_errdown));

    h_out->GetXaxis()->SetBinLabel(1, "poi_hat");
    h_out->GetXaxis()->SetBinLabel(2, "poi_up");
    h_out->GetXaxis()->SetBinLabel(3, "poi_down");

    int bin = 4;
    for( unsigned int i = 0; i < pois.size(); i++ ) {
      h_out->SetBinContent(bin, pois_hat[i]);
      h_out->SetBinContent(bin + 1, pois_up[i]);
      h_out->SetBinContent(bin + 2, pois_down[i]);
      h_out->SetBinContent(bin + 3, pois_nom_up[i]);
      h_out->SetBinContent(bin + 4, pois_nom_down[i]);

      h_out->GetXaxis()->SetBinLabel(bin, pois[i]->GetName());
      h_out->GetXaxis()->SetBinLabel(bin + 1, "poi_up");
      h_out->GetXaxis()->SetBinLabel(bin + 2, "poi_down");
      h_out->GetXaxis()->SetBinLabel(bin + 3, "poi_nom_up");
      h_out->GetXaxis()->SetBinLabel(bin + 4, "poi_nom_down");

      bin += 5;
    }

    fout.Write();
    fout.Close();
  }
  //---------------------------------------------------------END FOR POI
  // RANKING-----------------------------------------------//

  //    ROOT::Math::MinimizerOptions::SetDefaultStrategy(0);
  for( unsigned int in = 0; in < nrNuis; in++ ) {
    // for (int in = 0; in < 1; in++) {

    //if( in % num_total_slices != num_slice )
    //  continue;

    // only run on NPs contained in the WSName
    /*
    TString NPid = vec_nuis[in].c_str();
    NPid.ReplaceAll("ATLAS_", "");
    NPid.ReplaceAll("norm_", "");
    NPid.ReplaceAll("alpha_", "");
    if (NPid.First('_') > 0)
      NPid = NPid(0, NPid.First('_'));
    cout << "NPid: " << NPid.Data() << endl;
    TString fName = inFileName;
    if (!fName.Contains(NPid)) {
      continue;
    } else {
      cout << "OK: " << vec_nuis[in].c_str() << endl;
    }
    */

    ws->loadSnapshot("tmp_snapshot");

    RooRealVar* nuip = (RooRealVar*)nuis->find(vec_nuis[in].c_str());
    string      nuipName(nuip->GetName());

    cout << " doing nuip name " << nuipName << endl;
    if( variable != NULL && nuipName != string(variable) )
      continue;

    // find all unconstrained NFs etc.
    bool isNorm = 0;
    if( nuipName.find("ATLAS_norm") != string::npos )
      isNorm = 1;
    if( nuipName.find("gamma") != string::npos )
      isNorm = 1;
    // if (nuipName.find("atlas_nbkg_") != string::npos) isNorm = true;
    // if (nuipName.find("slope_") != string::npos) isNorm = true;
    // if (nuipName.find("p0_") != string::npos) isNorm = true;
    // if (nuipName.find("p1_") != string::npos) isNorm = true;
    // if (nuipName.find("p2_") != string::npos) isNorm = true;
    // if (nuipName.find("p3_") != string::npos) isNorm = true;
    // if (nuipName.find("ATLAS_Hbb_norm_") != string::npos) isNorm = true;
    // if (nuipName.find("ATLAS_PM_EFF_") != string::npos) isNorm = true;
    if( nuipName.find("scale_") != string::npos && nuipName.find("QCDscale_") == string::npos )
      isNorm = true;

    /* TODO: ask Stefan abouth this
    // setting all parameters but the one NF to look at constant at the best fit value when computing the error for the
    NF if (isNorm) { LOG(logDEBUG) << nuipName << " is unconstrained."; while ((var = (RooRealVar*)itr->Next())) {
            string varName(var->GetName());
            if (varName.find(nuipName) == string::npos) var->setConstant(1);
            LOG(logDEBUG) << varName << " is constant -> " << var->isConstant();
        }
        itr->Reset();
    }
    */

    double nuip_hat = nuip->getVal();
    nuip->setConstant(0);

    ws->saveSnapshot("tmp_snapshot2", *mc->GetPdf()->getParameters(data));

    LOG(logDEBUG) << "Computing error for var " << nuip->GetName() << " at " << nuip->getVal();

    double nuip_errup;
    double nuip_errdown;

    if( useMinos ) {
      RooArgSet* minosSet = new RooArgSet(*nuip);
      Fits::minimize(nll);
      nuip_errup   = nuip->getErrorHi();
      nuip_errdown = nuip->getErrorLo();
    } else {
      // should be careful for Poisson PDFs that are not defined for negative NP
      double nuip_high = nuip_hat + fabs(nuip->getErrorHi());
      double nuip_low  = nuip_hat - fabs(nuip->getErrorLo());
      NPType np_type   = getNPType(ws, nuip);
      if( np_type == NPType::GammaPoisson && nuip_low <= 0 ) {
        nuip_low = getPrefitErrorForGamma(ws, nuip, np_type).first;
      } else if( np_type == NPType::GammaProtection ) {
        // This is better estimation and faster convergence
        nuip_high = getPrefitErrorForGamma(ws, nuip, np_type).second;
      }

      if( np_type != NPType::GammaProtection ) {
        ws->loadSnapshot("tmp_snapshot2");
        nuip_errup = findSigma(nll, nll_hat, nuip, nuip_high, nuip_hat, +1, precision);
        ws->loadSnapshot("tmp_snapshot2");
        nuip_errdown = findSigma(nll, nll_hat, nuip, nuip_low, nuip_hat, -1, precision);
      } else {
        ws->loadSnapshot("tmp_snapshot2");
        nuip_errup = findSigma(nll, nll_hat, nuip, nuip_high, nuip_hat, +1, precision);
        LOG(logINFO) << "This is a gamma parameter for protection. No need to get -1 sigma.";
        nuip_errdown = 0.;
      }
    }

    LOG(logINFO) << nuip->GetName() << " = " << nuip_hat << " +" << fabs(nuip_errup) << " /  -" << fabs(nuip_errdown);

    // fix theta at the MLE value +/- postfit uncertainty and minimize again to estimate the change in the POI
    ws->loadSnapshot("tmp_snapshot2");
    nuip->setVal(nuip_hat + fabs(nuip_errup));
    nuip->setConstant(1);
    Fits::minimize(nll);
    vector<double> pois_up;
    for( unsigned int i = 0; i < pois.size(); i++ ) {
      pois_up.push_back(pois[i]->getVal());
    }

    ws->loadSnapshot("tmp_snapshot2");
    nuip->setVal(nuip_hat - fabs(nuip_errdown));
    nuip->setConstant(1);
    Fits::minimize(nll);
    vector<double> pois_down;
    for( unsigned int i = 0; i < pois.size(); i++ ) {
      pois_down.push_back(pois[i]->getVal());
    }

    // fix theta at the MLE value +/- postfit uncertainty and minimize again to estimate the change in the POI
    ws->loadSnapshot("tmp_snapshot2");
    vector<double> pois_nom_up;
    if( !isNorm ) {
      nuip->setVal(nuip_hat + 1.0);
      nuip->setConstant(1);
      Fits::minimize(nll);
    }
    for( unsigned int i = 0; i < pois.size(); i++ ) {
      pois_nom_up.push_back(pois[i]->getVal());
    }

    ws->loadSnapshot("tmp_snapshot2");
    if( !isNorm ) {
      nuip->setVal(nuip_hat - 1.0);
      nuip->setConstant(1);
      Fits::minimize(nll);
    }
    vector<double> pois_nom_down;
    for( unsigned int i = 0; i < pois.size(); i++ ) {
      pois_nom_down.push_back(pois[i]->getVal());
    }

    for( unsigned int i = 0; i < pois.size(); i++ ) {
      LOG(logINFO) << "Variation of " << pois[i]->GetName() << " = " << pois_up[i] << " (" << pois_nom_up[i] << ") / "
                   << pois_down[i] << " (" << pois_nom_down[i] << ")";
    }

    // store result in root file
    stringstream fileName;
    fileName << "output/" << folder << "/root-files/pulls/" << nuipName << ".root";
    TFile fout(fileName.str().c_str(), "recreate");

    TH1D* h_out = new TH1D(nuipName.c_str(), nuipName.c_str(), 3 + 5 * pois.size(), 0, 3 + 5 * pois.size());

    h_out->SetBinContent(1, nuip_hat);
    h_out->SetBinContent(2, fabs(nuip_errup));
    h_out->SetBinContent(3, fabs(nuip_errdown));

    h_out->GetXaxis()->SetBinLabel(1, "nuip_hat");
    h_out->GetXaxis()->SetBinLabel(2, "nuip_up");
    h_out->GetXaxis()->SetBinLabel(3, "nuip_down");

    int bin = 4;
    for( unsigned int i = 0; i < pois.size(); i++ ) {
      h_out->SetBinContent(bin, pois_hat[i]);
      h_out->SetBinContent(bin + 1, pois_up[i]);
      h_out->SetBinContent(bin + 2, pois_down[i]);
      h_out->SetBinContent(bin + 3, pois_nom_up[i]);
      h_out->SetBinContent(bin + 4, pois_nom_down[i]);

      h_out->GetXaxis()->SetBinLabel(bin, pois[i]->GetName());
      h_out->GetXaxis()->SetBinLabel(bin + 1, "poi_up");
      h_out->GetXaxis()->SetBinLabel(bin + 2, "poi_down");
      h_out->GetXaxis()->SetBinLabel(bin + 3, "poi_nom_up");
      h_out->GetXaxis()->SetBinLabel(bin + 4, "poi_nom_down");

      bin += 5;
    }

    fout.Write();
    fout.Close();
  }
  timer->Stop();
  double real_tot = timer->RealTime();
  double cpu_tot  = timer->CpuTime();
  cout << "Total time " << real_tot << " real sec, " << cpu_tot << " CPU sec" << endl;
  // timer_pulls.Stop();
  // timer_pulls.Print();
}

NPType getNPType(const RooWorkspace* ws, const RooRealVar* par)
{
  NPType      type     = NPType::Unknown;
  std::string par_name = par->GetName();
  if( par_name.find("gamma") != std::string::npos ) {
    RooAbsPdf* constraint_term = (RooAbsPdf*)ws->pdf((par_name + "_constraint").c_str());
    if( constraint_term ) {
      if( typeid(*constraint_term) == typeid(RooPoisson) ) {
        RooConstVar* var_tau = (RooConstVar*)ws->obj((par_name + "_tau").c_str());
        double       tau     = var_tau->getVal();
        if( tau > 0.9 ) {
          type = NPType::GammaPoisson;
        } else {
          type = NPType::GammaProtection;
        }
      } else if( typeid(*constraint_term) == typeid(RooGaussian) ) {
        type = NPType::GammaGaussian;
      }
    }
  } else {
    type = NPType::Others;
  }
  return type;
}

std::pair<double, double> getPrefitErrorForGamma(const RooWorkspace* ws, const RooRealVar* par, NPType type)
{

  double      xlo      = -999.;
  double      xhi      = -999.;
  std::string par_name = par->GetName();
  if( par_name.find("gamma") != std::string::npos ) {
    RooAbsPdf* constraint_term = (RooAbsPdf*)ws->pdf((par_name + "_constraint").c_str());
    if( constraint_term ) {
      if( type == NPType::GammaPoisson || type == NPType::GammaProtection ) {
        if( typeid(*constraint_term) == typeid(RooPoisson) ) {
          RooConstVar* var_tau   = (RooConstVar*)ws->obj((par_name + "_tau").c_str());
          double       ylim      = 0.5;
          double       tau       = var_tau->getVal();
          double       xlim_pois = TMath::Exp(-1 - ylim / tau); // <= -ln{(gamma*tau)^tau*exp(-tau)} = -ln{tau^tau}*ylim
          double       xlim_gaus = 1 - sqrt(2 * ylim / tau);    // <= -ln{exp(-(tau/2)*(gamma-1)^2)} = ylim
          if( type == NPType::GammaPoisson ) {
            if( xlim_gaus > 0. ) {
              xlo = xlim_gaus;
            } else {
              xlo = xlim_pois;
            }
            xhi = 2 - xlim_gaus; //=1+(1-xlim_gaus)
            std::cout << "getPrefitErrorForGamma    parameter:" << par_name << ". This is RooPoisson with tau:" << tau
                      << " xlim_pois:" << xlim_pois << " xlim_gaus:" << xlim_gaus << ".";
          } else {
            xlo = xlim_pois;
            // xhi = -(1./tau)*TMath::Log(1-0.6827); // 68.27% qunatile for exp(-tau*gamma)
            xhi = 1. / 2. / tau; // <= -ln(exp(-tau*gamma)) = 0.5
            std::cout << "getPrefitErrorForGamma    parameter:" << par_name
                      << ". This is RooPoisson for protecion with tau:" << tau << ".";
          }
        }
      } else if( type == NPType::GammaGaussian ) {
        if( typeid(*constraint_term) == typeid(RooGaussian) ) {
          type                   = NPType::GammaGaussian;
          RooConstVar* var_sigma = (RooConstVar*)ws->obj((par_name + "_sigma").c_str());
          double       sigma     = var_sigma->getVal();
          xlo                    = 1. - sigma;
          xhi                    = 1. + sigma;
          std::cout << "getPrefitErrorForGamma    parameter:" << par_name
                    << ". This is RooGaussian with sigma:" << sigma << ".";
        }
      }
      std::cout << " xlo:" << xlo << " xhi:" << xhi << std::endl;
    }
  }
  return std::make_pair(xlo, xhi);
}
