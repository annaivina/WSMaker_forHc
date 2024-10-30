#ifndef systematic_hpp
#define systematic_hpp

#include <functional>
#include <memory>
#include <unordered_map>
#include <utility>
#include <vector>

#include <TString.h>

#include "properties.hpp"

class TH1;
class Sample;
class SampleInCategory;

/**
 * @brief Complex definition for selecting categories.
 *
 * Allows to use a function to decide whether a category is selected or not
 * with a certain @c PropertiesSet.
 *
 * Example: [](const PropertiesSet& p) {
 *             return p[Property::nFatJet] > 0;
 *          }
 *
 * This is more flexible than using @c PropertiesSet to specify the selected categories,
 * as arbitrary boolean operations can be used.
 * This structure is used both is SysConfig and SysNormRegionConfig
 */
struct ComplexFunctions {
  using CategoryFunction = std::function<bool(const PropertiesSet&)>;
};

/**
 * @file systematic.hpp
 * @brief Contains the two basic blocks for the incorporation of systematics
 *
 * Systematic is the description of 1 systematic (or floating norm) on 1 sample
 * in 1 category.
 *
 * SysConfig is the mechanism used to describe treatments that need to be applied on
 * systematics (smoothing...), as well as to decide the regions and samples of application,
 * and setup the decorrelations between the categories and samples.
 *
 * @todo A better structure could be the following:
 * - A namespace Sys. The enums of @c Systematic should be directly there. @c interpretSysName
 *   should be there too.
 * - So @c Systematic would be in that namespace and would have only the info directly used to
 *   describe a given syst
 * - The rest of the contents of the file should be in the namespace too, and their names
 *   simplified, e.g @c SysConfig -> @c Sys::Config
 *
 */

/**
 * @brief Structure to hold configuration for systematics that need to be normalized
 * to some other regions, example: SUSY-Like systematics or BDTr modeling systematics
 *
 * Describe SUSY-like approach: normHistoSys in HistFitter:
 * For each floating background define one (and one only) MAIN normalisation region
 * the most pure and with the highest stat.
 * In CR the detector systematics for that background are *SHAPEONLY*
 * In the rest of the regions the NP only affects as proper
 * extrapolation uncertainty: the normalization factor is corrected by sys_CReg/norm_CReg.

 * NB.  In everything that concerns this structure:
 * - an empty sampleNames means it applies to ALL samples,
 * - an empty referenceCategories means it normalizes to the sum of ALL categories,
 * - an empty applicationCategories means it applies the normalization to ALL categories
 */
struct SysNormRegionsConfig {

  /// which samples it should apply to
  std::vector<TString> sampleNames;

  /// where should the normalization be computed
  std::vector<PropertiesSet> referenceCategories;

  /// where should the normalization be applied
  std::vector<PropertiesSet> applicationCategories;

  /// where should the normalization be computed using complex functions to express the PropertiesSet
  std::vector<ComplexFunctions::CategoryFunction> cplxReferenceCategories;

  /// where should the normalization be applied using complex functions to express the PropertiesSet
  std::vector<ComplexFunctions::CategoryFunction> cplxApplicationCategories;

  /**
   * @brief Simple decorrelation rules for categories
   *
   * Here one can define simple rules like: I want this systematic to be decorrelated
   * in number of jets, number of leptons, and tag type
   *
   *     {nLep, nJet, tagType}
   *
   * The resulting tag will be e.g for all 0 lepton 3 jet ll tag region:
   *
   *     _L0_J3_TTypell
   *
   * This is very close to what we have in SysConfig.
   */
  std::vector<Property> decorrelations;

  /**
   * @brief More complex decorrelation rules for categories
   *
   * Sometime one needs something a bit more complex than the above simple decorrelation
   * schemes. In that case one must define the precise regions that should be on their own.
   *
   * They way to describe precisely the affected regions is through @c PropertiesSet
   *
   * An example is ttbar 3jet systematic, which is correlated in 0 and 1 lepton, but
   * decorrelated in 2 lepton.
   *
   *     { {nLep, 2} }
   *
   * Then all 0 and 1 lepton categories won't have any tag, while all 2 lepton categories
   * will have a _L2 tag
   * This is very close to what we have in SysConfig.
   */
  std::vector<PropertiesSet> cplxDecorrelations;

  /// decorrelation configs: if true decorrelate over sampleNames
  bool decorrSamples;

  /// Add some nice constructors, and ways to build it similarly to what we have for SysConfig

  /// @name Constructors
  /// @{

  /// Default copy constructor
  SysNormRegionsConfig(const SysNormRegionsConfig&) = default;

  /// Default move constructor
  SysNormRegionsConfig(SysNormRegionsConfig&&) = default;

  /// @name Constructors useful mostly for histo systs
  /// @{

