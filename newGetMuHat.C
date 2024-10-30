#include <dirent.h>

#include "RooCategory.h"
#include "RooDataSet.h"
#include "RooNLLVar.h"
#include "RooPlot.h"
#include "RooRealVar.h"
#include "RooSimultaneous.h"
#include "RooWorkspace.h"
#include "TCanvas.h"
#include "TFile.h"
#include "TPRegexp.h"

#include "RooStats/ModelConfig.h"

// C++
#include <algorithm>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <set>
#include <sstream>

#include <time.h>

// Root
#include "TObjString.h"
#include "TROOT.h"
#include "TStopwatch.h"
#include "TSystem.h"
#include "TVectorD.h"

#include "macros/findSigma.C"
#include "macros/makeAsimovData.C"
#include "macros/minimize.C"

#if __has_include("../scripts/muHatModes.C")
// take analysis-specific mode configuration
#include "../scripts/muHatModes.C"
#else
// take central WSMaker core mode configuration
#warning "No analysis specific breakdown modes provided. Using old ones."
#include "muHatModes.C"
#endif

bool blind(false);

double subtractError(double err12, double err1)
{
  double check(err12 * err12 - err1 * err1);
  // if(check < 0) { cout << "NEGATIVE" << endl; }
  return sqrt(fabs(check));
}

double subtractFractionalError(double err12, double err1)
{
  double result = 1 - err1 * err1 / (err12 * err12);
  return result;
}

double fractionalError(double err12, double err1)
{
  double result = err1 * err1 / (err12 * err12);
  return result;
}

void SubtractAndSay(TString say, double err1_hi, double err1_lo, double err12_hi, double err12_lo)
{
  cout << say << " : + " << 1 - err1_hi * err1_hi / (err12_hi * err12_hi) << " /- "
       << 1 - err1_lo * err1_lo / (err12_lo * err12_lo) << endl;
  cout << " \t  : + " << subtractError(err12_hi, err1_hi) << " / - " << subtractError(err12_lo, err1_lo) << endl;
}

void newGetMuHat(const char* workspace, const TArrayI& acat, unsigned int total_jobs, unsigned int i_job,
                 const bool doAsimov = 0,
                 // 0 = do observed error
                 // 1 = do expected mu=1 error
                 const int mode = 1,
                 // 0 = standard
                 // 1 = cb
                 const char* mass = "125", TString poiStr = "SigXsecOverSM", const char* wsName = "combined",
                 const char* modelConfigName = "ModelConfig", const char* dataName = "obsData",
                 const bool doDummy = false,
                 // false = normal running
                 // true =don't call findSigma, run just to get set names
                 const bool doHesse = false, double mu_asimov = 1,
                 // for calling and printing Hesse for each NP set
                 const TString& overhead_path = "")
