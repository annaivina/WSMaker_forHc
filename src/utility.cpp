#include "utility.hpp"

#include <cmath>
#include <iostream>
#include <sstream>
#include <vector>

#include <TH1.h>
#include <TObjArray.h>
#include <TObjString.h>
#include <TString.h>
namespace Utils {

  std::vector<TString> splitString(TString orig, const char separator)
  {
    // splits the original string at 'separator' and fills the list
    // 'splitV' with the primitive strings
    std::vector<TString> splitV;
    orig.ReplaceAll("\n", " ");
    orig.Remove(TString::kBoth, separator);
    while( orig.Length() > 0 ) {
      // TODO condition in while could be omitted by appending separator before loop
      if( !orig.Contains(separator) ) {
        splitV.push_back(orig);
        break;
      } else {
        int     pos    = orig.First(separator);
        TString toSave = orig(0, pos);
        splitV.push_back(toSave);
        orig.Remove(0, pos);
      }
      orig.Remove(TString::kLeading, separator);
    }
    return splitV;
  } // SplitString

  TString assemble(const std::vector<TString>& elems, char separator)
  {
    if( elems.size() == 1 ) {
      return elems.at(0);
    }

    TString retval;
    TString sep = "";
    for( auto cur : elems ) {
      retval += sep;
      retval += cur;
      sep = separator;
    }
    return retval;
  }

  TString ftos(float d)
  {
    std::stringstream s;
    s << d;
    return TString(s.str().c_str());
  }

  TString group(TObjArray* res, int i)
  {
    if( i >= res->GetEntriesFast() ) {
      return "";
    }
    return ((TObjString*)res->At(i))->GetString();
  }

  TH1* symmetrize(const TH1* up, const TH1* nominal)
  {
    TH1* down = (TH1*)(nominal->Clone(nominal->GetName() + TString("Sym")));
    down->Scale(2);
    down->Add(up, -1);
    // std::cout << "after Add " << down << " " << up << std::endl;
    for( int bin = 0; bin < up->GetNbinsX() + 2; ++bin ) {
      const double err = up->GetBinError(bin);
      down->SetBinError(bin, err);
    }
    return down;
  }

  void sumOfSquares(TH1*& summed, const TH1* src)
  {
    if( summed == nullptr ) {
      summed    = (TH1*)src->Clone();
      int nbins = summed->GetNbinsX();
      for( int bin = 0; bin <= nbins + 1; ++bin ) {
        double tmp = src->GetBinContent(bin);
        summed->SetBinContent(bin, tmp * tmp);
      }
    } else {
      int nbins = summed->GetNbinsX();
      for( int bin = 0; bin <= nbins + 1; ++bin ) {
        double sum = summed->GetBinContent(bin);
        double tmp = src->GetBinContent(bin);
        summed->SetBinContent(bin, sum + tmp * tmp);
      }
    }
  }

  void squareRootOfHist(TH1* hist)
  {
    if( hist ) {
      int nbins = hist->GetNbinsX();
      for( int bin = 0; bin <= nbins + 1; ++bin ) {
        double content = hist->GetBinContent(bin);
        hist->SetBinContent(bin, sqrt(content));
      }
    }
  }

  TH1* GetSystRatioForQuadrature(const std::vector<const TH1*>& v_nom, const std::vector<const TH1*>& v_syst)
  {

    TH1* sumNom  = nullptr;
    TH1* qsumSys = nullptr;

    int nhists = (int)v_nom.size();
    for( int ihist = 0; ihist < nhists; ++ihist ) {
      if( !sumNom && !qsumSys ) {
        sumNom = (TH1*)v_nom.at(ihist)->Clone("nom");
        sumOfSquares(qsumSys, (TH1*)v_syst.at(ihist)->Clone("sys"));
      } else {
        sumNom->Add(v_nom.at(ihist));
        sumOfSquares(qsumSys, v_syst.at(ihist));
      }
    }
    squareRootOfHist(qsumSys);
    if( sumNom && qsumSys ) {
      qsumSys->Divide(sumNom);
      delete sumNom;
    }
    return qsumSys;
  }

} // namespace Utils