  /// Full constructor
  SysNormRegionsConfig(std::vector<TString>&& s, std::vector<PropertiesSet>&& rcat, std::vector<PropertiesSet>&& acat,
                       std::vector<Property>&& d = {}, std::vector<PropertiesSet>&& cd = {});

  /// Full constructor for one single sample or keyword
  SysNormRegionsConfig(const TString& s, std::vector<PropertiesSet>&& rcat, std::vector<PropertiesSet>&& acat,
                       std::vector<Property>&& d = {}, std::vector<PropertiesSet>&& cd = {});

  /// shortcut for one single sample and one single reference normalization region
  SysNormRegionsConfig(const TString& s, PropertiesSet& rcat, std::vector<PropertiesSet>&& acat,
                       std::vector<Property>&& d = {}, std::vector<PropertiesSet>&& cd = {});

  /// Full constructors with complex CategoryFunctions
  SysNormRegionsConfig(std::vector<TString>&& s, const std::vector<ComplexFunctions::CategoryFunction>&& rcat,
                       const std::vector<ComplexFunctions::CategoryFunction>&& acat, std::vector<Property>&& d = {},
                       std::vector<PropertiesSet>&& cd = {});

  SysNormRegionsConfig(std::vector<TString>&& s, const std::vector<ComplexFunctions::CategoryFunction>& rcat,
                       const std::vector<ComplexFunctions::CategoryFunction>& acat, std::vector<Property>&& d = {},
                       std::vector<PropertiesSet>&& cd = {});

  SysNormRegionsConfig(const TString& s, const std::vector<ComplexFunctions::CategoryFunction>&& rcat,
                       const std::vector<ComplexFunctions::CategoryFunction>&& acat, std::vector<Property>&& d = {},
                       std::vector<PropertiesSet>&& cd = {});

  SysNormRegionsConfig(const TString& s, const std::vector<ComplexFunctions::CategoryFunction>& rcat,
                       const std::vector<ComplexFunctions::CategoryFunction>& acat, std::vector<Property>&& d = {},
                       std::vector<PropertiesSet>&& cd = {});

  SysNormRegionsConfig(std::vector<TString>&& s, const ComplexFunctions::CategoryFunction& rcat,
                       const ComplexFunctions::CategoryFunction& acat, std::vector<Property>&& d = {},
                       std::vector<PropertiesSet>&& cd = {});

  SysNormRegionsConfig(std::vector<TString>&& s, const ComplexFunctions::CategoryFunction&& rcat,
                       const ComplexFunctions::CategoryFunction&& acat, std::vector<Property>&& d = {},
                       std::vector<PropertiesSet>&& cd = {});
  /// @}

  /// @}

  // Decorrelation setters
  /**
   * @brief This @c SysNormRegionsConfig should decorrelate based on the samples
   * given by @ std::vector<TString> sampleNames;
   *
   * @param bool @ds: True: decorrelate samples, False merge samples. Default = false.
   */
  SysNormRegionsConfig& decorrelateSamples(bool ds);

  /**
   * @brief This @c SysNormRegionsConfig should decorrelate based on a given @c Property
   *
   * @param d The @c Property used for decorrelation
   */
  SysNormRegionsConfig& decorr(const Property& d);

  /**
   * @brief This @c SysNormRegionsConfig should decorrelate based on som @c Property
   *
   * @param d The Properties used for decorrelation
   */
  SysNormRegionsConfig& decorr(const std::vector<Property>& d);

  /**
   * @brief This @c SysNormRegionsConfig should decorrelate in specific regions
   *
   * @param cd PropertiesSet which characterize the regions
   */
  SysNormRegionsConfig& decorrIn(const PropertiesSet& cd);

  /**
   * @brief This @c SysNormRegionsConfig should decorrelate in specific regions
   *
   * @param cd List of PropertiesSet which characterize the regions
   */
  SysNormRegionsConfig& decorrIn(const std::vector<PropertiesSet>& cd);

  /** @brief Compute the decorrelation tag corresponding to @c pset and @c
   *
   * Very similar to getDecorrelationTag in SysConfig. Will be used in ComputeNormalizationFactors
   * to properly classify the regions / samples in the groups desired by the user, and compute correctly
   * the factors, then assign them to the correct regions / samples.
   *
   * Computation of the decorrelation tag of the @c SampleInCategory characterized by
   * @c pset and @c s, based on the rules defined in this @c SysConfig.
   *
   * See the description of the class members for the details about how the decorrelation
   * tags are built.
   * @param pset        A @c PropertiesSet typically coming from some @c Category
   * @param s A @c Sample
   * @return The decorrelation tag, that will have to be appended to a systematic name
   */
  TString getDecorrelationTag(const PropertiesSet& pset, const Sample& s) const;
};

