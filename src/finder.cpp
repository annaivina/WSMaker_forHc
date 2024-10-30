#include "finder.hpp"

#include <algorithm>
#include <iostream>
#include <iterator>
#include <utility>

#include <TString.h>

#include "category.hpp"
#include "configuration.hpp"
#include "containerhelpers.hpp"
#include "properties.hpp"
#include "sample.hpp"
#include "systematic.hpp"

std::unordered_map<TString, std::set<Sample*>> SampleIndex::m_samples{};
std::map<SType, std::set<Sample*>>             SampleIndex::m_samplesByType{};

void SampleIndex::reset()
{
  m_samplesByType.clear();
  m_samples.clear();
}

void SampleIndex::feed(Sample* s, const std::set<TString>& kw)
{
  m_samplesByType[s->type()].insert(s);
  for( const auto& k : kw )
    m_samples[k].insert(s);
}

Sample* SampleIndex::find(const TString& k)
{
  const auto& res = findAll(k);
  if( res.size() != 1 ) {
    std::cout << "ERROR::SampleFinder::find:" << std::endl
              << "  Key " << k << " designates several samples." << std::endl
              << "  Consider using findAll instead." << std::endl;
    throw;
  }
  return *(res.begin());
}

Sample* SampleIndex::findOrNull(const TString& k)
{
  const auto& res = m_samples.find(k);
  if( res == m_samples.end() ) {
    return nullptr;
  }
  if( res->second.size() != 1 ) {
    return nullptr;
  }
  return *(res->second.begin());
}

const std::set<Sample*>& SampleIndex::findAll(const TString& k)
{
  if( Configuration::debug() ) {
    std::cout << "INFO::SampleIndex::findAll: Looking for sample" << k << " in list." << std::endl;
  }
  return m_samples.at(k); // throw if not found
}

std::unordered_map<TString, Category*> CategoryIndex::m_categories{};

void CategoryIndex::feed(Category* c) { m_categories.emplace(c->properties().getPropertiesTag(), c); }

Category* CategoryIndex::find(const PropertiesSet& pset)
{
  std::cout << "Looking for category with properties:" << std::endl << "Region" << pset.getPropertiesTag() << std::endl;
  return m_categories[pset.getPropertiesTag()];
}

std::set<Category*> CategoryIndex::findAll(const PropertiesSet& pset)
{
  std::set<Category*> result;
  for( const auto& p : m_categories ) {
    if( p.second->match(pset) ) {
      result.insert(p.second);
    }
  }
  return result;
}

std::set<Category*> CategoryIndex::findAll(std::vector<PropertiesSet>& pset)
{
  std::set<Category*> result;
  for( auto& p : pset )
    for( const auto& cat : m_categories ) {
      if( cat.second->match(p) ) {
        result.insert(cat.second);
      }
    }
  return result;
}

std::set<Category*> CategoryIndex::findAll(std::vector<ComplexFunctions::CategoryFunction>& cplxCategories)
{
  std::set<Category*> result;
  for( const auto& cat : m_categories ) {
    bool cplxMatch =
        std::any_of(std::begin(cplxCategories), std::end(cplxCategories),
                    [&cat](const ComplexFunctions::CategoryFunction func) { return func(cat.second->properties()); });
    if( cplxMatch ) {
      result.insert(cat.second);
    }
  }
  return result;
}

bool CategoryIndex::hasMatching(const PropertiesSet& pset)
{
  return std::any_of(m_categories.begin(), m_categories.end(),
                     [&pset](const auto& p) { return p.second->match(pset); });
}

std::set<Category*> CategoryIndex::GetAllCategoriesSet()
{
  std::set<Category*> fullset;

  for( const auto& cat : m_categories )
    fullset.insert(cat.second);

  return fullset;
}
