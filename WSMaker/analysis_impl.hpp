#ifndef analysis_impl_hpp
#define analysis_impl_hpp

#include <TString.h>

#include "analysis.hpp"
#include "postprocessing.hpp"

struct PropertiesSet;

// Factory: builds the necessary bits, but gives ownership to the actual users

/**
 * @brief Generic implementation of the interface of @c Analysis
 *
 * This implementation is supposed to be sufficient for all cases,
 * but another subclass of @c Analysis could be created if needed.
 *
 * @see Analysis for a description of the functions (not repeated here)
 * @see AnalysisHandler for usage of this class
 */
template <typename RegParser, typename InputH, typename SysBuilder, typename SampBuilder, typename BinTool,
          typename PostProcTool = PostProcessingTool>
class Analysis_Impl : public Analysis {
 public:
  Analysis_Impl() : Analysis() {}
  virtual ~Analysis_Impl() = default;

  virtual std::unique_ptr<SystematicListsBuilder>
  systListsBuilder(const Configuration& conf, std::vector<std::pair<Systematic, SysConfig>>& userSysts,
                   std::vector<std::pair<Systematic, SysConfig>>& pois, std::vector<Systematic32>& r32ratios,
                   std::unordered_map<TString, SysConfig>& histoSysts,
                   std::unordered_map<TString, TString>& renameHistoSysts, std::vector<TString>& constNormFacts,
                   std::vector<SysConfig>& MCStatSysts)
  {
    return std::make_unique<SysBuilder>(conf, userSysts, pois, r32ratios, histoSysts, renameHistoSysts, constNormFacts,
                                        MCStatSysts);
  }

  virtual std::unique_ptr<InputsHandler> inputsHandler(const Configuration& conf, const PropertiesSet& pset)
  {
    return std::make_unique<InputH>(conf, pset);
  }

  virtual std::unique_ptr<RegionNamesParser> regionNamesParser() { return std::make_unique<RegParser>(); }

  virtual std::unique_ptr<SamplesBuilder> samplesBuilder(const Configuration&                            conf,
                                                         std::unordered_map<TString, Sample>&            samples,
                                                         std::unordered_map<TString, std::set<TString>>& keywords,
                                                         std::map<Sample*, std::vector<Sample*>>&        samplesToMerge)
  {
    return std::make_unique<SampBuilder>(conf, samples, keywords, samplesToMerge);
  }

  virtual void createBinningTool(const Configuration& conf) { BinTool::createInstance(conf); }

  virtual void createPostProcessingTool(const Configuration& conf) { PostProcTool::createInstance(conf); }
};

#endif
