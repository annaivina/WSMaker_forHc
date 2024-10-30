#include "plotting.hpp"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <memory>
#include <set>
#include <sstream>
#include <string>
#include <utility>

#include <TAxis.h>
#include <TCanvas.h>
#include <TFile.h>
#include <TGaxis.h>
#include <TH1.h>
#include <TH2.h>
#include <TLatex.h>
#include <TLegend.h>
#include <TLine.h>
#include <TPie.h>
#include <TString.h>
#include <TStyle.h>

#include "binning.hpp"
#include "category.hpp"
#include "categoryhandler.hpp"
#include "configuration.hpp"
#include "outputhandler.hpp"
#include "plotUtils.hpp"
#include "properties.hpp"
#include "sample.hpp"
#include "sampleincategory.hpp"
#include "systematic.hpp"

TH1* rebinToOriginal(TH1* histo, float* newBin)
{
  TH1F* newHisto = new TH1F((histo->GetName() + std::string("Real")).c_str(),
                            (histo->GetName() + std::string("Real")).c_str(), histo->GetNbinsX(), newBin);
  newHisto->Sumw2();
  for( int i = 1; i <= histo->GetNbinsX(); i++ ) {
    newHisto->SetBinContent(i, histo->GetBinContent(i));
    newHisto->SetBinError(i, histo->GetBinError(i));
  }
  return (TH1*)newHisto;
}

Plotting::Plotting(const Configuration& conf) :
    m_conf(conf),
    m_specialMjjBlinding(false),
    m_createAllRootFiles(m_conf.getValue("CreateROOTfiles", false)),
    m_format(m_conf.getValue("PlotsFormat", "eps")),
    m_evtFile(nullptr),
    m_hData(nullptr),
    m_hDataBlind(nullptr),
    m_hSig(nullptr),
    m_hBkgs(),
    m_hStack(),
    m_hSignals(),
    m_binCount(0)
{
  m_hBkgs.clear();
  m_hStack.clear();
  m_hSignals.clear();
}

Plotting::~Plotting() {}

void Plotting::makeCategoryPlots(Category& c)
{
  // std::cout << "Plotting category: " << c.name() << std::endl;
  readHistosFromCat(c);

  if( m_hSig == nullptr ) {
    std::cout << "WARNING::Plotting::makeCategoryPlots: Signal histogram not found! Skipping plotting for region "
              << c.name() << std::endl;
    return;
  }
  if( m_hData == nullptr ) {
    std::cout << "WARNING::Plotting::makeCategoryPlots: Data histogram not found! Skipping plotting for region "
              << c.name() << std::endl;
    return;
  }
  if( m_hBkgs.size() == 0 ) {
    std::cout << "WARNING::Plotting::makeCategoryPlots: No background histogram found! Skipping plotting for region "
              << c.name() << std::endl;
    return;
  }

  m_binCount += m_hSig->GetNbinsX();

  writeYields(c);
  makeStackPlot(c);
  makePieChartPlot(c);
  makeStatPlot(c);
  makeSoBPlot(c);
  makeMCStatRelErrorPlots(c);
  deleteHistos();
}

void Plotting::prepare()
{
  // in ctor, BinningTool was not initialized yet. Now it is, so we can use it.
  m_specialMjjBlinding = !(BinningTool::getInstance().useMjjVariableRebin());
  // create directories
  std::cout << "INFO::Plotting::Preparing plotting..." << std::endl;
  OutputConfig* outconfig = OutputConfig::getInstance();
  std::system(("mkdir -vp " + outconfig->plotDir + "/mass").Data());
  std::system(("mkdir -vp " + outconfig->plotDir + "/systs").Data());
  std::system(("mkdir -vp " + outconfig->plotDir + "/shapes").Data());
  std::cout << "INFO::Plotting::Plot directory: " << outconfig->plotDir.Data() << std::endl;
  std::cout << "INFO::Plotting::Plots will be saved in : " << m_format << std::endl;
  std::cout << "INFO::Plotting::Plots will" << (m_createAllRootFiles ? "" : " not") << " be saved as ROOT files"
            << std::endl;

  // event file
  m_evtFile = new std::ofstream();
  *m_evtFile << std::fixed;
  m_evtFile->precision(4);
  m_evtFile->open((outconfig->plotDir + "/events.txt").Data());
  m_binCount = 0;
}

void Plotting::finish()
{
  std::cout << "INFO::Plotting::Finishing plotting..." << std::endl;
  std::cout << "INFO::Plotting::Total number of bins: " << m_binCount << std::endl;
  m_evtFile->close();
  delete m_evtFile;
}

void Plotting::readHistosFromCat(Category& c)
{
  // std::cout << "Reading histograms from Category..." << std::endl;
  TString region = c.name();
  TString dist   = c.getStringProp(Property::dist);
  // data and signal (c.getHist returns clones)
  m_hData = c.getDataHist();
  m_hSig  = c.getSigHist();
  if( m_hData == nullptr || m_hSig == nullptr )
    return;
  m_hSig->SetTitle("Signal");
  // sample = pair(Sample, SampleInCategory)
  for( auto& sample : c.samples() ) {
    if( sample.first->type() == SType::Sig ) {
      TString name = region + sample.first->name();
      // sample.getNomHist return pointers, need to clone
      TH1* hist = (TH1*)sample.second.getNomHist()->Clone(name + "_clone");
      hist->SetTitle(sample.first->name());
      m_hSignals.push_back(hist);
    }
  }
  // backgrounds and stack
  TH1* hprev = 0;
  for( auto& sample : c.samples() ) {
    // std::cout << "title=" << sample.first->name() << std::endl;
    if( sample.first->type() == SType::Bkg || sample.first->type() == SType::DataDriven ) {
      TString name = region + sample.first->name();
      // sample.getNomHist return pointers, need to clone
      TH1* hist = (TH1*)sample.second.getNomHist()->Clone(name + "_clone");
      hist->SetLineColor(sample.first->color());
      hist->SetTitle(sample.first->name());
      m_hBkgs.push_back(hist);
      TH1* stack = (TH1*)hist->Clone(name + "_stack");
      stack->SetFillColor(sample.first->color());
      if( hprev ) {
        stack->Add(hprev);
      }
      m_hStack.push_back(stack);
      hprev = stack;
    }
  }
  // std::cout << "Blinding data ... " << std::endl;
  //  blind data
  if( m_hData ) {
    m_hDataBlind = (TH1*)(m_hData->Clone("dataForBlinding"));
    m_hDataBlind->SetLineColor(kBlack);
    m_hDataBlind->SetLineWidth(3);

    // blind to VHbbRun2 analysis
    TString anaType = m_conf.getValue("Analysis", "");
    if( anaType == "VHbbRun2" ) {
      if( c.getIntProp(Property::nTag) == 2 && c.getStringProp(Property::descr).Contains("SR") ) {
        if( c.getIntProp(Property::nTag) == 2 && (dist == "mBB" || dist == "mBBMVA") ) {
          // blind 80. < mBB < 140.
          // blind 110. < mBB < 140. if diboson unblinded
          for( int i = 0; i < m_hDataBlind->GetNbinsX() + 2; i++ ) {
            if( m_hDataBlind->GetXaxis()->GetBinLowEdge(i) >= 110 &&
                m_hDataBlind->GetXaxis()->GetBinUpEdge(i) <= 140 ) {
              m_hDataBlind->SetBinContent(i, 0);
              m_hDataBlind->SetBinError(i, 0);
            }
          }
        } else if( dist == "mva" || dist.Contains("mva") ) {
          // blind 60% of signal from right to left.
          int    nBinsX      = m_hDataBlind->GetNbinsX();
          double totalSignal = m_hSig->Integral(0, nBinsX + 1);
          if( nBinsX != m_hSig->GetNbinsX() ) {
            totalSignal = -1; // this shouldn't happen
            std::cout << "WARNING: number of bins in signal and data is different!!!!" << std::endl;
          }
          for( int i = m_hDataBlind->GetNbinsX() + 1; i >= 0; i-- ) {
            bool blind = false;
            if( totalSignal <= 0. )
              blind = true;
            else {
              float nSig = m_hSig->Integral(i, nBinsX + 1);
              if( nSig / totalSignal < 0.6 )
                blind = true;
            }
            if( blind ) {
              m_hDataBlind->SetBinContent(i, 0);
              m_hDataBlind->SetBinError(i, 0);
            }
          }
        } else {
          // variables other than "mBB" and "*mva*" ??!!
          std::cout << "WARNING: not expecting variable " << dist << " in nTag=2, SR" << std::endl;
        }
      } else {
        // the rest: blind S/B > 5%
        for( int i = 0; i < m_hDataBlind->GetNbinsX() + 2; i++ ) {
          float nSig  = m_hSig->GetBinContent(i);
          float nBkg  = m_hStack.back()->GetBinContent(i);
          bool  blind = false;
          if( nBkg <= 0 )
            blind = true; // blind if no backgrounds
          else {
            blind = (nSig / nBkg > 0.05);
          }
          if( blind ) {
            m_hDataBlind->SetBinContent(i, 0);
            m_hDataBlind->SetBinError(i, 0);
          }
        }
      }
    } // end if( anaType == "VHbbRun2")

    /*
    // Blinding for 2 Tag mass window
    if(c.getIntProp(Property::nTag) == 2 && dist == "mBB") {
    for(int i=0; i<m_hDataBlind->GetNbinsX()+2; i++) {
    if(m_hDataBlind->GetBinCenter(i) > 100 && m_hDataBlind->GetBinCenter(i)<150) {
    m_hDataBlind->SetBinContent(i, 0);
    m_hDataBlind->SetBinError(i, 0);
    }
    }
    }
    */
    /*
    // Blinding for 2 Tag SR
    if(c.getIntProp(Property::nTag) == 2 && c.getStringProp(Property::descr).Contains("SR")) {
      for(int i=0; i<m_hDataBlind->GetNbinsX()+2; i++) {
        m_hDataBlind->SetBinContent(i, 0);
        m_hDataBlind->SetBinError(i, 0);
      }
    }
    */

    /*
    if(c.getIntProp(Property::nTag) == 2 && !c.getStringProp(Property::spec).Contains("top")) {
      // blind mass region
      if(dist == "mjj" && m_specialMjjBlinding) {
        for(int i=0; i<m_hDataBlind->GetNbinsX()+2; i++) {
          if(m_hDataBlind->GetBinCenter(i) > 100 && m_hDataBlind->GetBinCenter(i)<150) {
            m_hDataBlind->SetBinContent(i, 0);
            m_hDataBlind->SetBinError(i, 0);
          }
        }
      }
      // blind other distr where S/B > 2%
      else {
        for(int i=0; i<m_hDataBlind->GetNbinsX()+2; i++) {
          float nSig = m_hSig->GetBinContent(i);
          float nBkg = m_hStack.back()->GetBinContent(i);
          bool blind = false;
          if (nSig > 0 && nBkg > 0) {
            blind = (nSig / nBkg > 0.02);
          }
          if(blind) {
            m_hDataBlind->SetBinContent(i, 0);
            m_hDataBlind->SetBinError(i, 0);
          }
        }
      }
    }
    */
  }
}

