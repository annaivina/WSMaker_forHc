#ifndef __LINKDEF_H__
#define __LINKDEF_H__
#include <RooAbsData.h>
#include <RooAbsPdf.h>
#include <RooCurve.h>
#include <RooExpandedFitResult.h>
#include <RooProdPdf.h>
#include <RooRealVar.h>
#include <map>
#include <set>
#include <utility>
#include <vector>

#include <TGraph.h>

#include "plotUtils.hpp"
#include "roofitUtils.hpp"

#ifdef __CINT__

#pragma link off all globals;
#pragma link off all classes;
#pragma link off all functions;
#pragma link         C++ nestedclass;

#pragma link C++ class vector < TString> + ;
#pragma link C++ class map < TString, int> + ;
#pragma link C++ class set < TString> + ;
#pragma link C++ class pair < TString, int> + ;
#pragma link C++ class vector < pair < TString, int>> + ;
#pragma link C++ class vector < TGraph*> + ;
#pragma link C++ class vector < RooAbsPdf*> + ;
#pragma link C++ class vector < RooRealVar*> + ;
#pragma link C++ class vector < RooAbsData*> + ;
#pragma link C++ class vector < RooCurve*> + ;

#pragma link C++ namespace PU;
#pragma link C++ namespace RU;

#pragma link C++ class RooExpandedFitResult + ;

#endif
#endif