/**
 * @brief Configuration of area of application and decorrelations for systematics
 *
 * This structure is heavily used when adding systematics in the workspaces.
 * Through a series of matching rules, it encodes the configuration of systematics:
 * - how to treat them (shape, norm...)
 * - if they should be smoothed
 * - where do they apply, and on what samples
 * - what regions should be decorrelated or grouped together
 * - what samples should be decorrelated or grouped together
 *
 * The decorrelations are translated into 'tags' appended to the systematics names,
 * so that in the end everything that should be grouped together has the same tag,
 * and things that are decorrelated have different tags.
 */
struct SysConfig {
  /// Types of treatment to be applied on hist systs: skip norm, shape, shapeonly
  enum class Treat { skip, norm, shape, shapeonly };

  /// @brief Type of smoothing to apply on histo systs.
  ///
  /// None, or potentially one among several
  /// algs. The enum just needs to be extended to accomodate additional algs.
  enum class Smooth {
    noSmooth,
    smoothRebinMonotonic,
    smoothRebinParabolic,
    smoothRatioUniformKernel,
    smoothDeltaUniformKernel,
    removeSameSignBins,
    smoothUserDefined
  };

  /// @brief Type of symmetrisation to apply on histo systs.
  ///
  /// noSym keeps the original variations as is
  /// symmetriseAverage if both up and down are present use +- average of up/down variations
  /// symmetriseOneSided defines one side as the opposite of the other. Use it for one-sided
  /// systematics (e.g JER)
  enum class Symmetrise { noSym, symmetriseAverage, symmetriseOneSided, symmetriseUserDefined };

  using DecorrFunction    = std::function<TString(const PropertiesSet&, const Sample&)>;
  using SmoothingFunction = std::function<Smooth(const PropertiesSet&, const Sample&)>;
  using SymFunction       = std::function<Symmetrise(const PropertiesSet&, const Sample&)>;

  /// Type of treatment to apply
  Treat treat;

  /// Type of smoothign to apply
  Smooth smooth;

  /// Type of smoothign to apply
  Symmetrise symmetrise;

  /// A factor by which to scale the histo syst
  float scaleFactor;

  /**
   * @brief Samples that the systematic applies on
   *
   * Both sample names and keywords as defined in @c SampleHandler can be used
   */
  std::vector<TString> sampleNames;

  /**
   * @brief Categories the systematic applies on
   *
   * The way to make the list of affected categories is to use a vector of
   * @c PropertiesSet, that are used asa matching rules.
   *
   * So a category is matched if its properties match at least one of the @c PropertiesSet
   * in this vector
   *
   * e.g if one defines @c categories with
   *
   *     { {nTag, 2}, { { {nLep, 2}, {nJet, 3} }, {} } }
   *
   * then all 2-tag categories will be used, as well as all 2 lepton 3 jet categories.
   *
   */
  std::vector<PropertiesSet> categories;

  /**
   * @brief More complex definitions for when to apply a systematic.
   *
   * Allows to use a function to decide whether a systematic should apply to a category
   * with a certain @c PropertiesSet.
   *
   * Example: [](const PropertiesSet& p) {
   *	         return p[Property::nFatJet] > 0;
   *          }
   *
   * This is more flexible than using @c PropertiesSet to specify the applicable categories,
   * as arbitrary boolean operations can be used.
   */
  std::vector<ComplexFunctions::CategoryFunction> cplxCategories;

  /**
   * @brief Simple decorrelation rules for categories
   *
   * Here one can define simple rules like: I want this systematic to be decorrelated
   * in number of jets, number of leptons, and tag type
   *
   *     {nLep, nJet, tagType}
   *
   * The resulting tag will be e.g for all 0 lepton 3 jet ll tag region:
   *
   *     _L0_J3_TTypell
   *
   */
  std::vector<Property> decorrelations;

  /**
   * @brief More complex decorrelation rules for categories
   *
   * Sometime one needs something a bit more complex than the above simple decorrelation
   * schemes. In that case one must define the precise regions that should be on their own.
   *
   * They way to describe precisely the affected regions is through @c PropertiesSet
   *
   * An example is ttbar 3jet systematic, which is correlated in 0 and 1 lepton, but
   * decorrelated in 2 lepton.
   *
   *     { {nLep, 2} }
   *
   * Then all 0 and 1 lepton categories won't have any tag, while all 2 lepton categories
   * will have a _L2 tag
   */
  std::vector<PropertiesSet> cplxDecorrelations;

