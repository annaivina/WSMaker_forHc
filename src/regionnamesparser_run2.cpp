#include "regionnamesparser_run2.hpp"

#include <cstdlib>
#include <iostream>

#include <TPRegexp.h>
#include <TString.h>

#include "TObjArray.h"
#include "properties.hpp"
#include "utility.hpp"

RegionNamesParser_Run2::RegionNamesParser_Run2() :
    m_regionRegexp("^(\\d+)TeV(\\w+)?_(\\w+)_(\\w+)tag(\\w+)jet(\\w+taus)?_(\\d+)(_\\d+)?ptv(_\\w+)?_(\\w+)$"),
    m_tagRegexp("(\\d+)?([lmtxnba]+)?(p)?"),
    m_jetRegexp("((\\d+)(p)?fat)?(\\d+)(p)?"),
    m_tauRegexp("(\\d+)(p)?"),
    m_descrRegexp("(_([a-zA-Z0-9]+))+")
{}

std::pair<bool, PropertiesSet> RegionNamesParser_Run2::parseRegion(const TString& regConfig)
{
  PropertiesSet pset;
  // First parsing of the string
  TObjArray* res = m_regionRegexp.MatchS(regConfig, "", 0, 15);
  if( res->GetEntriesFast() == 0 ) { // no match
    std::cout << "ERROR: ParseRegions: region badly formatted " << regConfig << std::endl;
    throw;
  }

  TString cme = Utils::group(res, 1);
  if( cme == "13" ) {
    pset[Property::year] = 2015;
    TString mcprod       = Utils::group(res, 2);
    if( mcprod.Length() ) {
      if( mcprod == "mc16a" ) {
        pset[Property::year] = 2016;
      } else if( mcprod == "mc16d" ) {
        pset[Property::year] = 2017;
      } else if( mcprod == "mc16e" ) {
        pset[Property::year] = 2018;
      } else if( mcprod == "mc16ad" ) {
        pset[Property::year] = 4033;
      } else if( mcprod == "mc16ade" ) {
        pset[Property::year] = 6051;
      }
    }
  } else if( cme == "8" ) {
    pset[Property::year] = 2012;
  } else {
    pset[Property::year] = 2011;
  }

  TString channel = Utils::group(res, 3);
  // our config does make use of this category, so now get all its properties
  if( channel.Contains("Zero") )
    pset[Property::nLep] = 0;
  if( channel.Contains("One") )
    pset[Property::nLep] = 1;
  if( channel.Contains("Two") )
    pset[Property::nLep] = 2;
  if( channel.Contains("TauLH") ) {
    pset[Property::spec] = "TauLH";
    pset[Property::nLep] = 1;
    if( channel.Contains("LTT") )
      pset[Property::LTT] = 1;
    else
      pset[Property::LTT] = 0;
  }
  if( channel.Contains("TauHH") ) {
    pset[Property::spec] = "TauHH";
    pset[Property::nLep] = 0;
  }
  if( channel.Contains("MET") )
    pset[Property::spec] = "MET";
  if( channel.Contains("_Mu") )
    pset[Property::lepFlav] = 0;
  if( channel.Contains("_El") )
    pset[Property::lepFlav] = 1;
  if( channel.Contains("_MVA") )
    pset[Property::type] = 1;
  if( channel.Contains("_CUT") )
    pset[Property::type] = 0;

  TObjArray* res_tag = m_tagRegexp.MatchS(Utils::group(res, 4));
  if( res_tag->GetEntriesFast() == 0 ) { // no match
    std::cout << "ERROR: ParseRegions: tag block badly formatted " << Utils::group(res, 4) << std::endl;
    throw;
  }
  pset[Property::nTag] = atoi(Utils::group(res_tag, 1));
  TString tagType      = Utils::group(res_tag, 2);
  if( tagType.Length() ) {
    pset[Property::tagType]=tagType.Strip(TString::EStripType::kLeading, '_');
  }
  TString incTag = Utils::group(res_tag, 3);
  if( incTag.Length() ) {
    pset[Property::incTag] = 1;
  }

  TObjArray* res_jet = m_jetRegexp.MatchS(Utils::group(res, 5));
  if( res_jet->GetEntriesFast() == 0 ) { // no match
    std::cout << "ERROR: ParseRegions: jet block badly formatted " << Utils::group(res, 5) << std::endl;
    throw;
  }
  pset[Property::nJet] = atoi(Utils::group(res_jet, 4));
  TString incJet       = Utils::group(res_jet, 5);
  if( incJet.Length() ) {
    pset[Property::incJet] = 1;
  }
  TString nFatJet = Utils::group(res_jet, 1);
  if( nFatJet.Length() ) {
    pset[Property::nFatJet] = atoi(nFatJet);
  }
  TString incFat = Utils::group(res_jet, 2);
  if( incFat.Length() ) {
    pset[Property::incFat] = 1;
  }

  TObjArray* res_tau = m_tauRegexp.MatchS(Utils::group(res, 6)); //GDG
  TString nTaus = Utils::group(res_tau, 1);
  if (nTaus.Length()){
    pset[Property::ntau] = atoi(nTaus);
  }
  TString inctau = Utils::group(res_tau, 2);
  if( inctau.Length() ) {
    pset[Property::inctau] = 1;
  }
  

  pset[Property::binMin] = atoi(Utils::group(res, 7));
  TString ptvmax         = Utils::group(res, 8);
  if( ptvmax.Length() ) {
    pset[Property::binMax] = atoi(TString(ptvmax.Strip(TString::EStripType::kLeading, '_')));
  }

  TString descr         = Utils::group(res, 9);
  pset[Property::descr] = descr.Strip(TString::EStripType::kLeading, '_');

  pset[Property::dist] = Utils::group(res, 10);

  res->Delete();
  delete res;
  res_tag->Delete();
  delete res_tag;
  res_jet->Delete();
  delete res_jet;
  res_tau->Delete();
  delete res_tau;

  return {true, pset};
}
