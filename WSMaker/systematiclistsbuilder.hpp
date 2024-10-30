#ifndef systematiclistsbuilder_hpp
#define systematiclistsbuilder_hpp

#include <unordered_map>
#include <utility>
#include <vector>

#include <TString.h>

#include "configuration.hpp"
#include "containerhelpers.hpp"
#include "systematic.hpp"


/**
 * @brief Class to fill the list of systematics
 *
 * The main role of this class is to build the configuration for all sytematics
 * of the analysis:
 * * user-defined norm systematics
 * * POIs, norm factors
 * * histo-based systematics
 * * 3-to-2 systematics
 *
 * It has two main functions:
 * * @c listAllHistoSystematics defines the configuration for all histo-based systs
 * * @c listAllUserSystematics is used to set all user-defined values, normfactors, and POIs.
 *
 * It is triggered by @c SystematicHandler, which delegates the building of the systematics
 * configs to it.
 *
 * It is a base class that is meant to be subclassed by the different analyses.
 *
 * It has helper functions to easily add some kind of user-defined systematics.
 *
 */
class SystematicListsBuilder {
 protected:
  /// Configuration of the analysis
  Configuration m_config;

  /**
   * @brief Reference to storage of the user-defined systematics (norm systs and norm factors)
   *
   * @see SystematicHandler for details
   */
  std::vector<std::pair<Systematic, SysConfig>>& m_userSysts;

  /// Reference to storage of the POIs
  std::vector<std::pair<Systematic, SysConfig>>& m_pois;

  /// Reference to storage of the 3-to-2 systematics
  std::vector<Systematic32>& m_32ratios;

  /**
   * @brief Reference to storage of the hist-based systematics
   *
   * @see SystematicHandler for details
   */
  std::unordered_map<TString, SysConfig>& m_histoSysts;

  /// Reference to storage for renaming rules of systematics
  std::unordered_map<TString, TString>& m_renameHistoSysts;

  /// Reference to list of NormFactors that should be constant in the fit
  std::vector<TString>& m_constNormFacts;

  /// Reference to list of MCStatSysts that will be  used
  std::vector<SysConfig>& m_MCStatSysts;

  /// @name Internal functions to add user-defined systematics
  /// @{

  /**
   * @brief Add a user-defined syst and its configuration
   *
   * Most generic function. Is it needed at all ?
   *
   * @param sys Systematic to add
   * @param conf Its configuration
   */
  void applySys(Systematic&& sys, const SysConfig& conf = {});

  /// @name Basic ones
  /// @{

  /**
   * @brief Add an asymmetric norm systematic
   *
   * @param name	Name of the systematic
   * @param min	Down variation (e.g 0.8 means -20%)
   * @param max	Up variation (e.g 1.2 means +20% or 0.8 for -20%)
   * @param conf Configuration for this systematic
   */
  void normSys(const TString& name, float min, float max, const SysConfig& conf = {});

  /**
   * @brief Add a symmetric norm systematic
   *
   * @param name	Name of the systematic
   * @param size Size of the systematic (e.g 0.2 means +/-20%)
   * @param conf Configuration for this systematic
   */
  void normSys(const TString& name, float size, const SysConfig& conf = {});

  /**
   * @brief Add a floating norm
   *
   * @param name Name of the floating norm. "ATLAS_norm" is prepended.
   * @param conf Configuration of the floating norm
   * @param init Initial value of the variable in the workspace
   * @param down Lower bound for the variable
   * @param up   Upper bound for the variable
   * @param isConst Whether this variable should be constant by default
   */
  void normFact(const TString& name, const SysConfig& conf = {}, float init = 1, float down = 0, float up = 10,
                bool isConst = false);

  /**
   * @brief Add a floating shape (e.g. for data-driven background
   *
   * @param name Name of the floating norm. "ATLAS_norm" is prepended.
   * @param conf Configuration of the floating norm
   */
  void shapeFact(const TString& name, const SysConfig& conf = {});

  /**
   * @brief Add a POI
   *
   * @param name Name of the POI
   * @param conf Configuration for the POI
   * @param init Initial value of the POI
   * @param down Lower bound for the POI
   * @param up   Upper bound for the POI
   */
  void addPOI(const TString& name, const SysConfig& conf = {}, float init = 1, float down = 0, float up = 10);

  /**
   * @brief Declare a 3-to-2 systematic
   *
   * @see Systematic32 for the description of 3-to-2 systematics
   *
   * @param name Name of the systematic
   * @param size Size of the systematic
   * @param conf Configuration of the systematic
   */
  void ratio32(const TString& name, float size, const SysConfig& conf = {});

  /// @}

  /// @name Convenience  ones
  /// @{

