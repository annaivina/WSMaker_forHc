/*
Author: Philipp Windischhofer, August 2019
Email: philipp.windischhofer@cern.ch

Some code to probe the landscape of a profiled negative log-Likelihood (PNLL).

Description: Given a RooFit workspace, this code evaluates the PNLL as a function of the
POIs set in the RooStats::ModelConfig. The region in parameter space over which the scan
should be performed is specified in an XML configuration file, the path to which is passed
as an argument.

The output is stored as a ROOT tree with name "NLLscan" in the specified location.

If requested, also the best-fit point (and corresponding Minos uncertainties) is determined
and saved as a tree ("bsetFit") in the same file.

Note: if you want to use this code, it may be worth having a look at
scripts/runLikelihoodLandscape.py, which is a Python wrapper around this code. Depending
on your requirements, it may be more convenient to use.

- - - - - - - - - - - - - - - - - - - - - - - -
 The XML configuration file must obey the
 following structure:

 <root>
    <start_vertex op_1="-2.0" op_2="-2.0" ... op_n="-2.0" />
    <end_vertex op_1="2.0" op_2="2.0" ... op_n="2.0" />
    <opts density="10"/>
 <root>

 The volume which is to be scanned is a (hyper)rectangle, which is
 specified by giving two vertices along one of its space diagonals,
 encoded in the <start_vertex> and <end_vertex> nodes.
 Every coordinate of <start_vertex> is expected to be less than the
 corresponding coordinate in <end_vertex>.

 The <opts> section allows to pass some more parameters to the scanning
 algorithm. "Density" allows to specify the density of the points (per
 unit hypervolume) at which the PNLL is evaluated.
- - - - - - - - - - - - - - - - - - - - - - - -
*/

#include <iostream>
#include <limits>
#include <map>
#include <math.h>
#include <string>

#include <tuple>

// Root
#include "TError.h"
#include "TFile.h"
#include "TString.h"
#include "TTree.h"
#include "TXMLEngine.h"

// RooFit
#include "RooAbsData.h"
#include "RooAbsPdf.h"
#include "RooAbsReal.h"
#include "RooArgSet.h"
#include "RooGlobalFunc.h"
#include "RooMinimizer.h"
#include "RooWorkspace.h"

// RooStats
#include "RooStats/AsymptoticCalculator.h" // for MakeAsimovData
#include "RooStats/ModelConfig.h"
#include "RooStats/RooStatsUtils.h" // for RemoveConstantParameters

// WSMaker macros
#include "macros/makeAsimovData.C"

namespace LikelihoodLandscapeUtils {

  // some aliases to make their content clear ...
  using StartVertex = std::map<TString, double>;
  using EndVertex   = std::map<TString, double>;
  using ScanConfig  = std::map<TString, double>;

  using Table = std::map<TString, std::vector<double>>;

  void Table2Tree(Table& indata, const TString& outfile_path, const TString& tree_name = "NLLscan",
                  const TString& access_mode = "UPDATE")
  {
    TFile* outfile = TFile::Open(outfile_path, access_mode);
    TTree* outtree = new TTree(tree_name, tree_name);

    std::vector<TString> columns;
    int                  min_length = std::numeric_limits<int>::max();
    int                  max_length = std::numeric_limits<int>::min();

    std::vector<Double_t*> branch_buffer;

    for( const auto& column : indata ) {
      auto cur_column = column.first;
      columns.push_back(cur_column);

      Double_t* cur_branch = new Double_t();
      outtree->Branch(cur_column, cur_branch);
      branch_buffer.push_back(cur_branch);

      int cur_length = column.second.size();
      if( cur_length > max_length )
        max_length = cur_length;
      if( cur_length < min_length )
        min_length = cur_length;
    }

    if( max_length != min_length ) {
      std::cout << "ERROR: passed data does not define a flat table. No output will be written!" << std::endl;
      return;
    }

    std::cout << "now filling tree" << std::endl;

    for( int cur_row = 0; cur_row < max_length; cur_row++ ) {
      for( unsigned int cur_column = 0; cur_column < columns.size(); cur_column++ ) {
        if( branch_buffer[cur_column] ) {
          std::cout << branch_buffer[cur_column] << std::endl;
          *branch_buffer[cur_column] = indata[columns[cur_column]][cur_row];
        } else {
          std::cout << "Internal Error. This should not happen." << std::endl;
        }
      }
      outtree->Fill();
    }

    outtree->Write();
    outfile->Close();

    std::cout << "done with writing" << std::endl;
    delete outfile;
  }

