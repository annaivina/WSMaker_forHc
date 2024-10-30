#include <iostream>
#include <memory>
#include <sstream>

#include <TArrow.h>
#include <TAxis.h>
#include <TCanvas.h>
#include <TFile.h>
#include <TGaxis.h>
#include <TH1.h>
#include <TH2.h>
#include <TLegend.h>
#include <TPad.h>
#include <TStyle.h>

void project(const TH1* histIn, const char* outName)
{
  std::unique_ptr<TCanvas> c1(new TCanvas());
  c1->cd();

  const TH2* hist = dynamic_cast<const TH2*>(histIn);
  if( !hist )
    return;

  std::string outDir(outName);
  outDir           = outDir.substr(0, outDir.rfind('/'));
  const int dirErr = system(("mkdir -p " + outDir).c_str());
  if( dirErr == -1 )
    return;

  const TAxis*         axVar   = hist->GetXaxis();
  const TAxis*         axAlpha = hist->GetYaxis();
  std::unique_ptr<TH1> nom(hist->ProjectionX("Nominal", axAlpha->FindBin(0.), axAlpha->FindBin(0.), "eo"));
  std::unique_ptr<TH1> up(hist->ProjectionX("Up", axAlpha->FindBin(1.), axAlpha->FindBin(1.), "eo"));
  std::unique_ptr<TH1> dow(hist->ProjectionX("Down", axAlpha->FindBin(-1.), axAlpha->FindBin(-1.), "eo"));
  nom->SetTitle("Nominal");
  nom->SetLineStyle(1);
  nom->SetLineColor(kBlue);
  nom->SetLineWidth(2);
  up->SetTitle("+1 #sigma");
  up->SetLineStyle(2);
  up->SetLineColor(kRed);
  dow->SetTitle("-1 #sigma");
  dow->SetLineStyle(2);
  dow->SetLineColor(kGreen);

  vector<double> mins;
  vector<double> maxs;
  for( auto hist : {nom.get(), up.get(), dow.get()} ) {
    if( !hist )
      continue;
    mins.push_back(hist->GetMinimum());
    maxs.push_back(hist->GetMaximum());
  }
  const double ymin = *std::min_element(mins.begin(), mins.end());
  const double ymax = *std::max_element(maxs.begin(), maxs.end());

  int maxX, maxY, maxZ;
  hist->GetMaximumBin(maxX, maxY, maxZ);
  const bool legendOnRight = maxX < axVar->GetNbins() / 2;

  const double xLow = axVar->GetXmin(), xHigh = axVar->GetXmax();
  double       gAxStart, gAxEnd;
  if( legendOnRight ) {
    gAxStart = (1 - 0.6) * xLow + 0.6 * xHigh;
    gAxEnd   = (1 - 0.9) * xLow + 0.9 * xHigh;
  } else {
    gAxStart = (1 - 0.1) * xLow + 0.1 * xHigh;
    gAxEnd   = (1 - 0.4) * xLow + 0.4 * xHigh;
  }
  const double            heightGAx = 0.6;
  const double            yGAx      = (1 - heightGAx) * ymin + heightGAx * ymax;
  const double            alphaLow = axAlpha->GetXmin(), alphaHigh = axAlpha->GetXmax();
  std::unique_ptr<TGaxis> gax(new TGaxis(gAxStart, yGAx, gAxEnd, yGAx, alphaLow, alphaHigh, 505, ""));
  gax->SetName("alpha");
  gax->SetTitle("#alpha");

  std::unique_ptr<TLine> line(new TLine(xLow, 0, xHigh, 0));

  std::unique_ptr<TH1> proj;
  for( int i = 0; i <= axAlpha->GetNbins(); ++i ) {

    std::unique_ptr<TLegend> leg(legendOnRight ? new TLegend(0.55, 0.7, 0.85, 0.9) : new TLegend(0.15, 0.7, 0.45, 0.9));

    TH1* result = hist->ProjectionX("proj", i, i, "eo");
    if( !proj )
      proj.reset(result);
    assert(proj.get() == result);
    proj->SetDirectory(0);
    proj->SetTitle(TString("Morphing Check ") + hist->GetName());
    proj->SetFillStyle(0);
    proj->SetLineColor(kBlack);
    proj->SetLineWidth(2);
    //      proj->GetXaxis()->SetTitle(hist->GetXaxis()->GetT);
    proj->GetYaxis()->SetRangeUser(ymin - 0.1 * (ymax - ymin), ymax + 0.2 * (ymax - ymin));
    proj->Draw("hist");
    leg->AddEntry(proj.get(), "Morphed", "l");

    nom->Draw("hist same");
    up->Draw("hist same");
    dow->Draw("hist same");
    leg->AddEntry(nom.get(), "Nominal", "l");
    leg->AddEntry(up.get(), "+1 #sigma", "l");
    leg->AddEntry(dow.get(), "-1 #sigma", "l");

    leg->SetBorderSize(0);
    leg->SetFillStyle(0);
    leg->Draw();

    gax->Draw();

    double x = gAxStart + (gAxEnd - gAxStart) * (axAlpha->GetBinCenter(i) - alphaLow) / (alphaHigh - alphaLow);
    std::unique_ptr<TArrow> arr(new TArrow(x, yGAx, x, yGAx * 1.05, 0.1, "|->"));
    arr->Draw("same");

    line->Draw();

    c1->Modified();
    c1->Update();

    c1->Print((outName + std::string("+20")).c_str());
  }

  //"Close" animated gif
  c1->Print((outName + std::string("++")).c_str());
}

void morphingProjection(TDirectory* dir, const char* outName, const char* histoName, const char* canvasName = nullptr)
{
  gStyle->SetOptStat(0);

  TCanvas* c    = nullptr;
  TObject* prim = nullptr;
  TH2*     hist = nullptr;
  if( canvasName && histoName ) {
    dir->GetObject(canvasName, c);
    prim = c->GetPrimitive(histoName);
    hist = dynamic_cast<TH2*>(prim);
  }
  if( !hist && histoName ) {
    dir->GetObject(histoName, hist);
  }

  if( hist ) {
    project(hist, outName);
  } else {
    std::cout << "Histogram '" << histoName << "' not found in directory " << dir->GetName() << ".";
    if( canvasName && !c )
      std::cout << " (Canvas " << canvasName << " not found.)";
    if( prim )
      std::cout << " " << prim->GetName() << " (" << prim->ClassName() << ") is not compatible with TH2.";
    std::cout << std::endl;
  }

  delete hist;
  delete prim;
  delete c;
}