void Plotting::deleteHistos()
{
  delete m_hData;
  delete m_hDataBlind;
  delete m_hSig;
  m_hData      = 0;
  m_hDataBlind = 0;
  m_hSig       = 0;
  for( auto hist : m_hBkgs )
    delete hist;
  for( auto hist : m_hStack )
    delete hist;
  for( auto hist : m_hSignals )
    delete hist;
  m_hBkgs.clear();
  m_hStack.clear();
  m_hSignals.clear();
}

void Plotting::writeYields(Category& c)
{
  // std::cout << "Writing yields..." << std::endl;
  TString region = c.name();
  *m_evtFile << std::endl << region.Data() << std::endl;
  int    maxBin     = m_hData->GetNbinsX() + 1;
  float  dataInt    = m_hData->Integral(0, maxBin);
  double bkgStatErr = 0;
  float  bkgInt     = m_hStack.back()->IntegralAndError(0, maxBin, bkgStatErr);

  *m_evtFile << std::setw(10) << "data \t" << std::setw(8) << dataInt << "\t" << std::setw(8) << sqrt(dataInt)
             << std::endl;
  for( auto hist : m_hSignals ) {
    double sigError;
    *m_evtFile << std::setw(10) << hist->GetTitle() << "\t" << std::setw(8)
               << hist->IntegralAndError(0, maxBin, sigError) << "\t";
    *m_evtFile << std::setw(8) << " +/- " << sigError << "\t" << std::setw(8) << " | "
               << 100 * hist->Integral(0, maxBin) / bkgInt << std::endl;
  }
  for( auto hist : m_hBkgs ) {
    double bkgError;
    *m_evtFile << std::setw(10) << hist->GetTitle() << "\t" << std::setw(8)
               << hist->IntegralAndError(0, maxBin, bkgError) << "\t";
    *m_evtFile << std::setw(8) << " +/- " << bkgError << "\t" << std::setw(8) << " | "
               << 100 * hist->Integral(0, maxBin) / bkgInt << std::endl;
  }
  *m_evtFile << std::setw(10) << "Total Bkgd \t" << std::setw(8) << bkgInt << std::setw(8) << " +/- "
             << 100 * bkgStatErr / bkgInt << " %" << std::endl;
  *m_evtFile << std::setw(10) << "Data/MC \t" << std::setw(8) << dataInt / bkgInt << std::endl;
  *m_evtFile << std::endl;
}

void Plotting::makeMCStatRelErrorPlots(const Category& c)
{
  OutputConfig* outconfig = OutputConfig::getInstance();
  TString       region    = c.name();
  TString       dist      = c.getStringProp(Property::dist);

  // determine y min/max
  float max = 1;

  // initialize objects
  TCanvas* canvas = new TCanvas(region);
  canvas->cd();

  // get background histogram
  TH1F* rel_bkg = (TH1F*)c.getBkgHist();

  // create expected data stat histogram
  TH1F* rel_dat = (TH1F*)rel_bkg->Clone();
  for( int i = 1; i <= rel_dat->GetNbinsX(); i++ ) {
    if( rel_dat->GetBinContent(i) != 0 )
      rel_dat->SetBinContent(i, 1. / sqrt(rel_dat->GetBinContent(i)));
    else {
      rel_dat->SetBinContent(i, 0);
    }
  }

  // draw backgrounds
  for( int i = 1; i <= rel_bkg->GetNbinsX(); i++ ) {
    if( rel_bkg->GetBinContent(i) != 0 )
      rel_bkg->SetBinContent(i, rel_bkg->GetBinError(i) / rel_bkg->GetBinContent(i));
    else {
      rel_bkg->SetBinContent(i, 0);
    }
  }
  max = rel_bkg->GetMaximum();
  if( rel_dat->GetMaximum() > max ) {
    max = rel_dat->GetMaximum();
  }

  rel_bkg->SetMaximum(1.2 * max);
  rel_bkg->SetMinimum(0);

  rel_bkg->SetLineWidth(2);
  rel_bkg->SetLineColor(kBlue);
  rel_dat->SetLineWidth(2);
  rel_dat->SetLineColor(kRed);

  rel_bkg->SetStats(0);
  rel_bkg->SetXTitle(dist);
  rel_bkg->SetYTitle("Rel. Stat Error");
  rel_bkg->GetXaxis()->SetLabelSize(.04);
  rel_bkg->GetXaxis()->SetTitleSize(.04);
  rel_bkg->GetXaxis()->SetTitleOffset(1.);
  rel_bkg->GetYaxis()->SetLabelSize(.04);
  rel_bkg->GetYaxis()->SetTitleSize(.04);
  rel_bkg->GetYaxis()->SetTitleOffset(1.1);
  rel_bkg->Draw("hist");
  rel_dat->Draw("hist same");

  TLegend* leg = new TLegend(0.60, 0.54, 0.87, 0.86);
  setLegendStyle(leg);

  leg->AddEntry(rel_bkg, "MC Bkg", "l");
  leg->AddEntry(rel_dat, "exp. Data (bkg-only)", "l");
  leg->Draw();

  canvas->Print(outconfig->plotDir + "/mass/" + region + "_MCStatRelError." + m_format);
  if( m_createAllRootFiles )
    canvas->SaveAs(outconfig->plotDir + "/mass/" + region + "_MCStatRelError.root");

  // clean up
  delete rel_bkg;
  delete rel_dat;
  delete leg;
  delete canvas;
}