  /**
   * @brief Simple decorrelation rules for samples
   *
   * This simply works through sample names or keywords as definde in @c SampleHandler.
   *
   * An example is SysJetFlavComp, which should be decorrelated based on sample type:
   *
   *     {"Top", "Zjets", "Wjets", "VHVV"}
   *
   * All samples with Zjet keyword attached will have a _Zjets tag appended to the syst name,
   * and similarly for others.
   *
   * If a sample does not match any keyword in this vector, it simply won't have any tag appended.
   */
  std::vector<TString> sampleDecorrelations;

  /**
   * @brief Completely free decorrelation for desperate cases
   *
   * Ultimate freedom for the most complex schemes. One can pass a function to write tags based
   * on a @c Sample and a @c PropertiesSet. Typically one will write lambdas in the constructor.
   *
   * Example: SysWMbb. For Wbb and Wcc only, one wants to decorrelate pTV bins. Plus, in cut-based,
   * bins 2, 3 and 4 should be merged together
   *
   *                    [](const PropertiesSet& pset, const Sample& s) {
   *                      if(! s.hasKW("WbbORcc")) return "";
   *                      if(pset[P::bin] == 0) return "_B0";
   *                      if(pset[P::bin] == 1) return "_B1";
   *                      return "";
   *                    }
   *
   */
  DecorrFunction freeDecorrelation;

  /// Flag for NPs decorrelated in all the categories
  bool decorrEverywhere;

  /**
   * @brief Choose smoothing algorithm based on sample and category
   *
   * This gives freedom to the user to choose the basic smoothing algorithm to apply,
   * depending on the category (and even possibly the sample) considered.
   *
   * Typical usage: VHbb analysis uses monotonic rebinning for MVA distributions,
   * but parabolic rebinning for mBB ones. This function allows to do this configuration
   * once and for all.
   */
  SmoothingFunction userSmoothing;

  /**
   * @ brief Choose symmetrisation algorithm based on sample and category
   *
   * This gives freedom to the user to choose the way the up / down variations of
   * a systematic uncertainty are symmetrised, depending on the category and the sample
   * that the uncertainty affects.
   *
   * The shape impact of certain systematics might look very different in different
   * analysis categories, requiring an adaptation of the symmetrisation procedure.
   */
  SymFunction userSym;

  /** @brief This is a struct to hold the configuration of normalization of regions.
   *  This is what the user fills. One can indicate how to decorrelate things
   *
   *  The vector contains the regions to normalize as well as the regions to take the normalization from.
   *  In both cases they can be a sum of multiple regions.
   *
   *  Typical usage: normalize systematic uncertainties to one single region (SUSY-like systematic uncertainties)
   *  Typical usage: remove the overall impact of model systematic uncertainties in a region with multiple subregions
   */
  std::vector<SysNormRegionsConfig> normalizeRegionsConfig;

  /** @brief This is filled in ComputeNormalizationFactors.
   * This contains the up and down normalization factors for each region.
   */
  std::unordered_map<SampleInCategory*, std::pair<float, float>> normalizeRegionsFactors;

  // and now for dozens of constructors

  /// @name Constructors
  /// @{

  /// Default copy constructor
  SysConfig(const SysConfig&) = default;

  /// Default move constructor
  SysConfig(SysConfig&&) = default;

  /// @name Constructors useful mostly for histo systs
  /// @{

  /// Full constructor
  SysConfig(Treat t = Treat::skip, Smooth sm = Smooth::noSmooth, Symmetrise sym = Symmetrise::noSym,
            std::vector<TString>&& s = {}, std::vector<PropertiesSet>&& c = {}, std::vector<Property>&& d = {},
            std::vector<PropertiesSet>&& cd = {}, std::vector<TString>&& sd = {}, DecorrFunction&& fun = nullptr,
            float scaleFactor = 1.0);

  /// Shorthand with only 1 sample name or keyword to define the affected samples
  SysConfig(Treat t, Smooth sm, Symmetrise sym, const TString& s, std::vector<PropertiesSet>&& c = {},
            std::vector<Property>&& d = {}, std::vector<PropertiesSet>&& cd = {}, std::vector<TString>&& sd = {},
            DecorrFunction&& fun = nullptr, float scaleFactor = 1.0);

  /// Full constructor with user-defined smoothing instead of simple smoothing algorithm
  SysConfig(Treat t, const SmoothingFunction& smFun, Symmetrise sym = Symmetrise::noSym, std::vector<TString>&& s = {},
            std::vector<PropertiesSet>&& c = {}, std::vector<Property>&& d = {}, std::vector<PropertiesSet>&& cd = {},
            std::vector<TString>&& sd = {}, DecorrFunction&& fun = nullptr, float scaleFactor = 1.0);

  /// Full constructor with simple smoothing and user-defined symmetrisation
  SysConfig(Treat t, Smooth sm, const SymFunction& symFun, std::vector<TString>&& s = {},
            std::vector<PropertiesSet>&& c = {}, std::vector<Property>&& d = {}, std::vector<PropertiesSet>&& cd = {},
            std::vector<TString>&& sd = {}, DecorrFunction&& fun = nullptr, float scaleFactor = 1.0);

