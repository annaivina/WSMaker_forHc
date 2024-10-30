#include "systematichandler.hpp"

#include <algorithm>
#include <cstdlib>
#include <functional>
#include <iostream>
#include <iterator>
#include <set>
#include <utility>
//
#include <TH1.h>
#include <TString.h>

#include "analysis.hpp"
#include "analysishandler.hpp"
#include "category.hpp"
#include "finder.hpp"
#include "properties.hpp"
#include "sample.hpp"
#include "sampleincategory.hpp"
#include "systematic.hpp"
#include "systematiclistsbuilder.hpp"

SystematicHandler::SystematicHandler(const Configuration& conf) :
    m_config(conf),
    m_userSysts(),
    m_pois(),
    m_32ratios(),
    m_histoSysts(),
    m_renameHistoSysts(),
    m_constNormFacts(),
    m_MCStatSysts(),
    m_systListsBuilder(AnalysisHandler::analysis().systListsBuilder(
        conf, m_userSysts, m_pois, m_32ratios, m_histoSysts, m_renameHistoSysts, m_constNormFacts, m_MCStatSysts))
{}

void SystematicHandler::listAllUserSystematics(bool useFltNorms)
{
  m_systListsBuilder->listAllUserSystematics(useFltNorms);
}

void SystematicHandler::listAllHistoSystematics()
{
  m_systListsBuilder->listAllHistoSystematics();
  m_systListsBuilder->fillHistoSystsRenaming();
}

bool SystematicHandler::match(const SampleInCategory& s, const SysConfig& sys)
{
  return (match(s.sample(), sys) && match(s.category(), sys));
}

bool SystematicHandler::match(const Sample& s, const SysConfig& sys)
{
  if( sys.sampleNames.empty() )
    return true;
  return std::any_of(std::begin(sys.sampleNames), std::end(sys.sampleNames),
                     [&s](const TString& name) { return s.hasKW(name); });
}

bool SystematicHandler::match(const Category& c, const SysConfig& sys)
{

  if( sys.categories.empty() && sys.cplxCategories.empty() )
    return true;

  bool match = std::any_of(std::begin(sys.categories), std::end(sys.categories),
                           [&c](const PropertiesSet& pset) { return c.match(pset); });

  bool cplxMatch = std::any_of(std::begin(sys.cplxCategories), std::end(sys.cplxCategories),
                               [&c](const ComplexFunctions::CategoryFunction func) { return func(c.properties()); });

  return match || cplxMatch;
}

std::pair<TString, const SysConfig&> SystematicHandler::getHistoSysConfig(const TString& name) const
{
  TString    newName(name);
  const auto rename = m_renameHistoSysts.find(name);
  if( rename != m_renameHistoSysts.end() ) {
    // TODO add logging in that case, to report to analyses to change their names
    newName = rename->second;
  }
  if( !m_histoSysts.count(newName) ) {
    std::cout << "ERROR:  SystematicHandler::getHistoSysConfig" << std::endl;
    std::cout << "No configuration defined for systematic " << name << std::endl;
    std::cout << "Please define a configuration for it !" << std::endl;
    throw;
  }
  return std::make_pair(newName, std::cref(m_histoSysts.at(newName)));
}

bool SystematicHandler::hasHistoSysConfig(const TString& name) const
{
  if( m_histoSysts.count(name) ) {
    return true;
  }
  const auto rename = m_renameHistoSysts.find(name);
  if( rename != m_renameHistoSysts.end() && m_histoSysts.count(rename->second) ) {
    return true;
  }
  return false;
}

void SystematicHandler::applyRatioSys(const TString& name, float size, SampleInCategory& sic1, SampleInCategory& sic2,
                                      float weight1, float weight2)
{
  // simple case is to preserve the sum of the two categories
  if( weight1 <= 0 ) {
    weight1 = sic1.getNomHist()->Integral();
  }
  if( weight2 <= 0 ) {
    weight2 = sic2.getNomHist()->Integral();
  }
  // well-defined case
  if( weight2 > 0 ) {
    float r    = weight1 / weight2;
    float err1 = size / (1 + r + r * size);
    float err2 = -r * err1;
    sic1.addSyst(Systematic(name, 1 - err1, 1 + err1));
    sic2.addSyst(Systematic(name, 1 - err2, 1 + err2));
  }
  // then just put a syst on the first
  else {
    sic1.addSyst(Systematic(name, 1 - size, 1 + size));
  }
}