void Plotting::makeStackPlot(Category& c)
{
  // std::cout << "Plotting stack..." << std::endl;
  OutputConfig* outconfig = OutputConfig::getInstance();
  TString       region    = c.name();
  TString       dist      = c.getStringProp(Property::dist);
  bool          logScale  = m_conf.getValue("LogScalePlots", false);

  // determine y min/max
  float max = 1;
  float min = 0;
  if( m_hData ) {
    max = m_hData->GetMaximum();
  }
  for( auto hist : m_hStack ) {
    if( hist->GetMaximum() > max ) {
      max = hist->GetMaximum();
    }
    if( hist->GetMinimum() < min ) {
      min = hist->GetMinimum();
    }
  }

  // initialize objects
  TCanvas* canvas = new TCanvas(region);
  canvas->cd();
  if( logScale )
    canvas->SetLogy();
  TLegend* leg = new TLegend(0.67, 0.54, 0.87, 0.86);
  setLegendStyle(leg);

  // draw backgrounds
  for( int i = m_hStack.size() - 1; i >= 0; i-- ) {
    TH1* hist = m_hStack[i];
    if( !hist ) {
      continue;
    }
    leg->AddEntry(hist, hist->GetTitle(), "f");
    if( hist == m_hStack.back() ) {
      hist->SetTitle(region); // FIXME this will override the sample name for the legend
      if( !logScale ) {
        hist->SetMaximum(1.2 * max);
        hist->SetMinimum(min);
      } else {
        hist->SetMaximum(10 * max);
        hist->SetMinimum(1e-3);
      }
      hist->SetStats(0);
      hist->SetXTitle(dist);
      hist->SetYTitle("entries / bin");
      hist->GetXaxis()->SetLabelSize(.04);
      hist->GetXaxis()->SetTitleSize(.04);
      hist->GetXaxis()->SetTitleOffset(1.);
      hist->GetYaxis()->SetLabelSize(.04);
      hist->GetYaxis()->SetTitleSize(.04);
      hist->GetYaxis()->SetTitleOffset(1.);
      hist->Draw("hist");
    } else {
      hist->Draw("same hist");
    }
  }

  // draw signal
  float sigScale = 10;
  if( logScale )
    sigScale = 1;
  m_hSig->Scale(sigScale);
  m_hSig->SetLineColor(kRed);
  m_hSig->Draw("same hist");
  leg->AddEntry(m_hSig, TString::Format("signal (x%i)", (int)sigScale).Data(), "f");

  // draw data
  if( m_hDataBlind ) {
    m_hDataBlind->SetMarkerStyle(8);
    m_hDataBlind->SetMarkerSize(1);
    m_hDataBlind->Draw("samep");
    leg->AddEntry(m_hDataBlind, "Data", "l");
  }
  leg->Draw("same");
  canvas->Print(outconfig->plotDir + "/mass/" + region + "_stack." + m_format);
  if( m_createAllRootFiles )
    canvas->SaveAs(outconfig->plotDir + "/mass/" + region + "_stack.root");

  m_hSig->Scale(1 / sigScale); // TODO make nicer

  // clean up
  delete leg;
  delete canvas;
}

void Plotting::makePieChartPlot(Category& c)
{
  std::cout << "Plotting pie chart..." << std::endl;
  OutputConfig* outconfig      = OutputConfig::getInstance();
  TString       region         = c.name();
  TString       dist           = c.getStringProp(Property::dist);
  float         mergeThreshold = 0.02;

  // initialize objects
  TCanvas canvas(region, region, 600, 600);
  canvas.cd();

  int nBkg = m_hBkgs.size();
  // TODO want to have region title?
  TPie pie("pie", region, nBkg + 1); // one entry for merged bkgs
  pie.SetEntryLabel(nBkg, "");

  TH1* bkgSum      = m_hStack.at(nBkg - 1);
  int  nBin        = bkgSum->GetNbinsX();
  int  bkgSumYield = bkgSum->Integral(0, nBin + 2);

  // loop over backgrounds and fill pie
  for( int i = 0; i < nBkg; i++ ) {
    TH1* hist      = m_hBkgs.at(i);
    TH1* histStack = m_hStack.at(i);
    if( !hist || !histStack ) {
      continue;
    }
    float yield = hist->Integral(0, nBin + 2);
    if( yield / bkgSumYield > mergeThreshold ) {
      // fill current entry
      pie.SetEntryVal(i, yield);
      pie.SetEntryLabel(i, hist->GetTitle());
      pie.SetEntryFillColor(i, histStack->GetFillColor());
    } else {
      // fill rest entry, hide current one
      float restYield = pie.GetEntryVal(nBkg) + yield;
      pie.SetEntryVal(nBkg, restYield);
      pie.SetEntryLabel(nBkg, "Rest");
      pie.SetEntryLabel(i, "");
      pie.SetEntryFillColor(nBkg, kBlack);
    }
  }

  pie.SetRadius(0.28);
  pie.SetLabelsOffset(0.02);
  // TODO: could move pie a bit down and add S/B, ... labels above
  // pie.SetY(0.4);
  pie.Draw("nol");
  canvas.Print(outconfig->plotDir + "/mass/" + region + "_pie." + m_format);
  if( m_createAllRootFiles )
    canvas.SaveAs(outconfig->plotDir + "/mass/" + region + "_pie.root");
}

void Plotting::makeSoBPlot(Category& c)
{
  // std::cout << "Plotting signal over different backgrounds..." << std::endl;
  OutputConfig* outconfig = OutputConfig::getInstance();
  TString       region    = c.name();
  TString       dist      = c.getStringProp(Property::dist);

  // fill SoverB histograms
  std::vector<TH1*> v_sob;
  for( auto hist : m_hBkgs ) {
    TH1* copy = (TH1*)m_hSig->Clone();
    copy->Divide(hist);
    copy->SetFillColor(0);
    copy->SetFillStyle(0);
    copy->SetLineWidth(4);
    copy->SetLineStyle(1);
    copy->SetLineColor(hist->GetLineColor());
    copy->SetTitle(hist->GetTitle());
    copy->SetName(hist->GetName());
    v_sob.push_back(copy);
  }
  TH1* copy = (TH1*)m_hSig->Clone();
  copy->Divide(m_hStack.back());
  copy->SetTitle("Background");
  copy->SetName("Background");
  copy->SetFillColor(0);
  copy->SetFillStyle(0);
  copy->SetLineWidth(4);
  copy->SetLineStyle(1);
  copy->SetLineColor(1);
  v_sob.push_back(copy);

  // initialize objects
  TCanvas* canvas = new TCanvas(region);
  canvas->cd();
  TLegend* leg = new TLegend(0.17, 0.54, 0.37, 0.86);
  setLegendStyle(leg);

  // draw backgrounds
  bool first = true;
  for( auto hist : v_sob ) {
    if( !hist ) {
      continue;
    }
    leg->AddEntry(hist, hist->GetTitle(), "l");
    if( first ) {
      hist->SetTitle(region); // FIXME this will override the sample name for the legend
      hist->SetMaximum(100);
      hist->SetMinimum(1.e-4);
      hist->SetStats(0);
      hist->SetXTitle(dist);
      hist->SetYTitle("S/B");
      hist->GetXaxis()->SetLabelSize(.04);
      hist->GetXaxis()->SetTitleSize(.04);
      hist->GetXaxis()->SetTitleOffset(1.);
      hist->GetYaxis()->SetLabelSize(.04);
      hist->GetYaxis()->SetTitleSize(.04);
      hist->GetYaxis()->SetTitleOffset(1.);
      hist->Draw("hist");
      first = false;
    } else {
      hist->Draw("same hist");
    }
  }

  leg->Draw("same");
  canvas->SetLogy();
  canvas->SetTicky();
  canvas->SetGridy();
  canvas->Print(outconfig->plotDir + "/mass/" + region + "_sob." + m_format);
  if( m_createAllRootFiles )
    canvas->SaveAs(outconfig->plotDir + "/mass/" + region + "_sob.root");

  // clean up
  for( auto hist : v_sob ) {
    delete hist;
  }
  delete leg;
  delete canvas;
}