  /**
   * @brief Add a norm systematic for a given sample
   *
   * Convenience function to add a normalization uncertainty on a sample or a group of
   * samples.
   *
   * The name of the systematic will be @c Sys(name)Norm, e.g @c SysWccNorm
   *
   * The name can be the name of a sample or any keyword known to @c SampleHandler. All samples
   * that have this keyword attached will then be affected (e.g @c SysWjetsNorm)
   *
   * @param name	Name of the affected sample. Can be actually any keyword defined in
   * @c SampleHandler
   * @param size  Size of the systematic
   */
  void sampleNormSys(const TString& name, float size);

  /**
   * @brief Add an asymmetric norm systematic for a given sample
   *
   * Convenience function to add an asymemtric normalization uncertainty on a sample or a group of
   * samples.
   *
   * The name of the systematic will be @c Sys(name)Norm, e.g @c SysWccNorm
   *
   * The name can be the name of a sample or any keyword known to @c SampleHandler. All samples
   * that have this keyword attached will then be affected (e.g @c SysWjetsNorm)
   *
   * @param name  Name of the affected sample. Can be actually any keyword defined in
   * @c SampleHandler
   * @param min  Minimum scale factor of the systematic asymmetric down variation. If the asymmetric variation is (-0.2,
   * + 0.3), then min should read 0.8.
   * @param max  Maximum scale factor of the systematic asymmetric up variation. If the asymmetric variation is (-0.2, +
   * 0.3), then max should read 1.3
   */
  void sampleNormSys(const TString& name, float min, float max);

  /**
   * @brief Add a 3J norm systematic for a given sample
   *
   * Convenience function to add a 3J normalization uncertainty on a sample or a group of
   * samples.
   *
   * The name of the systematic will be @c Sys(name)Norm_J3, e.g @c SysWccNorm_J3
   *
   * The name can be the name of a sample or any keyword known to @c SampleHandler. All samples
   * that have this keyword attached will then be affected (e.g @c SysWjetsNorm_J3)
   *
   * @param name	Name of the affected sample. Can be actually any keyword defined in
   * @c SampleHandler
   * @param size  Size of the systematic
   */
  void sampleNorm3JSys(const TString& name, float size);

  /**
   * @brief Add a MC stat uncertianty to samples.
   *
   * This will be called in the systematiclistsbuilder specific to the analysis.
   * @return The reference to the @c SysConfig instanse that were just added.
   */
  SysConfig& MCStatSys();

  /// @}

  /// @}

 public:
  /// No empty constructor
  SystematicListsBuilder() = delete;

  /**
   * @brief Standard contructor
   *
   * @param conf Configuration of the analysis
   * @param userSysts Reference to the map of user-defined systematics
   * @param pois Reference to the map of pois
   * @param r32ratios Reference to the map of 3-to-2 jet systematics
   * @param histoSysts Reference to the map of histo-based systematics
   * @param renameHistoSysts Reference to the remapping of histo-based systs
   * (to work around typos in the inputs files)
   * @param constNormFacts Reference to the list of floating NP that should be
   * kept constant
   */
  SystematicListsBuilder(const Configuration& conf, std::vector<std::pair<Systematic, SysConfig>>& userSysts,
                         std::vector<std::pair<Systematic, SysConfig>>& pois, std::vector<Systematic32>& r32ratios,
                         std::unordered_map<TString, SysConfig>& histoSysts,
                         std::unordered_map<TString, TString>& renameHistoSysts, std::vector<TString>& constNormFacts,
                         std::vector<SysConfig>& MCStatSysts);

  /// Empty destructor
  virtual ~SystematicListsBuilder() {}

  /**
   * @brief Fill the map of renaming rules for systematics names
   *
   * This is typically used to correct for bugs in syst names in some inputs
   */
  virtual void fillHistoSystsRenaming() = 0;

  // list them all !
  /**
   * @brief Populate the list of user-defined systematics
   *
   * This is the main function where all user-defined systematics and flaoting norm NP should
   * be defined with their configurations.
   *
   * The POI(s) are also defined here.
   *
   * All the convenience functions can be used to define the systematics in the most readable way.
   *
   * This function must be implemented by the subclasses.
   *
   * @see @c SysConfig for the possibilities to configure systematics
   *
   * @param useFltNorms Whether some backgrounds should be let free, or be constrained to a prior
   */
  virtual void listAllUserSystematics(bool useFltNorms) = 0;

  /**
   * @brief Populate the list of expected histo-based systematics
   *
   * This is the main function where all the configuration for histo-based systematics
   * is defined.
   *
   * This function must be implemented by the subclasses.
   *
   * @see @c SysConfig for the possibilities to configure systematics
   */
  virtual void listAllHistoSystematics() = 0;
};

#endif