// storing the total error and snapshots of the overhead for a given workspace; looks like result_prefix+(.root|.txt)
{

  TStopwatch* timer = new TStopwatch();
  timer->Start();
  TString inFileName = "output/";
  inFileName += workspace;
  inFileName += "/workspaces/combined/";
  inFileName += mass;
  inFileName += ".root";
  TFile*        file = new TFile(inFileName.Data());
  RooWorkspace* ws   = (RooWorkspace*)file->Get(wsName);
  if( !ws ) {
    cout << "ERROR::Workspace: " << wsName << " doesn't exist!" << endl;
    return;
  }
  ModelConfig* mc = (ModelConfig*)ws->obj(modelConfigName);
  if( !mc ) {
    cout << "ERROR::ModelConfig: " << modelConfigName << " doesn't exist!" << endl;
    return;
  }

  RooDataSet* data = (RooDataSet*)ws->data(dataName);
  if( !data && doAsimov == 0 ) {
    cout << "ERROR::Dataset: " << dataName << " doesn't exist!" << endl;
    return;
  }

  cout << "Loaded Workspace " << workspace << "  - " << ws->GetName() << " , configuration and dataset." << endl;
  // ws->loadSnapshot("nominalNuis");

  MuHatModes mhm(mode);

  double err_raw_hi[mhm.npsets_max];
  double err_raw_lo[mhm.npsets_max];
  double err_npset_hi[mhm.npsets_max];
  double err_npset_lo[mhm.npsets_max];

  for( int iset = 0; iset < mhm.npsets_max; iset++ ) {
    err_raw_hi[iset]   = 0.0;
    err_raw_lo[iset]   = 0.0;
    err_npset_hi[iset] = 0.0;
    err_npset_lo[iset] = 0.0;
  }

  int setnamemax = 0;

  // which categories to run?
  set<int> run_these = {0};
  bool     only_some = false;
  if( acat[0] != -1 ) {
    only_some = true;

    for( int i = 0; i < acat.GetSize(); i++ ) {
      run_these.insert(acat[i]);
    }
  }

  if( only_some ) {
    for( const auto& i : run_these )
      cout << i << " " << mhm.npsetname[i]->Data() << " ";
    cout << endl;
  } else {
    cout << " (ALL of them for mode " << mode << ")" << endl;
  }

  RooRealVar* poi        = 0;
  RooDataSet* asimovData = 0;
  RooArgSet   globObs;
  RooNLLVar*  nll          = 0;
  double      nll_val_true = 0;
  double      muhat        = 0;
  double      err_guess    = 0;

  // mode -1 means we're doing the parallel overhead calculations, so don't load previous results
  // if we are not loading previous results, we will take this to mean we want to save them
  bool    load_previous_result = (mode != -1 && overhead_path != ""), minimize_anyway = false;
  TString outdir = "output/";
  outdir += workspace;
  outdir += "/bd-results/";
  TString overhead_file_name = (overhead_path == "" ? outdir + "breakdown-fitresults.root" : overhead_path);
  cout << "Breakdown results file name is " << overhead_file_name << endl;
  // TString overhead_file_name=(overhead_path==""?"./bd-results/breakdown-fitresults.root":overhead_path);
  RooFitResult* rfr      = 0;
  TFile*        overhead = 0;
  if( load_previous_result ) {
    string okay = overhead_file_name.Data(), front = okay.substr(0, okay.find_last_of("/")),
           back          = okay.substr(okay.find_last_of("/") + 1);
    DIR*           fdir  = opendir(front.c_str());
    struct dirent* ent   = NULL;
    bool           found = false;
    assert(fdir != NULL);
    while( (ent = readdir(fdir)) ) {
      // cout<<"Look at "<<ent->d_name<<", is it "<<back<<endl;
      if( back.compare(ent->d_name) == 0 ) {
        found = true;
        break;
      }
    }
    if( !found )
      load_previous_result = false;
    else {
      overhead = TFile::Open(overhead_file_name);
      rfr      = (RooFitResult*)overhead->Get("nominalNuis")->Clone();
      if( !rfr ) {
        load_previous_result = false;
        overhead->Close();
      }
    }
  }
  if( !load_previous_result ) {
    // make the directory for storing the initial fit result if it doesn't exist
    string path = "./", name = overhead_file_name.Data();
    if( name.find("/") != string::npos ) {
      path = name.substr(0, name.find_last_of("/") + 1);
    }
    DIR* directory = opendir(path.c_str());
    if( directory == NULL )
      system(("mkdir -p " + path).c_str());
    overhead = TFile::Open(overhead_file_name, "recreate");
  }
  bool multpoi = mc->GetParametersOfInterest()->getSize() > 1;
  if( !doDummy ) {
    ws->loadSnapshot("vars_final");
    // let's make all the POI's floating just in case....
    TIterator*  it = mc->GetParametersOfInterest()->createIterator();
    RooRealVar* n  = (RooRealVar*)it->Next();
    while( n ) {
      n->setConstant(0);
      cout << n->GetName() << " set to constant 0" << endl;
      n = (RooRealVar*)it->Next();
    }
    poi = (RooRealVar*)mc->GetParametersOfInterest()->first();
    mc->GetGlobalObservables()->Print("v");
    globObs = *mc->GetGlobalObservables();
    if( poiStr != "SigXsecOverSM" ) {
      // load_previous_result=false;
      poi->setConstant(0);
      cout << "SWITCHING POI TO " << poiStr << endl;
      poi = ws->var(poiStr.Data());
      if( !poi ) {
        cout << "Cannot find " << poiStr << " in workspace" << endl;
        return;
      }
    }

    // RooDataSet* asimovData = makeAsimovData(mc, 0, ws, mc->GetPdf(), data, 1); // unconditional fit and build asimov
    // with mu=1

    // the doAsimov conditional and the lines making the nll had a !doDummy condition on them...inside a if(!doDummy)
    // condition...
    if( doAsimov ) {
      asimovData = makeAsimovData(mc, 0, ws, mc->GetPdf(), data,
                                  mu_asimov); // unconditional fit and build asimov with mu=mu_asimov
      data       = asimovData;
      cout << "Made Asimov data. with mu = " << mu_asimov << endl;
    }
    RooArgSet nuisAndPOI(*mc->GetNuisanceParameters(), *mc->GetParametersOfInterest());

    if( load_previous_result ) {
      // these load something like a fit result into a RooArgSet (taken from doPlotFromWS to load FCC results)
      RooArgList* fpf = (RooArgList*)rfr->floatParsFinal().Clone();
      fpf->add(rfr->constPars());

      // now add information to relevant RooArgSets
      nuisAndPOI.assignValueOnly(*(RooAbsCollection*)fpf);
      globObs.assignValueOnly(*(RooAbsCollection*)fpf);

      // these only load the central values, so we add the sqrt(POI_variance) from the RFR
      int index_for_poi = fpf->index(poiStr);
      err_guess         = sqrt(rfr->covarianceMatrix()(index_for_poi, index_for_poi));
    }

    nll = (RooNLLVar*)mc->GetPdf()->createNLL(*data, GlobalObservables(globObs), Offset(1),
                                              Optimize(2) /*, NumCPU(nCPU, 3), Constrain(nuis)*/);
    //  nll->enableOffsetting(kTRUE);
    cout << "Created NLL." << endl;
    ROOT::Math::MinimizerOptions::SetDefaultMinimizer("Minuit2");
    ROOT::Math::MinimizerOptions::SetDefaultStrategy(1);
    ROOT::Math::MinimizerOptions::SetDefaultPrintLevel(-1);
    /*
      Strategy 1 is "intermediate" FCN's for Minuit (in between fast (0) and expensive (2))
      Default error level of 0.5 corresponds to +/- 1 sigma
      The standard epsilon value of 1.0 corresponds to some sort of tolerance
     */

    poi->setConstant(0);
    cout << "POI" << endl;
    cout << poi->getMin() << endl;
    cout << poi->getMax() << endl;

    cout << "setting min to -max" << endl;
    poi->setMin(-1 * poi->getMax());

    if( !load_previous_result ) {
      // If there is no fit result loaded, run the nominal fit and save the result
      Fits::minimize(nll, false, overhead, "nominalNuis"); // was just minimize(nll);
      err_guess = poi->getError();
    } /*else{
       Fits::minimize(nll);
       err_guess = poi->getError();
       }*/
    cout << "Minimum2 " << nll->getVal() << endl;
    ws->saveSnapshot("tmp_shot", nuisAndPOI);

    nll_val_true = nll->getVal();
    muhat        = poi->getVal();

    typedef std::numeric_limits<double> dbl;
    cout.precision(dbl::digits10);
    cout << "nll_val_true " << nll_val_true << endl;
    if( !blind ) {
      cout << "muhat " << muhat << endl;
    }
    cout << "err_guess " << err_guess << endl;
  }

  const RooArgSet* nuis = mc->GetNuisanceParameters();
  TIterator*       nitr = nuis->createIterator();
  RooRealVar*      var;

  timer->Stop();
  // read off how long the over head took in real and cpu time
  double real_front = timer->RealTime(), cpu_front = timer->CpuTime();
  // and store those values in the total
  double real_tot = real_front, cpu_tot = cpu_front;
  cout << "The mode-independent overhead took " << real_front << " real sec, " << cpu_front << " CPU sec" << endl;
  timer->Start(kTRUE);

  for( int iset = 0; iset < mhm.npsets; iset++ ) {
    if( only_some && !run_these.count(iset) )
      continue;
    if( iset == 0 && load_previous_result && !multpoi ) { // the error ought to be different for each POI
      TVectorD* numbers = (TVectorD*)overhead->Get("errors");
      if( numbers ) {
        cout << "LOAD values from " << overhead_file_name << " for TOT error +" << numbers->operator[](0) << "/ -"
             << numbers->                                                                   operator[](1) << endl;
        err_npset_hi[0] = numbers->                                                         operator[](0);
        err_npset_lo[0] = numbers->                                                         operator[](1);
        err_raw_hi[0]   = numbers->                                                           operator[](0);
        err_raw_lo[0]   = numbers->                                                           operator[](1);
        overhead->Close();
        continue;
      }
      overhead->Close();
    }
    if( setnamemax < mhm.npsetname[iset]->Length() )
      setnamemax = mhm.npsetname[iset]->Length();
    if( iset == 2 ) { // FullSyst is just Total -Stat (quadratically)
      err_raw_hi[iset]   = subtractError(err_raw_hi[0], err_raw_hi[1]);
      err_raw_lo[iset]   = subtractError(err_raw_lo[0], err_raw_lo[1]);
      err_npset_lo[iset] = err_raw_lo[iset];
      err_npset_hi[iset] = err_raw_hi[iset];
      cout << mhm.npsetname[iset]->Data() << " errors from quadratical subrtraction of Total and Stat." << endl;
      cout << mhm.npsetname[iset]->Data() << " _err_npset_hi same as raw: " << err_npset_hi[iset] << endl;
      cout << mhm.npsetname[iset]->Data() << " _err_npset_lo same as raw:  " << err_npset_lo[iset] << endl;
      continue;
    }

    if( !doDummy )
      ws->loadSnapshot("tmp_shot");
    nitr->Reset();
    cout << endl
         << "Holding constant the " << mhm.npsetname[iset]->Data() << " nuisance parameter set, which is: " << endl;

    while( (var = (RooRealVar*)nitr->Next()) ) {
      if( !TString(var->GetName()).Contains(mhm.npsetands[iset]->Data()) ) {
        // 	  std::cout<<"\t[SKC CHECK Can't find "<<mhm.npsetands[iset]<<" in "<<var->GetName()<<"]";
        continue;
      } else {
        //  Changqiao:
        //  for some cases, we need exclude some NPs because the above is not enough for grouping the NP that we want
        //  Like alpha_SysJET_21NP_JET_Flavor_Composition_ttbar_L2 for Model ttbar
        if( mhm.npsetname[iset]->Contains("Model ttbar") &&
            TString(var->GetName()).Contains("JET_Flavor_Composition_ttbar_L2") ) {
          cout << "  Note: Skip " << var->GetName() << " for " << mhm.npsetname[iset]->Data() << endl;
          continue;
        }
      }
      bool aux_isnp = false;
      for( int istr = 0; istr < mhm.npnstr[iset]; istr++ ) {
        aux_isnp = aux_isnp || (string(var->GetName()).find(mhm.npsetstring[iset][istr]->Data()) !=
                                string::npos); // is this var the iset _th NP?

        bool rev_rule = mhm.npsetstring[iset][istr]->BeginsWith("not@");
        if( rev_rule ) {
          TString keep = mhm.npsetstring[iset][istr]->Data();
          aux_isnp     = aux_isnp || (string(var->GetName()).find(keep.Remove(0, 4)) == string::npos);
        }
      }

      if( mhm.npsetexclude[iset] )
        aux_isnp = !aux_isnp;

      if( aux_isnp )
        var->setConstant(1);
      else {
        continue;
      }
      cout << "\t" << var->GetName() << endl;
    }

    // two poi fit, add the other poi to the floating norms
    TString setName = mhm.npsetname[iset]->Data();
    // if running multi-POI, add the POIs to "float norm" and "data stat only" (apart from the POI for which the
    // breakdown is done)
    if( setName.Contains("Floating normalizations") || setName.Contains("Data stat only") ) {
      TIterator*  it = mc->GetParametersOfInterest()->createIterator();
      RooRealVar* n  = (RooRealVar*)it->Next();
      while( n ) {
        TString varName = n->GetName();
        if( varName != poiStr ) {
          n->setConstant(1);
          cout << "\t" << varName << endl;
        }
        n = (RooRealVar*)it->Next();
      }
    }

    if( !doDummy ) {

      if( doHesse ) {
        Fits::minimize(nll, true);
        if( !blind ) {
          cout << "muhat " << poi->getVal() << endl;
        }
        cout << "err_hesse " << poi->getError() << endl;
      }

      err_raw_hi[iset] = findSigma(nll, nll_val_true, poi, muhat + err_guess, muhat, 1, 0.01);
      err_raw_lo[iset] = findSigma(nll, nll_val_true, poi, muhat - err_guess, muhat, -1, 0.01);
    }

    cout << mhm.npsetname[iset]->Data() << " constant" << endl;
    cout << mhm.npsetname[iset]->Data() << " _err_raw_hi straight from fit: " << err_raw_hi[iset] << endl;
    cout << mhm.npsetname[iset]->Data() << " _err_raw_lo straight from fit: " << err_raw_lo[iset] << endl;

    err_npset_lo[iset] = err_raw_lo[iset];
    err_npset_hi[iset] = err_raw_hi[iset];
    // if (iset != 0 && mhm.npsetexclude[iset] == false) {
    if( mhm.npsetsubtract[iset] ) {
      err_npset_hi[iset] = subtractError(err_raw_hi[0], err_raw_hi[iset]);
      err_npset_lo[iset] = subtractError(err_raw_lo[0], err_raw_lo[iset]);
      cout << mhm.npsetname[iset]->Data() << " _err_npset_hi quadratically subtracted from tot: " << err_npset_hi[iset]
           << endl;
      cout << mhm.npsetname[iset]->Data() << " _err_npset_lo quadratically subtracted from tot:  " << err_npset_lo[iset]
           << endl;
    } else {
      cout << mhm.npsetname[iset]->Data() << " _err_npset_hi same as raw: " << err_npset_hi[iset] << endl;
      cout << mhm.npsetname[iset]->Data() << " _err_npset_lo same as raw:  " << err_npset_lo[iset] << endl;
    }

    // save the total error if applicable
    if( iset == 0 && !load_previous_result && !multpoi ) {
      TVectorD numbers(3);
      numbers[0] = err_npset_hi[0];
      numbers[1] = err_npset_lo[0];
      numbers[2] = err_guess;
      overhead->cd();
      numbers.Write("errors");
      overhead->Close();
    }
    timer->Stop();
    // read off how long this NP set took and add it ot the total
    double real_back = timer->RealTime(), cpu_back = timer->CpuTime();
    real_tot += real_back;
    cpu_tot += cpu_back;
    cout << "NP set " << mhm.npsetname[iset]->Data() << " took " << real_back << " real sec, " << cpu_back << " CPU sec"
         << endl;
    timer->Start(kTRUE);
  }

  // having all errors, now output
  TString dirName = "output/";
  dirName += workspace;
  dirName += "/plots/breakdown";
  system(TString("mkdir -vp " + dirName));

  // if multiple jobs, save in a different directory
  if( acat[0] != -1 ) {
    dirName += "/subjobs";
    system(TString("mkdir -vp " + dirName));
  }

  TString fname = dirName;
  fname += "/muHatTable_mode";
  fname += mode;
  if( doAsimov )
    fname += "_Asimov1";
  else
    fname += "_Asimov0";
  fname += "_";
  fname += poiStr;
  TString fnameTxt = fname;
  TString nps      = "";
  if( acat[0] != -1 ) {
    nps += "_job_";
    nps += std::to_string(i_job + 1);
    nps += "_of_";
    nps += std::to_string(total_jobs);
  }
  fnameTxt += nps;
  fnameTxt += ".txt";
  time_t rawtime;
  time(&rawtime);
  FILE* fmuHatTxt = fopen(fnameTxt.Data(), "w");

  bool print_preamble = true, print_postamble = true;
  if( print_preamble ) {
    fprintf(fmuHatTxt, "\n\tOutput of newGetMuHat ran at: %s\n", ctime(&rawtime));
    fprintf(fmuHatTxt, "----------------------------------------------------------\n\tOptions:\n");
    fprintf(fmuHatTxt, "Workspace: %s\n", workspace);
    if( doAsimov )
      fprintf(fmuHatTxt, "Asimov: 1, ");
    else
      fprintf(fmuHatTxt, "Asimov: 0, ");
    if( doDummy )
      fprintf(fmuHatTxt, "Dummy ,");
    fprintf(fmuHatTxt, "Mode: %d, \n", mode);
    fprintf(fmuHatTxt, "Mass: %s GeV; poi: %s; wsName: %s\n", mass, poiStr.Data(), wsName);
    fprintf(fmuHatTxt, "ModelConfigName: %s ; dataName: %s\n", modelConfigName, dataName);
    fprintf(fmuHatTxt, "----------------------------------------------------------\n\n");

    if( !blind ) {
      fprintf(fmuHatTxt, "muhat: %7.5f\n\n", muhat);
    }
    if( !blind ) {
      cout << "muhat: " << muhat << endl;
    }
    fprintf(fmuHatTxt, "nll_val_true: %f\n\n", nll_val_true);

    fprintf(fmuHatTxt, "  Set of nuisance          Impact on error\n");
    fprintf(fmuHatTxt, "       parameters          \n");
    fprintf(fmuHatTxt, "----------------------------------------------------------\n");
  }
  cout << "Raw impact of nuisance parameter sets, quadratically substracted from total." << endl;

  for( int iset = 0; iset < mhm.npsets; iset++ ) {
    if( !print_preamble && iset == 0 )
      continue; // the total error is part of the preamble
    if( only_some && !run_these.count(iset) )
      continue;

    cout << mhm.npsetname[iset]->Data() << " : + " << err_npset_hi[iset] << " / - " << err_npset_lo[iset]
         << (err_npset_hi[iset] + err_npset_lo[iset]) / 2. << endl;

    fprintf(fmuHatTxt, "%25s  + %6.3f  - %6.3f  +- %6.3f\n", mhm.npsetname[iset]->Data(), err_npset_hi[iset],
            err_npset_lo[iset], (err_npset_hi[iset] + err_npset_lo[iset]) / 2.);
  }

  if( print_postamble ) {
    // breakdown bottom of tables for both txt and tex
    fprintf(fmuHatTxt, "Impact on error quadratically subtracted from total, except for:\n");
    for( int iset = 0; iset < mhm.npsets; iset++ ) {
      if( mhm.npsetexclude[iset] )
        fprintf(fmuHatTxt, "%s ", mhm.npsetname[iset]->Data());
    }
    fprintf(fmuHatTxt, "\n----------------------------------------------------------\n\n");
  }

  // fractional
  if( print_preamble ) {
    fprintf(fmuHatTxt, "  Set of nuisance          Fractional impact on error\n");
    fprintf(fmuHatTxt, "       parameters          (square of fraction of total)\n");
    fprintf(fmuHatTxt, "----------------------------------------------------------\n");
  }

  cout << endl;
  cout << "Fractional impact of nuisance parameter sets, quadratically substracted from total." << endl;

  for( int iset = 1; iset < mhm.npsets; iset++ ) {
    if( only_some && !run_these.count(iset) )
      continue;

    cout << mhm.npsetname[iset]->Data() << " : + " << fractionalError(err_npset_hi[0], err_npset_hi[iset]) << " / - "
         << fractionalError(err_npset_lo[0], err_npset_lo[iset]) << " +- "
         << fractionalError((err_npset_hi[0] + err_npset_lo[0]) / 2., (err_npset_hi[iset] + err_npset_lo[iset]) / 2.)
         << endl;

    fprintf(fmuHatTxt, "%25s  + %5.2f  - %5.2f  +-%5.2f\n", mhm.npsetname[iset]->Data(),
            fractionalError(err_npset_hi[0], err_npset_hi[iset]), fractionalError(err_npset_lo[0], err_npset_lo[iset]),
            fractionalError((err_npset_hi[0] + err_npset_lo[0]) / 2., (err_npset_hi[iset] + err_npset_lo[iset]) / 2.));
  }

  if( print_postamble ) {
    // the very end of the fractional impact tables
    fprintf(fmuHatTxt, "----------------------------------------------------------\n\n");
  }
  // we always need to close the files
  fclose(fmuHatTxt);

  cout << "DataStat - no NPs  : +" << err_npset_hi[1] << " / -" << err_npset_lo[1] << endl;
  cout << "FullSyst = Tot -(quad) Stat  : +" << err_npset_hi[2] << " / -" << err_npset_lo[2] << endl;
  cout << "TOT  : +" << err_npset_hi[0] << " / -" << err_npset_lo[0] << endl;

  // and now read off the final times
  timer->Stop();
  real_tot += timer->RealTime(), cpu_tot += timer->CpuTime();
  cout << "Total time " << real_tot << " real sec, " << cpu_tot << " CPU sec" << endl;
}