void Plotting::makeStatPlot(Category& c)
{

  OutputConfig* outconfig = OutputConfig::getInstance();
  TString       region    = c.name();
  float         max       = 0;

  // copy histograms
  TH1*              bkg = (TH1*)m_hStack.back()->Clone();
  std::vector<TH1*> statErrs;
  statErrs.push_back((TH1*)m_hSig->Clone());
  for( auto hist : m_hBkgs ) {
    TH1* statErr = (TH1*)hist->Clone();
    statErrs.push_back(statErr);
  }

  // calculate stat errors
  for( int b = 0; b < bkg->GetNbinsX() + 2; b++ ) {
    float value(0);
    for( auto hist : statErrs ) {
      value = hist->GetBinError(b) / hist->GetBinContent(b);
      if( hist->GetBinContent(b) == 0 ) {
        value = 0;
      }
      if( value > max ) {
        max = value;
      }
      hist->SetBinContent(b, value);
      hist->SetBinError(b, 0);
    }
    value = bkg->GetBinError(b) / bkg->GetBinContent(b);
    if( bkg->GetBinContent(b) == 0 ) {
      value = 0;
    }
    if( value > max ) {
      max = value;
    }
    bkg->SetBinContent(b, value);
    bkg->SetBinError(b, 0);
  }

  // limit max
  if( max > 1 ) {
    max = 1;
  }

  // style
  bkg->SetFillColor(0);
  bkg->SetFillStyle(0);
  bkg->SetLineWidth(4);
  bkg->SetLineStyle(4);
  bkg->SetLineColor(kBlack);
  for( auto hist : statErrs ) {
    hist->SetFillColor(0);
    ;
    hist->SetFillStyle(0);
    ;
    hist->SetLineWidth(2);
    ;
  }

  // draw
  TCanvas* canvas = new TCanvas();
  TLegend* leg    = new TLegend(0.67, 0.54, 0.87, 0.86);
  setLegendStyle(leg);
  bkg->SetMaximum(1.2 * max);
  bkg->GetYaxis()->SetRangeUser(0, 1.2 * max);
  bkg->GetYaxis()->SetTitle("MC Stat Rel. Error");
  bkg->Draw("hist");
  for( auto hist : statErrs ) {
    hist->SetMaximum(1.2 * max);
    hist->Draw("same hist");
    leg->AddEntry(hist, hist->GetTitle(), "f");
  }
  bkg->Draw("same hist");
  leg->AddEntry(bkg, "Total Bkg", "l");
  leg->Draw("same");
  canvas->Print(outconfig->plotDir + "/mass/" + region + "_stats." + m_format);
  if( m_createAllRootFiles )
    canvas->SaveAs(outconfig->plotDir + "/mass/" + region + "_stats.root");

  // clean up
  delete canvas;
  delete leg;
  delete bkg;
  for( auto hist : statErrs ) {
    delete hist;
  }
}

void Plotting::setLegendStyle(TLegend* leg)
{
  leg->SetBorderSize(0);
  leg->SetFillColor(0);
  leg->SetLineColor(0);
  leg->SetFillStyle(0);
  // l->SetTextFont(62);
  leg->SetTextSize(0.030);
  return;
}

void Plotting::makeSystStatusPlots(const Category& c) const
{
  gStyle->SetPaintTextFormat("1.2f");
  // prepare the output
  TString       region    = c.name();
  OutputConfig* outconfig = OutputConfig::getInstance();

  const auto&       samples = c.samples();
  std::set<TString> normSysts;
  std::set<TString> shapeSysts;
  std::set<TString> names;

  // fill the lists of systematics and samples
  for( const auto& spair : samples ) {
    names.insert(spair.first->name());
    const SampleInCategory& sic        = spair.second;
    std::set<TString>       normNames  = sic.getConsideredSysts(SysType::norm);
    std::set<TString>       shapeNames = sic.getConsideredSysts(SysType::shape);
    normSysts.insert(normNames.begin(), normNames.end());
    shapeSysts.insert(shapeNames.begin(), shapeNames.end());
  }

  // prepare the plots
  TH2I* hnormStatus =
      new TH2I("normStatus", "normStatus", normSysts.size(), 0, normSysts.size(), names.size(), 0, names.size());
  TH2F* hnormVal = new TH2F("normVal", "normVal", normSysts.size(), 0, normSysts.size(), names.size(), 0, names.size());
  TH2I* hshapeStatus =
      new TH2I("shapeStatus", "shapeStatus", shapeSysts.size(), 0, shapeSysts.size(), names.size(), 0, names.size());
  TH2D* hsmoothChi2Up = new TH2D("smoothChi2Up", ("#chi^{2}_{/NDF}(smooth vs. initial) " + c.name()).Data(),
                                 shapeSysts.size(), 0, shapeSysts.size(), names.size(), 0, names.size());
  TH2D* hsmoothChi2Do = new TH2D("smoothChi2Do", ("#chi^{2}_{/NDF}(smooth vs. initial) " + c.name()).Data(),
                                 shapeSysts.size(), 0, shapeSysts.size(), names.size(), 0, names.size());
  // To zoom in the histograms
  TFile* hnormValFile = new TFile(outconfig->plotDir + "/systs/" + region + "_normVal.root", "RECREATE");

  // make thre range always from 0 to 6:
  hnormStatus->SetMaximum(6);
  hshapeStatus->SetMaximum(6);

  int i = 1;
  for( auto& s : names ) {
    hnormStatus->GetYaxis()->SetBinLabel(i, s);
    hnormVal->GetYaxis()->SetBinLabel(i, s);
    hshapeStatus->GetYaxis()->SetBinLabel(i, s);
    hsmoothChi2Up->GetYaxis()->SetBinLabel(i, s);
    hsmoothChi2Do->GetYaxis()->SetBinLabel(i, s);
    i++;
  }
  i = 1;
  for( auto& s : normSysts ) {
    hnormStatus->GetXaxis()->SetBinLabel(i, s);
    hnormVal->GetXaxis()->SetBinLabel(i, s);
    i++;
  }
  i = 1;
  for( auto& s : shapeSysts ) {
    hshapeStatus->GetXaxis()->SetBinLabel(i, s);
    hsmoothChi2Up->GetXaxis()->SetBinLabel(i, s);
    hsmoothChi2Do->GetXaxis()->SetBinLabel(i, s);
    i++;
  }

  // fill the plots
  for( const auto& spair : samples ) {
    const SampleInCategory& sic  = spair.second;
    TString                 name = spair.first->name();
    int                     biny = hnormVal->GetYaxis()->FindBin(name);
    for( auto& s : normSysts ) {
      SysKey key  = std::make_pair(SysType::norm, s);
      int    binx = hnormStatus->GetXaxis()->FindBin(s);
      hnormStatus->SetBinContent(binx, biny, sic.getSystStatus(key));
      hnormVal->SetBinContent(binx, biny, sic.getMeanNormEffect(key) * 100);
    }
    for( auto& s : shapeSysts ) {
      int    binx = hshapeStatus->GetXaxis()->FindBin(s);
      SysKey key  = std::make_pair(SysType::shape, s);
      hshapeStatus->SetBinContent(binx, biny, sic.getSystStatus(key));

      const double testUp = sic.getChi2SmoothTest(key, Systematic::Side::up);
      const double testDo = sic.getChi2SmoothTest(key, Systematic::Side::down);
      if( testUp >= 0. )
        hsmoothChi2Up->SetBinContent(binx, biny, testUp);
      if( testDo >= 0. )
        hsmoothChi2Do->SetBinContent(binx, biny, testDo);
    }
  }

  std::set<TH2*> h2sys;
  h2sys.insert(hnormStatus);
  h2sys.insert(hnormVal);
  h2sys.insert(hshapeStatus);
  h2sys.insert(hsmoothChi2Up);
  h2sys.insert(hsmoothChi2Do);

  // TStyle *style = new TStyle();
  Int_t   palette[6] = {kWhite, kYellow, kOrange - 3, kOrange + 10, kRed + 1, kGreen + 2}; // color palette
  TString histoName, label;
  bool    canBePrinted = true;

  TCanvas can("can", "can", 800, 600);
  can.SetMargin(0.1, 0.15, 0.2, 0.1);

  for( auto h : h2sys ) {

    // Style
    h->SetStats(kFALSE);
    h->GetXaxis()->SetLabelSize(0.03);
    h->GetXaxis()->SetTickLength(0);
    h->GetXaxis()->LabelsOption("v");

    h->GetYaxis()->SetLabelSize(0.03);
    h->GetYaxis()->SetTickLength(0);

    // We split the 2D in Btag,JES and rest for make them easier to read
    auto ressys = split2Dplot(h);
    delete h;
    for( auto hsplit : ressys ) {

      histoName = hsplit->GetName();

      // We apply special palette in Status plots.
      if( histoName.Contains("Status") ) {
        gStyle->SetPalette(6, palette);
      } else if( histoName.Contains("Chi2") ) {
        gStyle->SetPalette(1);
        if( hsplit->GetMaximum() < 1. )
          hsplit->SetMaximum(1.);
        if( hsplit->GetMaximum() > 4. )
          hsplit->SetMaximum(4.);
      } else {
        gStyle->SetPalette(1);
      }

      // We compress the name of the label by removing "Sys", "SoftTerm",...
      for( int bin = 1; bin < hsplit->GetXaxis()->GetNbins() + 1; ++bin ) {
        label = hsplit->GetXaxis()->GetBinLabel(bin);
        label.ReplaceAll("Sys", "");
        label.ReplaceAll("SoftTerms", "ST");
        label.ReplaceAll("multijet", "MJ");
        label.ReplaceAll("Multijet", "MJ");

        TString anaType = std::getenv("ANALYSISTYPE");
        if( anaType == "boostedVHbbRun2" ) {
          label.ReplaceAll("Sys", "");
          label.ReplaceAll("FT_EFF_Eigen", "FT");
          label.ReplaceAll("stat_Region_", "Gamma_");
          label.ReplaceAll("MCStat_", "ddttbar_");
          label.ReplaceAll("extrapolation", "extrap");
          label.ReplaceAll("JET_21NP_", "");
          label.ReplaceAll("JET_23NP_", "");
          label.ReplaceAll("JET_CR_JET_JER", "JER");
          label.ReplaceAll("JET_CR_JET", "JET");
          label.ReplaceAll("JET_JER_SINGLE_NP", "JER");
          label.ReplaceAll("JET_GroupedNP", "JET");
          label.ReplaceAll("EtaIntercalibration", "EtaIntercal");
          label.ReplaceAll("Flavor_Composition", "FlavComp");
          label.ReplaceAll("Pileup", "PU");
          label.ReplaceAll("SoftTerms", "ST");
          label.ReplaceAll("multijet", "QCDMJ");
          label.ReplaceAll("Multijet", "QCDMJ");
          label.ReplaceAll("dist", "d");
          label.ReplaceAll("MedHighPtv", "Ptv");
          label.ReplaceAll("RatioHP", "R_HP");
          label.ReplaceAll("RatioPtv", "R_Ptv");
          label.ReplaceAll("RatioSR", "R_SR");
          label.ReplaceAll("Ratiottbar", "R_ttbar");
          label.ReplaceAll("L_BMin400", "L_400");
          label.ReplaceAll("Ptv_BMin400", "Ptv_400");
          label.ReplaceAll("FATJET", "FJ");
          label.ReplaceAll("MJJMR", "FJ_JMR");
          label.ReplaceAll("Medium_JET_Comb", "JMSJES");
          label.ReplaceAll("_Kin", "");
          label.ReplaceAll("MbbBoosted", "mJShape");
          label.ReplaceAll("DSRnoaddbjetsr", "SR");
          label.ReplaceAll("DSRtopaddbjetcr", "CR");
          label.ReplaceAll("Y2015_", "");
          label.ReplaceAll("_TOTAL_1NPCOR_PLUS_UNCOR", "_TOTAL_");
        }

        hsplit->GetXaxis()->SetBinLabel(bin, label);
      }
      if( histoName.Contains("normVal") ) {
        hsplit->Draw("colztext");
      } else {
        hsplit->Draw("colz");
      }
      // We make sure that the TH2F has something to plot. Some regions make TH2* come empty after splitting them.
      canBePrinted = true;
      if( hsplit->GetXaxis()->GetNbins() == 0 ) {
        canBePrinted = false;
      }
      if( canBePrinted ) {
        can.Print(outconfig->plotDir + "/systs/" + region + "_" + hsplit->GetName() + "." + m_format);
        if( m_createAllRootFiles )
          can.SaveAs(outconfig->plotDir + "/systs/" + region + "_" + hsplit->GetName() + ".root");

        if( histoName.Contains("normVal") ) {
          hnormValFile->cd();
          hsplit->Write();
        }
      }
      delete hsplit;
    }
  }
  hnormValFile->Close();
  delete hnormValFile;
}