void SystematicHandler::decorrSysForCategories(const TString& name, const std::vector<Properties::Property>& props,
                                               bool replace)
{
  // user systs
  for( auto hsys = m_userSysts.begin(); hsys != m_userSysts.end(); hsys++ ) {
    std::cout << "#" << hsys->first.name.Data() << ";" << std::endl;
    if( hsys->first.name == name ) {
      std::cout << "INFO: Found and decorrelating: " << name << std::endl;
      if( replace ) {
        hsys->second.decorrelations.clear();
        hsys->second.cplxDecorrelations.clear();
        hsys->second.decorrelations = props;
      } else {
        for( auto& prop : props )
          hsys->second.decorrelations.push_back(prop);
      }
    }
  }
  // histo systs
  for( auto hsys = m_histoSysts.begin(); hsys != m_histoSysts.end(); hsys++ ) {
    std::cout << "#" << hsys->first.Data() << ";" << std::endl;
    if( hsys->first == name ) {
      std::cout << "INFO: Found and decorrelating: " << name << std::endl;
      if( replace ) {
        hsys->second.decorrelations.clear();
        hsys->second.cplxDecorrelations.clear();
        hsys->second.decorrelations = props;
      } else {
        for( auto& prop : props )
          hsys->second.decorrelations.push_back(prop);
      }
    }
  }
}

void SystematicHandler::decorrSysForAllCategories(const TString& name)
{
  decorrSysForCategories(name, {Property::nLep, Property::nJet, Property::nTag, Property::tagType, Property::bin});
}

void SystematicHandler::ComputeNormalizationFactors()
{

  // loop over histSysts
  for( auto hsys = m_histoSysts.begin(); hsys != m_histoSysts.end(); hsys++ ) {
    TString    sysname = hsys->first;
    SysConfig& conf    = hsys->second;

    // check if normalizeRegionsConfig is not empty
    if( conf.normalizeRegionsConfig.size() == 0 ) {
      continue;
    }

    // loop over normalizeRegionsConfig
    for( auto& snrc : conf.normalizeRegionsConfig ) {

      std::unordered_map<TString, NormIntegrals> normMap;

      // first, get the list of real samples
      std::set<Sample*> samples;
      for( auto& s : snrc.sampleNames ) {
        auto& realSamples = SampleIndex::findAll(s);
        // fill samples with realSamples
        samples.insert(realSamples.begin(), realSamples.end());
      }

      // loop over the reference regions. A bit tedious (2 for loops) because it's a vector<PSet>,
      // where each PSet may refer to several regions
      // if refcategories is empty, consider all categories based on the decorrelation tag
      std::set<Category*> refCateg;
      if( snrc.referenceCategories.size() != 0 || snrc.cplxReferenceCategories.size() != 0 ) {
        refCateg                         = CategoryIndex::findAll(snrc.referenceCategories);
        std::set<Category*> cplxRefCateg = CategoryIndex::findAll(snrc.cplxReferenceCategories);
        refCateg.insert(cplxRefCateg.begin(), cplxRefCateg.end());
      } else
        refCateg = CategoryIndex::GetAllCategoriesSet();

      // Loop
      for( auto& cat : refCateg ) {
        // in each region, get the normalisation of the samples
        for( auto& s : samples ) {
          NormIntegrals vals = GetIntegrals(*s, *cat, sysname);
          // store that in the map, with the correct decorrelation tag
          TString tag  = snrc.getDecorrelationTag(cat->properties(), *s);
          normMap[tag] = normMap[tag] + vals;
        }
      }

      std::set<Category*> appCateg;
      if( snrc.applicationCategories.size() != 0 || snrc.cplxApplicationCategories.size() != 0 ) {
        appCateg                         = CategoryIndex::findAll(snrc.applicationCategories);
        std::set<Category*> cplxAppCateg = CategoryIndex::findAll(snrc.cplxApplicationCategories);
        appCateg.insert(cplxAppCateg.begin(), cplxAppCateg.end());
      } else
        appCateg = CategoryIndex::GetAllCategoriesSet();

      // Now the map is filled. We just have to fill normalizeRegionsFactors for the affected categories
      // same kind of 2 loops...
      // std::cout <<"INFO:: Now filling the normalizeRegionsFactors for sys " <<sysname <<std::endl;
      for( auto& cat : appCateg ) {
        auto& sicMap = cat->samples();
        // in each region, loop over the samples
        for( auto& s : samples ) {
          if( sicMap.find(s) == sicMap.end() ) { // eg. STXS bins for fits to single lep channels are not always defined
            std::cout << "WARNING:: This sample is in SysNormRegionConfig but NOT in the inputs. Please check "
                         "SysNormRegionConfig for "
                      << s->name() << std::endl;
            std::cout << "NO renormalization factor will be added for this sample. Skipping" << std::endl;
            continue;
          }

          // get the integrals from the reference regions of the correct categorisation (decorrelations)
          TString tag = snrc.getDecorrelationTag(cat->properties(), *s);

          if( normMap.count(tag) == 0 ) { // just check if the region we are trying to normalize to does exist in the
                                          // fit
            std::cout << "ERROR:: try to normalize sample " << s->name() << " and tag " << tag
                      << " with an unknown region "
                      << " SysNormRegionConfig is misconfigured for sys " << sysname << std::endl;
            std::cout << "ABORTING::Please fix it. " << std::endl;
            exit(0);
          }

          NormIntegrals& ni = normMap.at(snrc.getDecorrelationTag(cat->properties(), *s));

          // and Fill:
          // check that the sic does not already exist in normalizeRegionsFactors
          // that means that the user has put conflicting requests for normalization
          SampleInCategory& sic = sicMap.at(s);
          auto              pos = conf.normalizeRegionsFactors.find(&sic);
          //// and the program shoudl abort in that case to tell the user to fix his/her definitions
          if( pos != conf.normalizeRegionsFactors.end() ) {
            std::cout << "ERROR:: the normalize method for region " << sic.name() << "is misconfigured" << std::endl;
            std::cout << "ABORTING::Please fix it. " << std::endl;
            exit(0);
          }
          //// TO DO: maybe one should store nom/up and nom/down instead ?
          if( ni.nom != 0 ) {
            conf.normalizeRegionsFactors[&sic] = std::make_pair(ni.up / ni.nom, ni.down / ni.nom);
          }
        }
      }
    }
  }
}

