/*
Author: Aaron Armbruster
Date:   2012-05-30
Email:  armbrusa@umich.edu
Description: minimize a function andwith a smart retry strategy


*/

#ifndef MINIMIZE
#define MINIMIZE

#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

#include "RooDataSet.h"
#include "RooFitResult.h"
#include "RooMinimizer.h"
#include "RooNLLVar.h"
#include "RooRealVar.h"
#include "RooWorkspace.h"
#include "TFile.h"

#include "RooStats/ModelConfig.h"

using namespace std;
using namespace RooFit;
using namespace RooStats;

namespace Fits {

  int minimize(RooAbsReal* fcn, bool callHesse = false, TFile* f = nullptr, const TString& save_name = "")
  {

    //   cout << "Starting minimization. Using these global observables" << endl;
    //   mc->GetGlobalObservables()->Print("v");

    // nrMinimize++;

    bool             save_file  = f != nullptr && save_name != "";
    int              printLevel = ROOT::Math::MinimizerOptions::DefaultPrintLevel();
    RooFit::MsgLevel msglevel   = RooMsgService::instance().globalKillBelow();
    if( printLevel < 0 )
      RooMsgService::instance().setGlobalKillBelow(RooFit::FATAL);

    TString      anaType    = std::getenv("ANALYSISTYPE");
    int          strat      = ROOT::Math::MinimizerOptions::DefaultStrategy();
    int          save_strat = strat;
     RooMinimizer minim(*fcn);
     
     
    if( anaType == "VHccRun2" ) {
      minim.setEps(0.01);
    } else {
      minim.setEps(0.1);
    }
   //  if( anaType == "VHccRun2" || anaType == "VHqqRun2") {
//       minim.setMaxFunctionCalls(100000000);
//       minim.setMaxIterations(100000000);
//     }
//     else {
//     minim.setMaxFunctionCalls(100000000);
//     minim.setMaxIterations(100000000);
//     }
      
    minim.setStrategy(strat);
    minim.setPrintLevel(printLevel);
    minim.optimizeConst(2);

    int status = minim.minimize(ROOT::Math::MinimizerOptions::DefaultMinimizerType().c_str(),
                                ROOT::Math::MinimizerOptions::DefaultMinimizerAlgo().c_str());

    // up the strategy
    if( status != 0 && status != 1 && strat < 2 ) {
      strat++;
      cout << "Fit failed with status " << status << ". Retrying with strategy " << strat << endl;
      minim.setStrategy(strat);
      status = minim.minimize(ROOT::Math::MinimizerOptions::DefaultMinimizerType().c_str(),
                              ROOT::Math::MinimizerOptions::DefaultMinimizerAlgo().c_str());
    }

    if( status != 0 && status != 1 && strat < 2 ) {
      strat++;
      cout << "Fit failed with status " << status << ". Retrying with strategy " << strat << endl;
      minim.setStrategy(strat);
      status = minim.minimize(ROOT::Math::MinimizerOptions::DefaultMinimizerType().c_str(),
                              ROOT::Math::MinimizerOptions::DefaultMinimizerAlgo().c_str());
    }

    // //switch minuit version and try again
    //   if (status != 0 && status != 1)
    //   {

    //     string minType = ROOT::Math::MinimizerOptions::DefaultMinimizerType();
    //     string newMinType;
    //     if (minType == "Minuit2") newMinType = "Minuit";
    //     else newMinType = "Minuit2";

    //     cout << "Switching minuit type from " << minType << " to " << newMinType << endl;

    //     ROOT::Math::MinimizerOptions::SetDefaultMinimizer(newMinType.c_str());
    //     strat = ROOT::Math::MinimizerOptions::DefaultStrategy();
    //     minim.setStrategy(strat);

    //     status = minim.minimize(ROOT::Math::MinimizerOptions::DefaultMinimizerType().c_str(),
    //     ROOT::Math::MinimizerOptions::DefaultMinimizerAlgo().c_str());

    //     if (status != 0 && status != 1 && strat < 2)
    //     {
    //       strat++;
    //       cout << "Fit failed with status " << status << ". Retrying with strategy " << strat << endl;
    //       minim.setStrategy(strat);
    //       status = minim.minimize(ROOT::Math::MinimizerOptions::DefaultMinimizerType().c_str(),
    //       ROOT::Math::MinimizerOptions::DefaultMinimizerAlgo().c_str());
    //     }

    //     if (status != 0 && status != 1 && strat < 2)
    //     {
    //       strat++;
    //       cout << "Fit failed with status " << status << ". Retrying with strategy " << strat << endl;
    //       minim.setStrategy(strat);
    //       status = minim.minimize(ROOT::Math::MinimizerOptions::DefaultMinimizerType().c_str(),
    //       ROOT::Math::MinimizerOptions::DefaultMinimizerAlgo().c_str());
    //     }

    //     ROOT::Math::MinimizerOptions::SetDefaultMinimizer(minType.c_str());

    //   }

    if( status != 0 && status != 1 ) {
      cout << "Fit failed with status " << status << endl;
    }

    //   if (status != 0 && status != 1)
    //   {
    //     cout << "Fit failed for mu = " << mu->getVal() << " with status " << status << ". Retrying with pdf->fitTo()"
    //     << endl; combPdf->fitTo(*combData,Hesse(false),Minos(false),PrintLevel(0),Extended(), Constrain(nuiSet_tmp));
    //   }
    if( printLevel < 0 )
      RooMsgService::instance().setGlobalKillBelow(msglevel);
    ROOT::Math::MinimizerOptions::SetDefaultStrategy(save_strat);

    if( callHesse ) {
      cout << "Calling Hesse ..." << endl;
      int hessStatus = minim.hesse();
      cout << "Hesse Status : " << hessStatus << endl;
    }
    if( save_file ) {
      f->cd();
      RooFitResult* saveme = minim.save();
      saveme->Write(save_name);
    }
    return status;
  }

  /*
  void minimize(RooNLLVar* nll)
  {
    int strat = ROOT::Math::MinimizerOptions::DefaultStrategy();
    RooMinimizer minim(*nll);
    minim.setStrategy(strat);
    minim.setPrintLevel(ROOT::Math::MinimizerOptions::DefaultPrintLevel());

  //   RooFit::MsgLevel msglevel = RooMsgService::instance().globalKillBelow();
  //   RooMsgService::instance().setGlobalKillBelow(RooFit::FATAL);

    int status = minim.minimize(ROOT::Math::MinimizerOptions::DefaultMinimizerType().c_str(),
  ROOT::Math::MinimizerOptions::DefaultMinimizerAlgo().c_str());


    if (status != 0 && status != 1 && strat < 2)
    {
      strat++;
      cout << "Fit failed with status " << status << ". Retrying with strategy " << strat << endl;
      minim.setStrategy(strat);
      status = minim.minimize(ROOT::Math::MinimizerOptions::DefaultMinimizerType().c_str(),
  ROOT::Math::MinimizerOptions::DefaultMinimizerAlgo().c_str());
    }

    if (status != 0 && status != 1 && strat < 2)
    {
      strat++;
      cout << "Fit failed with status " << status << ". Retrying with strategy " << strat << endl;
      minim.setStrategy(strat);
      status = minim.minimize(ROOT::Math::MinimizerOptions::DefaultMinimizerType().c_str(),
  ROOT::Math::MinimizerOptions::DefaultMinimizerAlgo().c_str());
    }

  //   RooMsgService::instance().setGlobalKillBelow(msglevel);
  }
  */

}; // namespace Fits

#endif