  std::map<TString, double> UnpackAttributes(TXMLEngine& xml, XMLNodePointer_t node)
  {
    std::map<TString, double> retval;

    XMLAttrPointer_t attr = xml.GetFirstAttr(node);
    do {
      retval.insert(std::make_pair(xml.GetAttrName(attr), std::stod(xml.GetAttrValue(attr))));
    } while( (attr = xml.GetNextAttr(attr)) );

    return retval;
  }

  XMLNodePointer_t GetNodeByName(TXMLEngine& xml, XMLNodePointer_t parent_node, const TString& requested_name)
  {
    // iterate over all child nodes connected to here, then return the first one whose name matches
    XMLNodePointer_t child = xml.GetChild(parent_node);
    while( child != 0 ) {
      if( strcmp(xml.GetNodeName(child), requested_name.Data()) == 0 ) {
        break;
      }

      child = xml.GetNext(child);
    }
    return child;
  }

  std::tuple<StartVertex, EndVertex, ScanConfig> LoadConfig(const std::string& config_path)
  {
    StartVertex sv;
    EndVertex   ev;
    ScanConfig  conf;

    TXMLEngine      xml;
    XMLDocPointer_t xmldoc = xml.ParseFile(config_path.c_str());
    if( !xmldoc ) {
      std::cout << "ERROR: parsing of XML input failed." << std::endl;
      return std::make_tuple(sv, ev, conf);
    }
    XMLNodePointer_t mainnode = xml.DocGetRootElement(xmldoc);

    // TODO: see if can use the equivalent function from XMLUtils
    // extract the start vertex ...
    XMLNodePointer_t start_node = GetNodeByName(xml, mainnode, "start_vertex");
    sv                          = UnpackAttributes(xml, start_node);

    // ... and the end vertex
    XMLNodePointer_t end_node = GetNodeByName(xml, mainnode, "end_vertex");
    ev                        = UnpackAttributes(xml, end_node);

    // also read the remaining options / settings
    XMLNodePointer_t opts_node = GetNodeByName(xml, mainnode, "opts");
    conf                       = UnpackAttributes(xml, opts_node);

    return std::make_tuple(sv, ev, conf);
  }

  std::tuple<RooWorkspace*, RooStats::ModelConfig*, RooAbsData*> LoadWorkspace(TFile*             infile,
                                                                               const std::string& WorkspaceName,
                                                                               const std::string& ModelConfigName,
                                                                               const std::string& ObsDataName)
  {
    // load workspace, the model configuration and the data
    RooWorkspace* w = (RooWorkspace*)(infile->Get(WorkspaceName.c_str()));
    if( !w ) {
      std::cerr << "ERROR: Workspace '" << WorkspaceName << "' could not be loaded!";
      throw;
    }
    RooStats::ModelConfig* mc = (RooStats::ModelConfig*)(w->obj(ModelConfigName.c_str()));
    if( !mc ) {
      std::cerr << "ERROR: ModelConfig '" << ModelConfigName << "' could not be loaded!";
      throw;
    }
    RooAbsData* data = w->data(ObsDataName.c_str());
    if( !data ) {
      std::cerr << "ERROR: Dataset '" << ObsDataName << "' could not be loaded!";
      throw;
    }

    std::cout << "Successfully loaded workspace, ModelConfig and data!" << std::endl;

    return std::make_tuple(w, mc, data);
  }

  template <class T> std::vector<std::vector<T>> CartesianProduct(const std::vector<std::vector<T>>& factors)
  {
    std::vector<std::vector<T>> prod = {{}};

    for( const auto& cur_factor : factors ) {
      std::vector<std::vector<T>> updated_prod;

      // go through the partial products that have already been built ...
      for( const auto& cur_comb : prod ) {

        // and add all possible values for the current factor
        for( const auto& new_factor : cur_factor ) {
          updated_prod.push_back(cur_comb);
          updated_prod.back().push_back(new_factor);
        }
      }

      prod = move(updated_prod);
    }

    return prod;
  }