void Plotting::makeSystShapePlots(const Category& c) const
{
  OutputConfig* outconfig      = OutputConfig::getInstance();
  TString       region         = c.name();
  TString       dist           = c.getStringProp(Property::dist);
  const auto&   samples        = c.samples();
  double        m_tsize        = 0.04;
  TCanvas*      canvas         = new TCanvas("canvas", "canvas", 600, 400);
  const bool    overlayNominal = m_conf.getValue("OverlayNominalForSystShapes", true);

  bool doRealBinning = m_conf.getValue("UseRealBinningInSysPlot", false);
  bool doNormBand    = m_conf.getValue("ShowMCStatBandInSysPlot", false);

  std::vector<float> theBinning = c.getBinningFloat();
  int                binSize    = theBinning.size();
  float*             newBin     = 0;
  newBin                        = new float[binSize];
  for( int bin = binSize - 1; bin >= 0; bin-- ) {
    // std::cout << " bin: " << bin << " --> " << theBinning[bin] << std::endl;
    newBin[binSize - 1 - bin] = theBinning[bin];
  }
  // exit(-1);

  // loop over samples
  for( const auto& spair : samples ) {
    TString name = spair.first->name();
    // std::cout<<"Component Name:= "<<name<<std::endl;
    if( name == "data" )
      continue;
    const SampleInCategory& sic = spair.second;
    // get Nominal hist
    TH1*   h_NomHist = (TH1*)sic.getNomHist();
    double maxX      = h_NomHist->GetXaxis()->GetXmax();

    // this is a bit nasty but I realy don't have time to rewrite all the code
    // ... just a little attention ...
    if( doRealBinning ) {
      h_NomHist = rebinToOriginal(h_NomHist, newBin);
    }

    std::set<TString> shapeNames = sic.getConsideredSysts(SysType::shape);
    std::set<TString> normNames  = sic.getConsideredSysts(SysType::norm);

    // define the normalised nominal for the error band
    TH1*  h_Norm   = (TH1*)h_NomHist->Clone("nom");
    float maxNomV  = -1;
    float valRatio = 0;
    for( int bin = 0; bin <= h_NomHist->GetNbinsX(); bin++ ) {
      double val = h_NomHist->GetBinContent(bin);
      h_Norm->SetBinContent(bin, 0.);
      if( val == 0 ) {
        h_Norm->SetBinError(bin, 0.);
      } else {
        valRatio = 100 * h_NomHist->GetBinError(bin) / val;
        if( valRatio > maxNomV )
          maxNomV = valRatio;
        h_Norm->SetBinError(bin, valRatio);
      }
    }
    h_Norm->SetLineColor(1);
    h_Norm->SetLineWidth(2);
    h_Norm->SetMarkerSize(0);
    h_Norm->SetFillColor(0);
    h_Norm->SetFillStyle(3344);
    h_Norm->SetFillColor(kYellow - 7);

    // loop over systematics
    for( auto& s : shapeNames ) {
      canvas->Clear();
      // std::cout << "Requested systematic name " << s << std::endl;
      const SysKey key     = std::make_pair(SysType::shape, s);
      const SysKey keyNorm = std::make_pair(SysType::norm, s);

      // std::cout<< "Read systematic histos"<<std::endl;
      TH1*    h_tmpUp = (TH1*)sic.getShapeSyst(key, Systematic::Side::up);
      TH1*    h_tmpDo = (TH1*)sic.getShapeSyst(key, Systematic::Side::down);
      TString fNorm;
      fNorm += sic.getMeanNormEffect(keyNorm) * 100;
      fNorm.Resize(4);
      fNorm = "NormEff = " + fNorm + "%";
      if( !h_tmpUp || !h_tmpDo ) {
        // std::cout<<"Requested histogram not found"<<std::endl;
        continue;
      }
      if( doRealBinning ) {
        h_tmpUp = rebinToOriginal(h_tmpUp, newBin);
        h_tmpDo = rebinToOriginal(h_tmpDo, newBin);
      }
      TString hSystName     = h_tmpUp->GetName();
      TH1*    h_ShapeSystUp = (TH1*)h_tmpUp->Clone(hSystName + "_Up");
      TH1*    h_ShapeSystDo = (TH1*)h_tmpDo->Clone(hSystName + "_Do");

      TH1*                 h_shapeSystUp_unsmoothed_tmp = (TH1*)sic.getShapeSyst(key, Systematic::Side::up, true);
      TH1*                 h_shapeSystDo_unsmoothed_tmp = (TH1*)sic.getShapeSyst(key, Systematic::Side::down, true);
      std::unique_ptr<TH1> h_shapeSystUp_unsmoothed, h_shapeSystDo_unsmoothed;

      if( doRealBinning ) {
        if( h_shapeSystUp_unsmoothed_tmp ) {
          h_shapeSystUp_unsmoothed_tmp = rebinToOriginal(h_shapeSystUp_unsmoothed_tmp, newBin);
        }
        if( h_shapeSystDo_unsmoothed_tmp ) {
          h_shapeSystDo_unsmoothed_tmp = rebinToOriginal(h_shapeSystDo_unsmoothed_tmp, newBin);
        }
      }

      // calculate shift
      std::vector<double> minAndMax;
      h_ShapeSystUp->SetTitle(region);
      h_ShapeSystUp->Add(h_NomHist, -1);
      h_ShapeSystUp->Divide(h_NomHist);
      h_ShapeSystUp->Scale(100.);
      h_ShapeSystDo->Add(h_NomHist, -1);
      h_ShapeSystDo->Divide(h_NomHist);
      h_ShapeSystDo->Scale(100.);
      h_ShapeSystUp->SetLineColor(kRed);
      h_ShapeSystDo->SetLineColor(4);
      h_ShapeSystUp->SetLineWidth(2);
      h_ShapeSystDo->SetLineWidth(2);
      h_ShapeSystUp->SetStats(kFALSE);
      h_ShapeSystUp->Draw("hist");
      if( doNormBand )
        h_Norm->Draw("SAMEE2");
      h_ShapeSystDo->Draw("hist same");
      h_ShapeSystUp->Draw("hist same");
      if( h_shapeSystUp_unsmoothed_tmp ) {
        h_shapeSystUp_unsmoothed.reset((TH1*)h_shapeSystUp_unsmoothed_tmp->Clone(hSystName + "_unsmoothedUp"));
        h_shapeSystUp_unsmoothed->Add(h_NomHist, -1);
        h_shapeSystUp_unsmoothed->Divide(h_NomHist);
        h_shapeSystUp_unsmoothed->Scale(100.);
        h_shapeSystUp_unsmoothed->SetLineColor(kRed);
        h_shapeSystUp_unsmoothed->SetLineStyle(2);
        h_shapeSystUp_unsmoothed->Draw("same HIST");
        minAndMax.push_back(h_shapeSystUp_unsmoothed->GetMaximum());
        minAndMax.push_back(h_shapeSystUp_unsmoothed->GetMinimum());
      }
      if( h_shapeSystDo_unsmoothed_tmp ) {
        h_shapeSystDo_unsmoothed.reset((TH1*)h_shapeSystDo_unsmoothed_tmp->Clone(hSystName + "_unsmoothedDo"));
        h_shapeSystDo_unsmoothed->Add(h_NomHist, -1);
        h_shapeSystDo_unsmoothed->Divide(h_NomHist);
        h_shapeSystDo_unsmoothed->Scale(100.);
        h_shapeSystDo_unsmoothed->SetLineColor(4);
        h_shapeSystDo_unsmoothed->SetLineStyle(2);
        h_shapeSystDo_unsmoothed->Draw("same HIST");
        minAndMax.push_back(h_shapeSystDo_unsmoothed->GetMaximum());
        minAndMax.push_back(h_shapeSystDo_unsmoothed->GetMinimum());
      }

      h_ShapeSystUp->Draw("histsame");
      h_ShapeSystDo->Draw("histsame");
      // draw a line
      TLine the1(h_ShapeSystUp->GetXaxis()->GetXmin(), 0., h_ShapeSystUp->GetXaxis()->GetXmax(), 0.);
      the1.SetLineWidth(2);
      the1.SetLineColor(922);
      the1.SetLineStyle(2);
      the1.Draw("SAME");

      double maxFactor = 1.1;
      double maxNom    = h_NomHist->GetMaximum();
      minAndMax.push_back(h_ShapeSystUp->GetMaximum());
      minAndMax.push_back(h_ShapeSystDo->GetMaximum());
      minAndMax.push_back(h_ShapeSystUp->GetMinimum());
      minAndMax.push_back(h_ShapeSystDo->GetMinimum());
      std::sort(minAndMax.begin(), minAndMax.end());
      double       max         = minAndMax.back();
      double       min         = minAndMax.front();
      const double spikeThresh = 5.;
      if( max > spikeThresh * minAndMax.at(minAndMax.size() - 2) ) {
        // This is an ugly spike in one of the histograms, don't extend the plot range up to here
        max = spikeThresh * minAndMax.at(minAndMax.size() - 2);
      }
      if( min < spikeThresh * minAndMax.at(1) ) {
        // This is an ugly spike in one of the histograms, don't extend the plot range up to here
        min = spikeThresh * minAndMax.at(1.);
      }
      double delta   = max - min;
      double maxHist = min + maxFactor * delta;
      double minHist = max - maxFactor * delta;
      h_ShapeSystUp->GetYaxis()->SetRangeUser(minHist, maxHist);
      h_ShapeSystUp->GetYaxis()->SetTitle("Shift [%]");
      TH1* h_nomScaled = nullptr;
      if( overlayNominal ) {
        h_nomScaled = (TH1*)h_NomHist->Clone();
        h_nomScaled->Scale(delta / maxNom);
        for( int iBin = 0; iBin <= h_nomScaled->GetNbinsX() + 1; iBin++ ) {
          double cont = h_nomScaled->GetBinContent(iBin);
          cont += minHist;
          h_nomScaled->SetBinContent(iBin, cont);
        }
        h_nomScaled->Draw("E1 same");
      }

      // labels
      TLatex* latex = new TLatex();
      latex->DrawTextNDC(0.3, 0.85, key.second.Data());
      latex->DrawTextNDC(0.3, 0.77, h_NomHist->GetName());
      latex->DrawTextNDC(0.3, 0.69, fNorm.Data());
      if( h_shapeSystDo_unsmoothed || h_shapeSystUp_unsmoothed ) {
        std::ostringstream stream;
        stream << "#chi^{2}/NDF: Up=" << std::setprecision(3) << sic.getChi2SmoothTest(key, Systematic::Side::up)
               << " Do=" << sic.getChi2SmoothTest(key, Systematic::Side::down);
        latex->SetTextSize(latex->GetTextSize() * 0.7);
        latex->DrawLatexNDC(0.11, 0.12, stream.str().c_str());
      }

      // axis
      TGaxis* axis = nullptr;
      if( h_nomScaled ) {
        axis = new TGaxis(maxX, minHist, maxX, maxHist, 0, (2 * maxFactor - 1) * maxNom, 510, "+L");
        axis->SetLabelSize(0.05);
        axis->SetLabelFont(42);
        axis->SetTitleSize(0.05);
        axis->SetTitleFont(42);
        axis->SetTitle("Events");
        axis->SetTitleOffset(1.5);
        axis->Draw();
      }
      h_ShapeSystUp->GetXaxis()->SetTitle(dist);

      // legend
      TLegend* leg = new TLegend(0.7, 0.75, 0.8, 0.9);
      leg->SetFillStyle(0);
      leg->SetBorderSize(0);
      leg->SetTextSize(m_tsize);
      leg->AddEntry(h_ShapeSystUp, "Up", "l");
      leg->AddEntry(h_ShapeSystDo, "Down", "l");
      if( h_shapeSystUp_unsmoothed )
        leg->AddEntry(h_shapeSystUp_unsmoothed.get(), "Unsmoothed", "l");
      leg->Draw();

      // set histo name
      TString plotFileName = outconfig->plotDir + "/shapes/" + region + "_" + name + "_" + key.second + "." + m_format;
      canvas->Print(plotFileName.Data());
      if( m_createAllRootFiles ) {
        plotFileName = outconfig->plotDir + "/shapes/" + region + "_" + name + "_" + key.second + ".root";
        canvas->SaveAs(plotFileName.Data());
      }

      delete h_ShapeSystUp;
      delete h_ShapeSystDo;
      delete h_nomScaled;
      delete latex;
      delete axis;
      delete leg;

      if( doRealBinning ) {
        delete h_tmpUp;
        delete h_tmpDo;
        if( h_shapeSystUp_unsmoothed_tmp )
          delete h_shapeSystUp_unsmoothed_tmp;
        if( h_shapeSystDo_unsmoothed_tmp )
          delete h_shapeSystDo_unsmoothed_tmp;
      }
    }

    if( doRealBinning )
      delete h_NomHist;

    delete h_Norm;
  }
  if( newBin != 0 )
    delete newBin;

  delete canvas;
  return;
}