  /// Full constructor with user-defined smoothing and user-defined symmetrisation
  SysConfig(Treat t, const SmoothingFunction& smFun, const SymFunction& symFun, std::vector<TString>&& s = {},
            std::vector<PropertiesSet>&& c = {}, std::vector<Property>&& d = {}, std::vector<PropertiesSet>&& cd = {},
            std::vector<TString>&& sd = {}, DecorrFunction&& fun = nullptr, float scaleFactor = 1.0);

  /// Shorthand with only 1 sample name or keyword, and user-defined smoothing
  SysConfig(Treat t, const SmoothingFunction& smFun, Symmetrise sym, const TString& s,
            std::vector<PropertiesSet>&& c = {}, std::vector<Property>&& d = {}, std::vector<PropertiesSet>&& cd = {},
            std::vector<TString>&& sd = {}, DecorrFunction&& fun = nullptr, float scaleFactor = 1.0);

  /// Shorthand to decorrelate years
  [[deprecated("This shorthand is deprecated. Please use the regular constructor.")]] SysConfig(
      Treat t, Smooth sm, Symmetrise sym, bool corr_years, std::vector<TString>&& s = {},
      std::vector<PropertiesSet>&& c = {}, std::vector<TString>&& sd = {}, DecorrFunction&& fun = nullptr,
      float scaleFactor = 1.0);

  // SysConfig(Treat t, Smooth sm, bool corr_years, const TString& s,
  // std::vector<PropertiesSet>&& c = {}, std::vector<TString>&& sd = {},
  // std::function<TString(const PropertiesSet&)>&& fun = nullptr);

  /// @}

  /// @name Constructors useful mostly for user-defined systs
  /// @{

  /// Full constructor. Treat and Smooth are useless for user-defined systs.
  SysConfig(std::vector<TString>&& s, std::vector<PropertiesSet>&& c = {}, std::vector<Property>&& d = {},
            std::vector<PropertiesSet>&& cd = {}, std::vector<TString>&& sd = {}, DecorrFunction&& fun = nullptr,
            float scaleFactor = 1.0);

  /// Shorthand with only 1 sample name or keyword to define the affected samples
  SysConfig(const TString& s, std::vector<PropertiesSet>&& c = {}, std::vector<Property>&& d = {},
            std::vector<PropertiesSet>&& cd = {}, std::vector<TString>&& sd = {}, DecorrFunction&& fun = nullptr,
            float scaleFactor = 1.0);

  /// @}

  /// @}

  /// @name Modifiers. They can be chained to easily compose a full @c SysConfig
  /// @{

  /**
   * @brief This @c SysConfig should apply to a given sample
   *
   * @param s Sample name or keyword
   */
  SysConfig& applyTo(const TString& s);

  /**
   * @brief This @c SysConfig should apply to a given set of samples
   *
   * @param vs Sample names or keywords
   */
  SysConfig& applyTo(const std::vector<TString>& vs);

  /**
   * @brief This @c SysConfig should apply in specific regions
   *
   * @param c PropertiesSet which characterize the regions
   */
  SysConfig& applyIn(const PropertiesSet& c);

  /**
   * @brief This @c SysConfig should apply in specific regions
   *
   * @param c List of PropertiesSet which characterize the regions
   */
  SysConfig& applyIn(const std::vector<PropertiesSet>& vc);

  /**
   * @brief This @c SysConfig should apply in specific regions
   *
   * @param func Function of type PropertiesSet -> bool that
   * specifies whether the systematic should apply or not.
   */
  SysConfig& applyIn(const ComplexFunctions::CategoryFunction& func);
  SysConfig& applyIn(const ComplexFunctions::CategoryFunction&& func);

  SysConfig& applyIn(const std::vector<ComplexFunctions::CategoryFunction>& vfunc);

  /**
   * @brief This @c SysConfig should decorrelate based on a given @c Property
   *
   * @param d The @c Property used for decorrelation
   */
  SysConfig& decorr(const Property& d);

  /**
   * @brief This @c SysConfig should decorrelate based on som @c Property
   *
   * @param d The Properties used for decorrelation
   */
  SysConfig& decorr(const std::vector<Property>& d);

  /**
   * @brief This @c SysConfig should decorrelate in specific regions
   *
   * @param cd PropertiesSet which characterize the regions
   */
  SysConfig& decorrIn(const PropertiesSet& cd);

  /**
   * @brief This @c SysConfig should decorrelate in specific regions
   *
   * @param cd List of PropertiesSet which characterize the regions
   */
  SysConfig& decorrIn(const std::vector<PropertiesSet>& cd);