  std::vector<double> linspace(double start, double end, int numberPoints)
  {
    std::vector<double> retval;
    double              increment = (end - start) / numberPoints;

    for( auto cur = start; cur < end; cur += increment ) {
      retval.push_back(cur);
    }

    return retval;
  }

  RooAbsData* CreateAsimovDataset(RooStats::ModelConfig* mc, RooArgSet* params)
  {
    RooArgSet globObs(
        "AsimovGlobObs"); // will hold the global observables set to values that are compatible with all constraints
    RooStats::RemoveConstantParameters(params); // don't need to keep constants
    RooAbsData* asimovData = RooStats::AsymptoticCalculator::MakeAsimovData(*mc, *params, globObs);

    return asimovData;
  }

  Table BestFit(RooStats::ModelConfig* mc, RooAbsData* scandata)
  {
    Table retval;
    // get the PDF from the ModelConfig
    RooAbsPdf* scanpdf = mc->GetPdf();
    std::cout << "Using the following pdf: " << scanpdf->GetName() << std::endl;

    RooArgSet* constrainedParams = scanpdf->getParameters(*scandata);
    RooStats::RemoveConstantParameters(constrainedParams);
    RooFit::Constrain(*constrainedParams);
    const RooArgSet* glbObs = mc->GetGlobalObservables();

    // get the POIs that should be scanned
    const RooArgSet* POIs       = mc->GetParametersOfInterest();
    double           numberPOIs = POIs->getSize();

    // generate the (profiled) likelihood
    RooAbsReal* nll =
        scanpdf->createNLL(*scandata, RooFit::Constrain(*constrainedParams), RooFit::GlobalObservables(*glbObs),
                           RooFit::Offset(1), RooFit::NumCPU(1, 3), RooFit::Optimize(2));

    // perform the actual fit
    RooMinimizer minim(*nll);
    int          fit_status = minim.minimize(ROOT::Math::MinimizerOptions::DefaultMinimizerAlgo().c_str());

    // get some nice uncertainties for the POIs
    minim.minos(*POIs);

    // read out the best-fit point
    std::cout << "found the following best-fit point" << std::endl;
    POIs->Print("v");

    auto        it = POIs->createIterator();
    RooRealVar* cur_POI;
    while( (cur_POI = (RooRealVar*)(it->Next())) ) {
      TString cur_POI_name     = cur_POI->GetName();
      double  cur_POI_value    = cur_POI->getValV();
      double  cur_POI_unc_up   = cur_POI->getAsymErrorHi();
      double  cur_POI_unc_down = cur_POI->getAsymErrorLo();

      retval.insert(std::make_pair(cur_POI_name, std::vector<double>({cur_POI_value})));
      retval.insert(std::make_pair(cur_POI_name + "_unc_up", std::vector<double>({cur_POI_unc_up})));
      retval.insert(std::make_pair(cur_POI_name + "_unc_down", std::vector<double>({cur_POI_unc_down})));
    }

    return retval;
  }