NormIntegrals SystematicHandler::GetIntegrals(Sample& sample, Category& cat, TString sysname)
{

  TString fullsysname = sysname;

  // retrieve nominal histogram
  TH1* nom = cat.getHist(sample);

  if( nom == nullptr ) {
    std::cout << "WARNING: Nominal histogram: " << Form("%s", sysname.Data()) << " does not exist, assuming zero yield."
              << std::endl;
    return {0., 0., 0.};
  }

  // up and down integrals
  float int_nom = nom->Integral(-1, -1);
  float int_up  = 0.;
  float int_do  = 0.;

  // retrieve up/down type histogram
  TH1* tmp_up = cat.getHist(sample, Form("%s__1up", sysname.Data()));
  TH1* tmp_do = cat.getHist(sample, Form("%s__1down", sysname.Data()));

  if( (tmp_up == nullptr) && (tmp_do == nullptr) ) {
    // look for renamed systematics
    std::cout << "INFO:: No up & down variations found for systs " << sysname << std::endl;
    auto reverseNameMap = Utils::reverseMap<TString, TString>(m_renameHistoSysts);

    if( reverseNameMap.find(sysname) != reverseNameMap.end() ) {
      fullsysname = reverseNameMap.at(sysname);
      std::cout << "INFO:: Match renamed Histogram. Now looking for : " << fullsysname << std::endl;
      tmp_up = cat.getHist(sample, Form("%s__1up", fullsysname.Data()));
      tmp_do = cat.getHist(sample, Form("%s__1down", fullsysname.Data()));
    }
  }

  // set up integrals
  int_up = (tmp_up == nullptr) ? 0. : tmp_up->Integral(-1, -1);
  if( int_up == int_nom ) {
    std::cout << "WARNING: No variations for histogram " << Form("%s__1up", fullsysname.Data())
              << " has been found. Setting zero yields." << std::endl;
  }

  // set down integrals
  int_do = (tmp_do == nullptr) ? 0. : tmp_do->Integral(-1, -1);
  if( int_do == int_nom ) {
    std::cout << "WARNING: No variations for histogram " << Form("%s__1down", fullsysname.Data())
              << " has been found. Setting zero yields." << std::endl;
  }

  NormIntegrals integrals(int_nom, int_up, int_do);

  return integrals;
}