  /**
   * @brief This @c SysConfig should decorrelate a specific sample
   *
   * @param sd Sample name or keyword
   */
  SysConfig& decorrTo(const TString& sd);

  /**
   * @brief This @c SysConfig should decorrelate specific samples
   *
   * @param sd Sample names or keywords
   */
  SysConfig& decorrTo(const std::vector<TString>& sd);

  /**
   * @brief Chose freely how to correlate this @c SysConfig among regions and samples
   *
   * @param fun Function returning the desired decorrelation tag based on the properties
   * of the region and the name of the sample considered
   */
  SysConfig& decorrFun(const DecorrFunction& fun);

  /// Some convenience functions to push_back SysNormRegionsConfig objects.

  /**
   * @brief This @c SysConfig should add a single SysNormRegionsConfig
   * object to normalizeRegionsConfig
   *
   * @param normConf: the SysNormRegionsConfig to be added
   */
  SysConfig& normalize(const SysNormRegionsConfig& normConf);

  /**
   * @brief This @c SysConfig should add a vector of multiple SysNormRegionsConfig
   * objects to normalizeRegionsConfig
   *
   * @param normConf: the SysNormRegionsConfig vector to be added
   */
  SysConfig& normalize(const std::vector<SysNormRegionsConfig>& normConf);

  /**
   * @brief This @c SysConfig should be scaled by a constant factor
   *
   * @param sf scale factor by which histo syst is scaled
   */
  SysConfig& scale(float sf);

  /// @}

  /**
   * @brief Compute the decorrelation tag corresponding to @c pset and @c s
   *
   * Computation of the decorrelation tag of the @c SampleInCategory characterized by
   * @c pset and @c s, based on the rules defined in this @c SysConfig.
   *
   * See the description of the class members for the details about how the decorrelation
   * tags are built.
   *
   * @param pset	A @c PropertiesSet typically coming from some @c Category
   * @param s A @c Sample
   * @return The decorrelation tag, that will have to be appended to a systematic name
   */
  TString getDecorrelationTag(const PropertiesSet& pset, const Sample& s) const;

  /**
   * @brief Get the smoothing algorithm corresponding to this @c pset and @c s
   *
   * If a regular smoothing algorithm has been selected by the user, just return it.
   * If instead the user has provided a function to select the smoothing algo, then
   * execute that function and return the result
   *
   * @param pset A @c PropertiesSet typically coming from some @c Category
   * @param s A @c Sample
   * @return The smoothing algorithm adapted to this @c SampleInCategory
   */
  Smooth getSmoothingAlg(const PropertiesSet& pset, const Sample& s) const;

  /**
   * @ brief Get the symmetrisation algorithm corresponding to this @c pset and @c s
   *
   * If a global symmetrisation procedure has been selected by the user for all regions,
   * just return it. If instead the user has provided a SymFunction to specify the
   * symmetrisation algorithm for a certain category and sample, then execute that
   * function and return the result
   *
   * @param pset A @c PropertiesSet typically coming from some @c Category
   * @param s A @c sample
   * @return The symmetrisation algorithm chosen for this @c SampleInCategory
   */
  Symmetrise getSymAlg(const PropertiesSet& pset, const Sample& s) const;
};

// logical operators to be able to use both CategoryFunctions and PropertiesSets when defining systematics
ComplexFunctions::CategoryFunction operator&&(ComplexFunctions::CategoryFunction& a,
                                              ComplexFunctions::CategoryFunction& b);
ComplexFunctions::CategoryFunction operator&&(const PropertiesSet& a, const ComplexFunctions::CategoryFunction& b);
ComplexFunctions::CategoryFunction operator&&(const ComplexFunctions::CategoryFunction& a, const PropertiesSet& b);

/// Short version of @c SysConfig::Treat for use in other classes
using STreat = SysConfig::Treat;

/**
 * @brief A systematic of any type, that applies on 1 sample in 1 category
 *
 * The internal (in @c WSMaker) representation of a systematic of any type (histo, normalization,
 * even floating normalization). This information is easily translated into @c HistFactory language,
 * with all numbers written in the XML files and variation histograms written in 'normalized'
 * @c ROOT files.
 *
 * @see OutputHandler for the translation in @c HistFactory language
 *
 * When building systematics from histograms, one loops over the input files, and will encounter
 * a @c MySystUp and a @c MySystDo directories, in any order. So typically partial @c Systematic
 * objects will be created with only @c up or @c down variation, then they will be merged into
 * a complete object.
 *
 * @see @c Category and @c SampleInCategory for the logic of the construction of systematics
 * from input histograms
 *
 */
struct Systematic {
  /// Possible sides of a systematic when built from histograms.
  enum class Side { up, down };

