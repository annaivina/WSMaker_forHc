#include "samplehandler.hpp"

#include <iostream>
#include <map>
#include <memory>
#include <set>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

#include <TString.h>

#include "analysis.hpp"
#include "analysishandler.hpp"
#include "category.hpp"
#include "configuration.hpp"
#include "containerhelpers.hpp"
#include "finder.hpp"
#include "sample.hpp"
#include "sampleincategory.hpp"
#include "samplesbuilder.hpp"
#include "systematic.hpp"
#include "systematichandler.hpp"

SampleHandler::SampleHandler(const Configuration& conf) :
    m_config(conf),
    m_samples(),
    m_keywords(),
    m_samplesToMerge(),
    m_builder(AnalysisHandler::analysis().samplesBuilder(conf, m_samples, m_keywords, m_samplesToMerge))
{
  populate();
}

SampleHandler::~SampleHandler() {}

void SampleHandler::populate()
{
  // first, fill all the samples
  m_builder->declareSamples();

  // then fill keywords
  // Last of all, fill the index of samples. Keywords must be frozen at that point
  update();

  // some basic checks
  checkContent();

} // populate

void SampleHandler::fillKeywords()
{
  // Add keywords.

  m_builder->declareKeywords();

  // resolve possible indirections (keywords pointing to keywords, yay !)
  expandKeywords();

  // then, analysis-agnostic keywords
  std::map<SType, TString> typenames{{SType::None, "None"},
                                     {SType::Data, "Data"},
                                     {SType::DataDriven, "DataDriven"},
                                     {SType::Sig, "Sig"},
                                     {SType::Bkg, "Bkg"}};

  // Then some automatic filling of the keywords:
  for( const auto& spair : m_samples ) {
    const Sample& s = spair.second;
    m_keywords["All"].insert(s.name());
    // names and type names are keywords too
    m_keywords[s.name()].insert(s.name());
    m_keywords[typenames[s.type()]].insert(s.name());
    //// if there are subsamples, they should be keywords also... actually better not
    // for(const auto& ss : s.subsamples()) {
    // m_keywords[ss].insert(s.name());
    // }
    //  MC can be a nice shorthand
    if( s.type() == SType::Sig || s.type() == SType::Bkg ) {
      m_keywords["MC"].insert(s.name());
    }
  }

  // now do reverse filling of keywords in samples
  for( auto& spair : m_samples ) {
    Sample& sample = spair.second;
    for( const auto& kw : m_keywords ) {
      if( kw.second.count(sample.name()) > 0 ) {
        sample.addKW(kw.first);
      }
    }
  }
}

void SampleHandler::expandKeywords()
{
  // algorithm:
  // * go through each line
  // * basically we create a queue of lines to visit to resolve the indirections for this line
  // * if the values are not keywords (i.e not other lines in the map), then add it to the final result
  // * else, push the new line to visit in the queue
  // * except if it's a line we have already visited... cycle detection to avoid infinite recursion

  /*
  // Debug: print KW before expansion
  std::cout << "SampleHandler::DEBUG: Keywords prior to expansion\n";
  for(const auto& kw : m_keywords) {
    std::cout << kw.first << " :\n";
    for (const auto& sample : kw.second){
      std::cout << "  : " << sample.Data() << '\n';
    }
    std::cout << std::endl;
  }
  */

  for( auto& kv : m_keywords ) {
    std::set<TString> visited{};
    std::set<TString> to_visit{kv.first}; // use set instead of queue to avoid duplicate entries
    std::set<TString> final_vals{};

    while( to_visit.size() ) {
      const TString& study = *(to_visit.begin());
      visited.insert(study);
      const auto& pointees = m_keywords[study];
      for( const auto& p : pointees ) {
        if( !m_keywords.count(p) ) {
          // this value is not a keyword: just insert it
          final_vals.insert(p);
        } else {
          // it is a keyword...
          if( visited.count(p) ) {
            // ... that we have already seen... there is some recursion ongoing
            // just add it as a final value and forget about it
            final_vals.insert(p);
          } else {
            // ok, it's a genuine additional level of indirection. Add it to the queue
            to_visit.insert(p);
          }
        }
      }
      // ok, we have dealt with it.
      to_visit.erase(study);
    }

    // now replace the contents of the values by the final ones
    auto& vals = kv.second;
    vals.clear();
    vals.insert(final_vals.begin(), final_vals.end());
  }

  /*
  std::cout << "SampleHandler::DEBUG: Keywords after expansion\n";
  for(const auto& kw : m_keywords) {
    std::cout << kw.first << " :\n";
    for (const auto& sample : kw.second){
      std::cout << "  : " << sample.Data() << '\n';
    }
    std::cout << std::endl;
  }
  */
}