  Table Scan(RooStats::ModelConfig* mc, RooAbsData* scandata, const StartVertex& sv, const EndVertex& ev,
             const ScanConfig& conf)
  {
    // get the PDF from the ModelConfig
    RooAbsPdf* scanpdf = mc->GetPdf();
    std::cout << "Using the following pdf: " << scanpdf->GetName() << std::endl;

    RooArgSet* constrainedParams = scanpdf->getParameters(*scandata);
    RooStats::RemoveConstantParameters(constrainedParams);
    RooFit::Constrain(*constrainedParams);
    const RooArgSet* glbObs = mc->GetGlobalObservables();

    // get the POIs that should be scanned
    const RooArgSet* POIs       = mc->GetParametersOfInterest();
    double           numberPOIs = POIs->getSize();

    // scanning over the following POIs:
    std::cout << "=================================" << std::endl;
    std::cout << "will scan over the following " << numberPOIs << " POIs" << std::endl;
    std::vector<TString> POI_names;
    for( const auto& cur : sv ) {
      auto cur_name = cur.first;
      POI_names.push_back(cur_name);
      std::cout << cur_name << std::endl;
    }
    std::cout << "=================================" << std::endl;

    // get the density per dimension
    int density_red = int(std::pow(conf.at("density"), 1.0 / numberPOIs));
    std::cout << "using as density / dim = " << density_red << std::endl;

    // for each POI (for each dimension), get the evaluation points
    std::cout << "building grid...";
    std::vector<std::vector<double>> factors;
    for( const auto& cur_POI : POI_names ) {
      auto cur_linspace = linspace(sv.at(cur_POI), ev.at(cur_POI), density_red);
      factors.push_back(cur_linspace);
    }
    std::vector<std::vector<double>> grid = CartesianProduct(factors);
    std::cout << " done!" << std::endl;

    // prepare the data structure holding the return values
    Table retval;
    for( const auto& cur_POI_name : POI_names ) {
      retval.insert(std::make_pair(cur_POI_name, std::vector<double>()));
    }
    retval.insert(std::make_pair("NLL", std::vector<double>()));

    std::cout << "=================================" << std::endl;
    std::cout << "starting scan" << std::endl;
    std::cout << "=================================" << std::endl;

    // generate the likelihood and find its minimum
    RooAbsReal* nll =
        scanpdf->createNLL(*scandata, RooFit::Constrain(*constrainedParams), RooFit::GlobalObservables(*glbObs),
                           RooFit::Offset(1), RooFit::NumCPU(1, RooFit::Hybrid), RooFit::Optimize(2));
    nll->setEvalErrorLoggingMode(RooAbsReal::ErrorLoggingMode::CountErrors);
    std::cout << "Created NLL!" << std::endl;

    //ROOT::Math::MinimizerOptions::SetDefaultStrategy(0);
    RooMinimizer minim_nll(*nll);
    minim_nll.setPrintEvalErrors(-1);
    minim_nll.setVerbose(false);
    minim_nll.setStrategy(ROOT::Math::MinimizerOptions::DefaultStrategy());
    minim_nll.setEps(0.01);
    TString minimizer = "Minuit2";
    TString algorithm = ROOT::Math::MinimizerOptions::DefaultMinimizerAlgo();

    int    fit_status            = minim_nll.minimize(minimizer, algorithm);
    double nll_min_unconstrained = nll->getVal();
    std::cout << "unconstrained fit status = " << fit_status << std::endl;
    std::cout << "unconstrained min(NLL) = " << nll_min_unconstrained << std::endl;

    if( fit_status != 0 ) {
      std::cout << "ERROR: unable to perform the unconditional fit correctly, can't continue!" << std::endl;
      throw;
    } else {
      std::cout << "unconditional fit finished" << std::endl;
    }

    minim_nll.setPrintLevel(0);

    for( const auto& cur_point : grid ) {
      for( unsigned int cur_POI = 0; cur_POI < POI_names.size(); cur_POI++ ) {
        double  cur_value = cur_point[cur_POI];
        TString cur_name  = POI_names[cur_POI];
        ((RooRealVar*)(POIs->find(cur_name)))->setVal(cur_value);
        ((RooRealVar*)(POIs->find(cur_name)))->setConstant(1);
      }
      int    fit_status    = minim_nll.minimize(minimizer, algorithm);
      double nll_min       = nll->getVal();
      double cur_delta_nll = nll_min - nll_min_unconstrained;

      if( fit_status == 0 ) {
        for( unsigned int cur_POI = 0; cur_POI < POI_names.size(); cur_POI++ ) {
          double  cur_value = cur_point[cur_POI];
          TString cur_name  = POI_names[cur_POI];
          retval[cur_name].push_back(cur_value);
        }
        retval["NLL"].push_back(cur_delta_nll);

        std::cout << "- - - - - - - - - - - - - - - - -" << std::endl;
        POIs->Print("v");
        std::cout << "NLL = " << cur_delta_nll << std::endl;
        std::cout << "- - - - - - - - - - - - - - - - -" << std::endl;
      } else {
        std::cout << "WARNING: unable to perform the NLL calculation correctly!" << std::endl;
      }
    }

    return retval;
  }

  void Finalize() { std::cout << "Done with everything!" << std::endl; }
} // namespace LikelihoodLandscapeUtils