std::vector<TH1*> Plotting::split2Dplot(const TH2* h) const
{
  std::vector<TH1*> res;
  TH1*              tmp = PU::reduceTHAxisInclude(h, true, {"SysJET", "SysMET", "SysBJet"});
  tmp->SetName(TString(h->GetName()) + "_JetMET");
  res.push_back(tmp);
  tmp = PU::reduceTHAxisInclude(h, true, {"SysFT"});
  tmp->SetName(TString(h->GetName()) + "_BTag");
  res.push_back(tmp);
  tmp = PU::reduceTHAxisInclude(h, true, {"SysMUON", "SysEL", "SysEG", "SysTAUS"});
  tmp->SetName(TString(h->GetName()) + "_Lepton");
  res.push_back(tmp);
  tmp = PU::reduceTHAxisExclude(h, true, {"SysJET", "SysMET", "SysFT", "SysMUON", "SysEL", "SysEG", "SysTAUS"});
  tmp->SetName(TString(h->GetName()) + "_Other");
  res.push_back(tmp);
  return res;
}

void Plotting::makeOverallSystStatusPlots(const CategoryHandler& handler) const
{
  gStyle->SetPaintTextFormat("1.2f");
  // prepare the output
  OutputConfig* outconfig = OutputConfig::getInstance();

  std::set<TString> normSysts;
  std::set<TString> shapeSysts;
  std::set<TString> names;
  std::set<TString> regions;

  for( const auto& c : handler ) {
    TString region = c.name();
    regions.insert(region);
    const auto& samples = c.samples();
    // fill the lists of systematics and samples
    for( const auto& spair : samples ) {
      names.insert(spair.first->name());
      const SampleInCategory& sic        = spair.second;
      std::set<TString>       normNames  = sic.getConsideredSysts(SysType::norm);
      std::set<TString>       shapeNames = sic.getConsideredSysts(SysType::shape);
      normSysts.insert(normNames.begin(), normNames.end());
      shapeSysts.insert(shapeNames.begin(), shapeNames.end());
    }
  }

  // To zoom in the histograms
  TFile* hnormValFile = new TFile(outconfig->plotDir + "/systs/" + "normVals.root", "RECREATE");

  // first normalization systematics
  for( auto& sys : normSysts ) {
    // prepare the plots
    TH2I* hnormStatus = new TH2I("normStatus", Form("normStatus: %s", sys.Data()), regions.size(), 0, regions.size(),
                                 names.size(), 0, names.size());
    TH2F* hnormVal    = new TH2F("normVal", Form("normVal: %s", sys.Data()), regions.size(), 0, regions.size(),
                                 names.size() + 1, 0, names.size() + 1);
    hnormStatus->SetMaximum(6);

    int i = 1;
    for( auto& s : names ) {
      hnormStatus->GetYaxis()->SetBinLabel(i, s);
      hnormVal->GetYaxis()->SetBinLabel(i, s);
      i++;
    }
    hnormVal->GetYaxis()->SetBinLabel(names.size() + 1, "All");

    i = 1;
    for( auto& s : regions ) {
      hnormStatus->GetXaxis()->SetBinLabel(i, s);
      hnormVal->GetXaxis()->SetBinLabel(i, s);
      i++;
    }

    // fill the plots
    for( const auto& c : handler ) {
      TString     region  = c.name();
      int         binx    = hnormStatus->GetXaxis()->FindBin(region);
      const auto& samples = c.samples();
      float       sumNom  = 0;
      float       sumSyst = 0;
      for( const auto& spair : samples ) {
        const SampleInCategory& sic  = spair.second;
        TString                 name = spair.first->name();
        int                     biny = hnormVal->GetYaxis()->FindBin(name);
        SysKey                  key  = std::make_pair(SysType::norm, sys);
        hnormStatus->SetBinContent(binx, biny, sic.getSystStatus(key));
        hnormVal->SetBinContent(binx, biny, sic.getMeanNormEffect(key) * 100);

        sumNom += sic.integral();
        sumSyst += sic.integral() * sic.getMeanNormEffect(key);
      }
      hnormVal->SetBinContent(binx, hnormVal->GetYaxis()->FindBin("All"), (sumSyst / sumNom) * 100);
    }

    std::set<TH2*> h2sys;
    h2sys.insert(hnormStatus);
    h2sys.insert(hnormVal);

    // TStyle *style = new TStyle();
    Int_t   palette[6] = {kWhite, kYellow, kOrange - 3, kOrange + 10, kRed + 1, kGreen + 2}; // color palette
    TString histoName, label;
    bool    canBePrinted = true;

    TCanvas can("can", "can", 800, 600);
    can.SetMargin(0.1, 0.15, 0.3, 0.1);
    can.SetGridx();

    for( auto& h : h2sys ) {

      // Style
      h->SetStats(kFALSE);
      h->GetXaxis()->SetLabelSize(0.025);
      h->GetXaxis()->SetTickLength(0);
      h->GetXaxis()->LabelsOption("v");

      h->GetYaxis()->SetLabelSize(0.03);
      h->GetYaxis()->SetTickLength(0);

      // rename regions:
      TString anaType = std::getenv("ANALYSISTYPE");
      if( anaType == "boostedVHbbRun2" ) {
        for( int bin = 1; bin < h->GetXaxis()->GetNbins() + 1; ++bin ) {
          label = h->GetXaxis()->GetBinLabel(bin);
          label.ReplaceAll("Region_BMin400_incFat1_Fat1_incJet1_Y6051_DSR_T2_L2_distmBB_J0", "L2_SR_400ptv");
          label.ReplaceAll("Region_distmBB_J0_L2_T2_DSR_Y6051_incJet1_Fat1_incFat1_BMin250_BMax400",
                           "L2_SR_250_400ptv");
          label.ReplaceAll("Region_BMin400_incFat1_Fat1_Y6051_DSRnoaddbjetsr_T2_L0_distmBB_J0", "L0_HPSR_400ptv");
          label.ReplaceAll("Region_BMin400_incFat1_Fat1_Y6051_DSRnoaddbjetsr_T2_L1_distmBB_J0", "L1_HPSR_400ptv");
          label.ReplaceAll("Region_BMax400_BMin250_incFat1_Fat1_Y6051_DSRnoaddbjetsr_T2_L0_distmBB_J0",
                           "L0_HPSR_250_400ptv");
          label.ReplaceAll("Region_BMax400_BMin250_incFat1_Fat1_Y6051_DSRnoaddbjetsr_T2_L1_distmBB_J0",
                           "L1_HPSR_250_400ptv");
          label.ReplaceAll("Region_BMin400_incFat1_Fat1_incJet1_Y6051_DSRnoaddbjetsr_T2_L0_distmBB_J1",
                           "L0_LPSR_400ptv");
          label.ReplaceAll("Region_BMin400_incFat1_Fat1_incJet1_Y6051_DSRnoaddbjetsr_T2_L1_distmBB_J1",
                           "L1_LPSR_400ptv");
          label.ReplaceAll("Region_BMin400_incFat1_Fat1_incJet1_Y6051_DSRtopaddbjetcr_T2_L1_distmBB_J0",
                           "L1_CR_400ptv");
          label.ReplaceAll("Region_BMin400_incFat1_Fat1_incJet1_Y6051_DSRtopaddbjetcr_T2_L0_distmBB_J0",
                           "L0_CR_400ptv");
          label.ReplaceAll("Region_distmBB_J0_L1_T2_DSRtopaddbjetcr_Y6051_incJet1_Fat1_incFat1_BMin250_BMax400",
                           "L1_CR_250_400ptv");
          label.ReplaceAll("Region_distmBB_J0_L0_T2_DSRtopaddbjetcr_Y6051_incJet1_Fat1_incFat1_BMin250_BMax400",
                           "L0_CR_250_400ptv");
          label.ReplaceAll("Region_distmBB_J1_L0_T2_DSRnoaddbjetsr_Y6051_incJet1_Fat1_incFat1_BMin250_BMax400",
                           "L0_LPSR_250_400ptv");
          label.ReplaceAll("Region_distmBB_J1_L1_T2_DSRnoaddbjetsr_Y6051_incJet1_Fat1_incFat1_BMin250_BMax400",
                           "L1_LPSR_250_400ptv");

          h->GetXaxis()->SetBinLabel(bin, label);
        }
      }

      // We split the 2D in Btag,JES and rest for make them easier to read

      histoName = h->GetName();

      // We apply special palette in Status plots.
      if( histoName.Contains("Status") ) {
        gStyle->SetPalette(6, palette);
      } else {
        gStyle->SetPalette(1);
      }

      if( histoName.Contains("normVal") ) {
        h->Draw("colztext");
      } else {
        h->Draw("colz");
      }
      // We make sure that the TH2F has something to plot. Some regions make TH2* come empty after splitting them.
      canBePrinted = true;
      if( h->GetXaxis()->GetNbins() == 0 ) {
        canBePrinted = false;
      }
      if( canBePrinted ) {
        can.Print(outconfig->plotDir + "/systs/" + sys + "_" + h->GetName() + "." + m_format);
        if( m_createAllRootFiles )
          can.SaveAs(outconfig->plotDir + "/systs/" + sys + "_" + h->GetName() + ".root");

        if( histoName.Contains("normVal") ) {
          hnormValFile->cd();
          h->Write(sys + histoName);
        }
      }
      delete h;
    }
  }

  // then shape systematics
  for( auto& sys : shapeSysts ) {
    // prepare the plots
    TH2I* hshapeStatus = new TH2I("shapeStatus", Form("shapeStatus: %s", sys.Data()), regions.size(), 0, regions.size(),
                                  names.size(), 0, names.size());
    TH2D* hsmoothChi2Up = new TH2D("smoothChi2Up", ("#chi^{2}_{/NDF}(smooth vs. initial) " + sys).Data(),
                                   regions.size(), 0, regions.size(), names.size(), 0, names.size());
    TH2D* hsmoothChi2Do = new TH2D("smoothChi2Do", ("#chi^{2}_{/NDF}(smooth vs. initial) " + sys).Data(),
                                   regions.size(), 0, regions.size(), names.size(), 0, names.size());

    hshapeStatus->SetMaximum(6);

    std::vector<TH2*> histos;
    histos.push_back(hshapeStatus);
    histos.push_back(hsmoothChi2Up);
    histos.push_back(hsmoothChi2Do);

    int i = 1;
    for( auto& s : names ) {
      for( TH2* const histo : histos ) {
        histo->GetYaxis()->SetBinLabel(i, s);
      }
      i++;
    }
    i = 1;
    for( auto& s : regions ) {
      for( TH2* const histo : histos ) {
        histo->GetXaxis()->SetBinLabel(i, s);
      }
      i++;
    }

    // fill the plots
    for( const auto& c : handler ) {
      TString     region  = c.name();
      int         binx    = hshapeStatus->GetXaxis()->FindBin(region);
      const auto& samples = c.samples();
      for( const auto& spair : samples ) {
        const SampleInCategory& sic  = spair.second;
        TString                 name = spair.first->name();
        int                     biny = hshapeStatus->GetYaxis()->FindBin(name);
        SysKey                  key  = std::make_pair(SysType::shape, sys);
        hshapeStatus->SetBinContent(binx, biny, sic.getSystStatus(key));

        const double testUp = sic.getChi2SmoothTest(key, Systematic::Side::up);
        const double testDo = sic.getChi2SmoothTest(key, Systematic::Side::down);
        if( testUp >= 0. )
          hsmoothChi2Up->SetBinContent(binx, biny, testUp);
        if( testDo >= 0. )
          hsmoothChi2Do->SetBinContent(binx, biny, testDo);
      }
    }

    if( hsmoothChi2Up->GetMaximum() < 1. )
      hsmoothChi2Up->SetMaximum(1.);
    if( hsmoothChi2Do->GetMaximum() < 1. )
      hsmoothChi2Do->SetMaximum(1.);
    if( hsmoothChi2Up->GetMaximum() > 4. )
      hsmoothChi2Up->SetMaximum(4.);
    if( hsmoothChi2Do->GetMaximum() > 4. )
      hsmoothChi2Do->SetMaximum(4.);

    // TStyle *style = new TStyle();
    Int_t   palette[6] = {kWhite, kYellow, kOrange - 3, kOrange + 10, kRed + 1, kGreen + 2}; // color palette
    TString histoName, label;
    bool    canBePrinted = true;

    TCanvas can("can", "can", 800, 600);
    can.SetMargin(0.1, 0.15, 0.3, 0.1);
    can.SetGridx();

    for( TH1* const h : histos ) {
      // Style
      h->SetStats(kFALSE);
      h->GetXaxis()->SetLabelSize(0.025);
      h->GetXaxis()->SetTickLength(0);
      h->GetXaxis()->LabelsOption("v");

      h->GetYaxis()->SetLabelSize(0.03);
      h->GetYaxis()->SetTickLength(0);

      // rename regions:
      TString anaType = std::getenv("ANALYSISTYPE");
      if( anaType == "boostedVHbbRun2" ) {

        for( int bin = 1; bin < h->GetXaxis()->GetNbins() + 1; ++bin ) {
          label = h->GetXaxis()->GetBinLabel(bin);
          label.ReplaceAll("Region_BMin400_incFat1_Fat1_incJet1_Y6051_DSR_T2_L2_distmBB_J0", "L2_SR_400ptv");
          label.ReplaceAll("Region_distmBB_J0_L2_T2_DSR_Y6051_incJet1_Fat1_incFat1_BMin250_BMax400",
                           "L2_SR_250_400ptv");
          label.ReplaceAll("Region_BMin400_incFat1_Fat1_Y6051_DSRnoaddbjetsr_T2_L0_distmBB_J0", "L0_HPSR_400ptv");
          label.ReplaceAll("Region_BMin400_incFat1_Fat1_Y6051_DSRnoaddbjetsr_T2_L1_distmBB_J0", "L1_HPSR_400ptv");
          label.ReplaceAll("Region_BMax400_BMin250_incFat1_Fat1_Y6051_DSRnoaddbjetsr_T2_L0_distmBB_J0",
                           "L0_HPSR_250_400ptv");
          label.ReplaceAll("Region_BMax400_BMin250_incFat1_Fat1_Y6051_DSRnoaddbjetsr_T2_L1_distmBB_J0",
                           "L1_HPSR_250_400ptv");
          label.ReplaceAll("Region_BMin400_incFat1_Fat1_incJet1_Y6051_DSRnoaddbjetsr_T2_L0_distmBB_J1",
                           "L0_LPSR_400ptv");
          label.ReplaceAll("Region_BMin400_incFat1_Fat1_incJet1_Y6051_DSRnoaddbjetsr_T2_L1_distmBB_J1",
                           "L1_LPSR_400ptv");
          label.ReplaceAll("Region_BMin400_incFat1_Fat1_incJet1_Y6051_DSRtopaddbjetcr_T2_L1_distmBB_J0",
                           "L1_CR_400ptv");
          label.ReplaceAll("Region_BMin400_incFat1_Fat1_incJet1_Y6051_DSRtopaddbjetcr_T2_L0_distmBB_J0",
                           "L0_CR_400ptv");
          label.ReplaceAll("Region_distmBB_J0_L1_T2_DSRtopaddbjetcr_Y6051_incJet1_Fat1_incFat1_BMin250_BMax400",
                           "L1_CR_250_400ptv");
          label.ReplaceAll("Region_distmBB_J0_L0_T2_DSRtopaddbjetcr_Y6051_incJet1_Fat1_incFat1_BMin250_BMax400",
                           "L0_CR_250_400ptv");
          label.ReplaceAll("Region_distmBB_J1_L0_T2_DSRnoaddbjetsr_Y6051_incJet1_Fat1_incFat1_BMin250_BMax400",
                           "L0_LPSR_250_400ptv");
          label.ReplaceAll("Region_distmBB_J1_L1_T2_DSRnoaddbjetsr_Y6051_incJet1_Fat1_incFat1_BMin250_BMax400",
                           "L1_LPSR_250_400ptv");

          h->GetXaxis()->SetBinLabel(bin, label);
        }
      }

      // We split the 2D in Btag,JES and rest for make them easier to read

      histoName = h->GetName();

      // We apply special palette in Status plots.
      if( histoName.Contains("Status") ) {
        gStyle->SetPalette(6, palette);
      } else {
        gStyle->SetPalette(1);
      }

      h->Draw("colz");
      // We make sure that the TH2F has something to plot. Some regions make TH2* come empty after splitting them.
      canBePrinted = h->GetXaxis()->GetNbins() > 0;
      if( canBePrinted ) {
        can.Print(outconfig->plotDir + "/systs/" + sys + "_" + h->GetName() + "." + m_format);
        if( m_createAllRootFiles )
          can.SaveAs(outconfig->plotDir + "/systs/" + sys + "_" + h->GetName() + ".root");
      }
      delete h;
    }
  }

  hnormValFile->Close();
  delete hnormValFile;
}
