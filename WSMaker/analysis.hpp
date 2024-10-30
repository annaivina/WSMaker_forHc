#ifndef analysis_hpp
#define analysis_hpp

#include <map>
#include <memory>
#include <set>
#include <unordered_map>
#include <utility>
#include <vector>

#include "configuration.hpp"
#include "containerhelpers.hpp"
#include "postprocessing.hpp"
#include "sample.hpp"

class InputsHandler;
class RegionNamesParser;
class SamplesBuilder;
class SystematicListsBuilder;
class TString;
struct SysConfig;
struct Systematic32;
struct Systematic;
struct PropertiesSet;

// Factory: builds the necessary bits, but gives ownership to the actual users

/**
 * @brief Factory class to build all analysis-dependent subclasses
 *
 * All analysis-dependent "big" chunks of code now sit in a few classes that
 * should be derived.
 *
 * This pure virtual class holds the base interface to create instances of those
 * specialized classes.
 * The functions here are meant to be called by the analysis-agnostic classes
 * that are consumer of those analysis-specific bits, when they need it.
 *
 * @see Analysis_Imp for a generic (read: templated) implementation of this
 * interface.
 */
class Analysis {
 public:
  /**
   * @brief Standard default constructor
   */
  Analysis() = default;

  /// Empty destructor
  virtual ~Analysis() {}

  /**
   * @brief Builder of @c SystematicListsBuilder
   *
   * This is called in @c SystematicHandler
   *
   * @param conf Reference to the global configuration
   * @param userSysts Reference to storage of the user-defined systematics (norm systs and norm factors)
   * @param pois Reference to storage of the POIs
   * @param r32ratios Reference to storage of the 3-to-2 systematics
   * @param histoSysts Reference to storage of the hist-based systematics
   * @param renameHistoSysts Reference to storage for renaming rules of systematics
   * @param constNormFacts Reference to list of NormFactors that should be constant in the fit
   * @param MCStatSysts Reference to list of MC stat errors that are implemented with ShapeSys
   * @return Pointer to the built @c SystematicListsBuilder
   */
  virtual std::unique_ptr<SystematicListsBuilder>
  systListsBuilder(const Configuration& conf, std::vector<std::pair<Systematic, SysConfig>>& userSysts,
                   std::vector<std::pair<Systematic, SysConfig>>& pois, std::vector<Systematic32>& r32ratios,
                   std::unordered_map<TString, SysConfig>& histoSysts,
                   std::unordered_map<TString, TString>& renameHistoSysts, std::vector<TString>& constNormFacts,
                   std::vector<SysConfig>& MCStatSysts) = 0;

  /**
   * @brief Builder of @c InputsHandler
   *
   * This is called once per @c Category
   *
   * @param conf Reference to the global configuration
   * @param pset @c PropertiesSet describing the category for which to build the @c InputsHandler
   * @return Pointer to the built @c InputsHandler
   */
  virtual std::unique_ptr<InputsHandler> inputsHandler(const Configuration& conf, const PropertiesSet& pset) = 0;

  /**
   * @brief Builder of RegionNamesParser
   *
   * This is called in @c CategoryHandler
   *
   * @return Pointer to the built @c RegionNamesParser
   */
  virtual std::unique_ptr<RegionNamesParser> regionNamesParser() = 0;

  /**
   * @brief Builder of @c SamplesBuilder
   *
   * This is called in @c SampleHandler
   *
   * @param conf Reference to the global configuration
   * @param samples Reference to storage of the samples
   * @param keywords Reference to all defined keywords
   * @param samplesToMerge Reference to lists of samples to be merged
   * @return Pointer to the built @c SamplesBuilder
   */
  virtual std::unique_ptr<SamplesBuilder> samplesBuilder(const Configuration&                            conf,
                                                         std::unordered_map<TString, Sample>&            samples,
                                                         std::unordered_map<TString, std::set<TString>>& keywords,
                                                         std::map<Sample*, std::vector<Sample*>>& samplesToMerge) = 0;

  /**
   * @brief Builder of the @c BinningTool
   *
   * This is called directly in @c Engine.
   *
   * Choice has been made to keep the @c BinningTool a singleton, as it is used
   * independently in different places of the code. So this function only creates
   * the static instance, without returning it.
   *
   * @see BinningTool::getInstance to get a pointer to the created instance.
   *
   * @param conf Reference to the global configuration
   */
  virtual void createBinningTool(const Configuration& conf) = 0;

  /**
   * @brief Builder of the @c PostprocessingTool
   *
   * This is called directly in @c Engine.
   *
   * The PostProcessingTool allows to modify a workspace after it has been created.
   *
   * @see PostProcessingTool::getInstance to get a pointer to the created instance.
   *
   * @param conf Reference to the global configuration
   */
  virtual void createPostProcessingTool(const Configuration& conf) { PostProcessingTool::createInstance(conf); }
};

#endif