void LikelihoodLandscape(
    const char* infile_path,                  // path to the input workspace file
    const char* outfile_path,                 // path to the ROOT file that holds the results
    const char* config_path,                  // path to the XML configuration file that determines the scanned volume
    const char* WorkspaceName   = "combined", // name of the RooFit workspace contained in 'infile_path'
    const char* ModelConfigName = "ModelConfig", // name of the RooStats::ModelConfig contained in 'infile_path'
    const char* ObsDataName     = "obsData",     // name of the dataset embedded in the workspace
    bool        doAsimov        = false,         // select whether to compute the PNLL based on Asimov- or observed data
    bool        doPostFit       = false,         // select whether Asimov should be built with central values of NPs or with best-fit values
    float       poiValue        = 1.0,           // select which poi values to be used if conditionnal fits are run
    bool        doBestFit       = false)         // select whether or not to also find (and store) the best-fit value
{

  gErrorIgnoreLevel = 1001;

  std::cout << "=========================================" << std::endl;
  std::cout << " This is LikelihoodLandscape.C " << std::endl;
  std::cout << "-----------------------------------------" << std::endl;
  std::cout << " reading workspace from " << infile_path << std::endl;
  std::cout << "=========================================" << std::endl;

  TFile* infile = TFile::Open(infile_path, "READ");
  if( !infile ) {
    std::cout << "ERROR: file " << infile_path << " could not be opened." << std::endl;
    return;
  }

  // load the workspace, Modelconfig and the embedded data
  RooWorkspace*          w;
  RooStats::ModelConfig* mc;
  RooAbsData*            data;
  std::tie(w, mc, data) = LikelihoodLandscapeUtils::LoadWorkspace(infile, WorkspaceName, ModelConfigName, ObsDataName);

  // load the XML config file
  LikelihoodLandscapeUtils::ScanConfig  conf;
  LikelihoodLandscapeUtils::StartVertex sv;
  LikelihoodLandscapeUtils::EndVertex   ev;
  std::tie(sv, ev, conf) = LikelihoodLandscapeUtils::LoadConfig(config_path);
  
  ROOT::Math::MinimizerOptions::SetDefaultMinimizer("Minuit2", "Migrad");
  ROOT::Math::MinimizerOptions::SetDefaultStrategy(2);

  std::cout << "got the following start vertex:" << std::endl;
  for( const auto& cur : sv ) {
    std::cout << cur.first << ": " << cur.second << std::endl;
  }

  std::cout << "got the following end vertex:" << std::endl;
  for( const auto& cur : ev ) {
    std::cout << cur.first << ": " << cur.second << std::endl;
  }

  std::cout << "got the following additional options:" << std::endl;
  for( const auto& cur : conf ) {
    std::cout << cur.first << ": " << cur.second << std::endl;
  }

  // if requested, create the Asimov dataset (following the configuration in the ModelConfig)
  if( doAsimov ) {
    std::cout << "creating Asimov dataset" << std::endl;

    if(!doPostFit){
      std::cout << "--> doing pre-fit Asimov" << std::endl;
      // pre-fit Asimov
      // create Asimov dataset, using the current (= nominal) values of the nuisance parameters
      TIterator*  it = mc->GetParametersOfInterest()->createIterator();
      RooRealVar* n  = (RooRealVar*)it->Next();
      while( n ) {
	n->setVal(poiValue);
	n = (RooRealVar*)it->Next();
      }
      data = LikelihoodLandscapeUtils::CreateAsimovDataset(mc, mc->GetPdf()->getParameters(*data));
    }else{
      // post-fit Asimov
      std::cout << "--> doing (conditional) post-fit Asimov" << std::endl;
      std::cout << "--> with poi set to " << poiValue << std::endl;
      RooAbsData* obs_data = data;
      bool doConditional = true;
      data = makeAsimovData(mc, doConditional, w, mc->GetPdf(), (RooDataSet*) obs_data, poiValue);

      stringstream muStr; muStr << "_" << poiValue;
      w -> loadSnapshot(("conditionalGlobs" + muStr.str()).c_str());
    }
  }

  // get the best-fit point if requested
  if( doBestFit ) {
    LikelihoodLandscapeUtils::Table best_fit = LikelihoodLandscapeUtils::BestFit(mc, data);
    LikelihoodLandscapeUtils::Table2Tree(best_fit, outfile_path, "bestFit", "RECREATE");
  }

  // perform the NLL scan, following the settings set forth in the ModelConfig
  LikelihoodLandscapeUtils::Table scandata = LikelihoodLandscapeUtils::Scan(mc, data, sv, ev, conf);

  // store the data into a TTree
  LikelihoodLandscapeUtils::Table2Tree(scandata, outfile_path, "NLLscan", "UPDATE");

  LikelihoodLandscapeUtils::Finalize();

  infile->Close();
}