void SampleHandler::feedSampleIndex()
{
  SampleIndex::reset();
  for( auto& spair : m_samples ) {
    Sample& sample = spair.second;
    SampleIndex::feed(&sample, sample.keywords());
  }
}

void SampleHandler::update()
{
  fillKeywords();
  feedSampleIndex();
}

void SampleHandler::checkContent() const
{
  // Basic Check: all samples have different names
  std::unordered_set<TString> allSampleNames;
  for( const auto& spair : m_samples ) {
    const Sample&        s      = spair.second;
    std::vector<TString> sNames = s.subsamples();
    sNames.push_back(s.name());
    for( const auto& ss : sNames ) {
      if( allSampleNames.count(ss) == 0 ) {
        allSampleNames.insert(ss);
      } else {
        std::cerr << "SampleHandler::checkContent: Sample " << ss << " seems to have been added twice ! Abort..."
                  << std::endl;
        throw;
      }
    }
  }

  // Some printed stuff
  if( Configuration::debug() ) {
    std::cout << std::endl << "SampleHandler::populate:" << std::endl << std::endl;
    std::cout << "Considering " << m_samples.size() << " samples" << std::endl;
    for( const auto& spair : m_samples ) {
      const Sample& s = spair.second;
      std::cout << "\t" << s.name() << std::endl;
    }
    std::cout << std::endl;
  }

} // checkContent

void SampleHandler::finalizeNominal()
{
  // std::cout << "SampleHandler::finalizeNominal()" << std::endl;
  for( auto& spair : m_samples ) {
    Sample& s = spair.second;
    s.finalizeNominal();
  }
  // is there any other stuff to add ? (stats, logs...)
}

std::set<TString> SampleHandler::addUserSyst(const Systematic& sys, const SysConfig& conf)
{
  // now loop through samples to apply systematics only where needed
  std::set<TString> result;
  for( auto& spair : m_samples ) {
    Sample& s = spair.second;
    if( !SystematicHandler::match(s, conf) )
      continue;
    auto sysnames = s.addUserSyst(sys, conf);
    result.insert(sysnames.begin(), sysnames.end());
  }
  return result;
}

void SampleHandler::add32Syst(const Systematic32& sys32)
{
  for( auto& spair : m_samples ) {
    Sample& s = spair.second;
    if( !SystematicHandler::match(s, sys32.conf) )
      continue;
    s.add32Syst(sys32);
  }
}

void SampleHandler::addMCStatSyst(SysConfig& conf)
{
  for( auto& spair : m_samples ) {
    Sample& s = spair.second;
    if( !SystematicHandler::match(s, conf) )
      continue;
    s.addMCStatSyst(conf);
  }
}

void SampleHandler::finishMerging()
{
  for( auto& pair : m_samplesToMerge ) {
    for( auto s : pair.second ) {
      std::cout << "INFO::SampleHandler:finishMerging: sample " << s->name()
                << " has been merged and will now be deleted !" << std::endl;
      auto pos = m_samples.find(s->name());
      m_samples.erase(pos);
    }
  }

  // Finally, update keywords and Finder
  update();

  std::cout << "INFO::SampleHandler:finishMerging: Merge complete. Success !" << std::endl;
}

void SampleHandler::mergeSamplesInCategory(Category& cat)
{
  for( auto& pair : m_samplesToMerge ) {
    mergeSamplesInCategory(cat, *(pair.first), pair.second);
  }
}

void SampleHandler::mergeSamplesInCategory(Category& cat, Sample& target, const std::vector<Sample*>& samplesToMerge)
{
  auto& catSamples = cat.samples();
  // Find which samples this category has
  std::vector<SampleInCategory*> sicToMerge;
  for( auto s : samplesToMerge ) {
    const auto& pos = catSamples.find(s);
    if( pos != catSamples.end() ) {
      sicToMerge.push_back(&(pos->second));
    }
  }
  // sometimes there is no merging to do
  if( sicToMerge.empty() ) {
    return;
  }
  // create the SiC
  SampleInCategory sic(cat, target, sicToMerge);
  // feed the SiC into its Category and this new Sample
  auto sicpair = catSamples.emplace(&target, std::move(sic));
  // we have moved sic, so it is not accessible directly any longer
  target.categories().emplace(&cat, &(sicpair.first->second)); // add pointer to the SiC in Sample s
  // then remove the old SiC from this category
  for( auto s : samplesToMerge ) {
    const auto& pos = catSamples.find(s);
    if( pos != catSamples.end() ) {
      catSamples.erase(pos); // in principle, also deletes the sic
    }
  }
}

void SampleHandler::declareSamplesToMerge()
{
  // just delegate this
  m_builder->declareSamplesToMerge();
  // update keywords !
  update();
}