  /**
   * @brief A syst can be a shape syst, a norm syst, or a floating norm syst.
   *
   * The order of the enum is important to follow the HistFactory XML DTD.
   *
   */
  enum class Type { shape, norm, flt, MCstat, freeShape };

  /**
   * @brief Status of a systematic wrt pruning
   *
   * If the systematic has been pruned at some stage, keep track of it.
   *
   * @todo Should we keep this enum here ?
   *
   */
  enum Status { NotConsidered = 0, PruneSmall, PruneOneSide, PruneYao, PruneOther, Used };

  Type                  type;       ///< Type of the systematic
  TString               name;       ///< Name of the systematic, e.g SysBTagB3
  float                 var_up;     ///< Up variation for a norm systematic, and upper bound for floating norm
  float                 var_do;     ///< Down variation for a norm systematic, and lower bound for floating norm
  float                 init;       ///< Initial value for floating norm
  std::shared_ptr<TH1>  shape_up;   ///< Histo with Up variation for shape syst
  std::shared_ptr<TH1>  shape_do;   ///< Histo with Down variation for shape syst
  bool                  isConst;    ///< For a floating norm, should it be constant ?
  SysConfig::Smooth     smooth;     ///< Which kind of smoothing to use
  SysConfig::Symmetrise symmetrise; ///< Which kind of symmetrisation to use
  std::shared_ptr<TH1>  shape_up_unsmoothed; ///< Histo with Up variation for shape syst before smoothing
  std::shared_ptr<TH1>  shape_do_unsmoothed; ///< Histo with Down variation for shape syst before smoothing
  std::shared_ptr<TH1>
      mc_stat_error_absolute_sample; ///< Histo representing the MC stat error in each bin. This is an absolute error.
  std::shared_ptr<TH1>
      mc_stat_error_fractional_shared; ///< Histo representing the total MC stat error of the group of samples. This is
                                       ///< directly passed to HistFactory. This should be a fractional error.

  /// No empty constructor
  Systematic() = delete;

  /// Default copy constructor
  Systematic(const Systematic&) = default;

  /// Default move constructor
  Systematic(Systematic&&) = default;

  /**
   * @brief Generic constructor for an empty syst
   *
   * @param t Type of the systematic
   * @param aname Name of the systematic
   */
  Systematic(Type t, const TString& aname) :
      type(t),
      name(aname),
      var_up(1),
      var_do(1),
      init(0),
      shape_up(nullptr),
      shape_do(nullptr),
      isConst(false),
      smooth(SysConfig::Smooth::noSmooth),
      symmetrise(SysConfig::Symmetrise::noSym),
      shape_up_unsmoothed(nullptr),
      shape_do_unsmoothed(nullptr)
  {}

  /**
   * @brief Constructor for a normalization systematic
   *
   * @param aname Name of the systematic
   * @param down Normalization factor for down variation (e.g 0.8 for -20%)
   * @param up Normalization factor for up variation (e.g 1.2 for +20% or 0.8 for -20%)
   */
  Systematic(const TString& aname, float down, float up) :
      type(Type::norm),
      name(aname),
      var_up(up),
      var_do(down),
      init(0),
      shape_up(nullptr),
      shape_do(nullptr),
      isConst(false),
      smooth(SysConfig::Smooth::noSmooth),
      symmetrise(SysConfig::Symmetrise::noSym),
      shape_up_unsmoothed(nullptr),
      shape_do_unsmoothed(nullptr)
  {}

  /**
   * @brief Constructor for a floating norm systematic
   *
   * @param aname Name of the systematic
   * @param init Initial value of the scale factor
   * @param down Lower bound
   * @param up Upper bound
   * @param constness Should this normalization be floated or not in the fits ?
   */
  Systematic(const TString& aname, float init, float down, float up, bool constness) :
      type(Type::flt),
      name(aname),
      var_up(up),
      var_do(down),
      init(init),
      shape_up(nullptr),
      shape_do(nullptr),
      isConst(constness),
      smooth(SysConfig::Smooth::noSmooth),
      symmetrise(SysConfig::Symmetrise::noSym),
      shape_up_unsmoothed(nullptr),
      shape_do_unsmoothed(nullptr)
  {}

  /**
   * @brief Constructor for a free shape (e.g. data-driven background shape)
   *
   * @param aname Name of the systematic
   * @param init Initial value of the scale factor
   * @param down Lower bound
   * @param up Upper bound
   */
  Systematic(const TString& aname) :
      type(Type::freeShape),
      name(aname),
      var_up(10),
      var_do(0),
      init(1),
      shape_up(nullptr),
      shape_do(nullptr),
      isConst(false),
      smooth(SysConfig::Smooth::noSmooth),
      symmetrise(SysConfig::Symmetrise::noSym),
      shape_up_unsmoothed(nullptr),
      shape_do_unsmoothed(nullptr)
  {}

  /**
   * @brief Find the real name and @c Side of the syst from its directory name in input files
   *
   * HSG5 conventions are:
   * - @c XXXXUp -> name is @c XXXX, @c Side is @c up
   * - @c XXXXDo -> name is @c XXXX, @c Side is @c down
   * - @c XXXX   -> name is @c XXXX, @c Side is @c symmetrize
   *
   * But there are exceptions in some inputs... so we take care of them too.
   * @c JetEResolUp that is present sometimes should be interpreted as JetEResol.
   *
   * @param name	The directory name in the input file
   * @return A pair with the name of the systematic and its @c Side
   */
  static std::pair<TString, Side> interpretSysName(const TString& name);

  /**
   * @brief Merge @c other @c Systematic into @c this
   *
   * Merge 2 complementary systematics into a single one. Typical use-case is for
   * histo-based systematics, where the up and down variations are built separately,
   * then merged.
   *
   * @c this and @c other must be of the same @c Type, otherwise an exception is thrown.
   *
   * In case a property defined in @c other already exists in @c this, the value from
   * @c other is used. A warning is then printed on @c stdout.
   *
   * @param other	The @c Systematic to merge into @c this
   */
  void merge(const Systematic& other);

  /**
   * @brief Comparison of @c Systematic
   *
   * Ordering of @c Systematic is ensures they are written in correct order in the XML files.
   * We have to comply with the @c HistFactory DTD format.
   *
   * @see @c SysOrdering for the description of the ordering scheme
   *
   * @param other The @c Systematic to compare to
   * @return @c true if @c this is lower than @c other. @c false otherwise.
   */
  bool operator<(const Systematic& other) const;

  /**
   * @brief Equality of @c Systematic
   *
   * Both @c type and @c name are tested for equality.
   *
   * @param other	The @c Systematic to compare to
   * @return @c true if @c this and @c other are equal in type and name
   */
  bool operator==(const Systematic& other);

  /**
   * @brief Print some info on @c this
   *
   * The content printed depend on the type. Useful for debugging purpose,
   * but can quickly fill the ouput if used on all systematics of a workspace
   *
   */
  void print() const;
};

using SysType   = Systematic::Type;
using SysKey    = std::pair<SysType, TString>;
using SysStatus = Systematic::Status;

/**
 * @brief Ordering scheme of @c Systematic
 *
 * Systematics are first ordered according to their @c Type. The order of the enum is
 * chosen to comply with @c HistFactory DTD.
 *
 * Then systematics are ordered with their name, in plain alphabetical order.
 */
struct SysOrdering {
  bool operator()(const SysKey& s1, const SysKey& s2) const
  {
    int itype       = static_cast<int>(s1.first);
    int other_itype = static_cast<int>(s2.first);

    if( itype == other_itype )
      return (s1.second.CompareTo(s2.second) > 0);
    return (itype < other_itype);
  }
};

/**
 * @brief Structure to hold configuration for 3-to-2 systematics
 *
 * Describe 3-to-2 systematics à la ttbar EPS 2013:
 * A systematic uncertainty is put on the 3/2 ratio, with 2+3 constant in each category.
 * So for every 2jet category, its exact correspondance in 3jet must exist.
 * Then the anticorrelated uncertainties in the 2jet and the 3jet categories are computed,
 * so that the uncetainty on the ratio matches the desired number.
 *
 */
struct Systematic32 {
  TString   name; ///< Name of the systematic
  float     size; ///< Size of the 3-to-2 systematic uncertainty
  SysConfig conf; ///< Configuration: where it applies, what should be decorrelated
};

struct NormIntegrals {

  /// total integral nominal
  float nom;

  /// total integral variation up
  float up;

  /// total integral variation down
  float down;

  /* @brief Sum of @ NormIntegrals
   * This operator sums up two NormIntegrals structures
   * nom+=nom, up+=up, down+=down
   *
   * @param other The @c NormIntegrals to be summed together
   */
  NormIntegrals operator+(NormIntegrals& other);

  /* @brief self assignment operator for @ NormIntegrals
   * This operator fills a  NormIntegrals structure
   * (all of this to be able to do a+=b)
   *
   * @param other The @c NormIntegrals to be assigned
   */

  NormIntegrals operator=(const NormIntegrals& other);

  /// Default constructor
  NormIntegrals() = default;

  /** default constructor
   * @param n is nominal  integral
   * @param u is up   var integral
   * @param d is down var integral
   */
  NormIntegrals(float n, float u, float d);

  /** @brief Printing function
      it prints out nom, up and down integrals stored in the NormIntegrals object
      * in the form of:
      *  nom: X up: Y down: Z
   */
  void print();
};

#endif
