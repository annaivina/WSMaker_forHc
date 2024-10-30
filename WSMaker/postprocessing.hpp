#ifndef postprocessing_hpp
#define postprocessing_hpp

#include <memory>

#include <TString.h>

#include "configuration.hpp"

/**
 * @brief Class to perform operations on a workspace after its creation.
 *
 * Sometimes, it is more convenient to first create a standard HistFactory workspace
 * and then make changes afterwards, i.e. through factory EDIT commands. The
 * PostProcessingTool allows to do this.
 *
 * This base class does not modify the workspace, but is only used to maintain
 * backward compatibility. If your analysis requires making modifications to the workspace,
 * you should create your own derived class.
 */

class PostProcessingTool {
 protected:
  /// the instance of the singleton
  static std::unique_ptr<PostProcessingTool> the_instance;

  /// Pointer to the @c Configuration of the analysis
  Configuration m_config;

  /// No default constructor
  PostProcessingTool() = delete;

  /**
   * @brief Default constructor with a @c Configuration object
   *
   * Set a number of internal parameters based on the configuration.
   *
   * @param conf the @c Configuration of the analysis.
   */
  PostProcessingTool(const Configuration& conf);

 public:
  /**
   * @brief Return static pointer to the instance after building it
   *
   * A similar function must be implemented by all child classes.
   *
   * @param conf A @c Configuration object
   * @return Pointer to the instance of the @c PostProcessingTool
   */
  static void createInstance(const Configuration& conf);

  /**
   * @brief Return static pointer to the instance
   *
   * @return Pointer to the instance of the @c PostProcessingTool
   */
  static PostProcessingTool& getInstance();

  /**
   * @brief Modify the created HistFactory workspace
   *
   * A similar function must be implemented by all child classes. This is
   * where the actual modifications of the workspace occur.
   *
   * @param wsfilename The path to the file containing the HistFactory
   * workspace created by the @c Engine. The corresponding method in the
   * derived class will typically read the workspace from this file, modify
   * it and store the result in the same (or another) file.
   */
  virtual void process(const TString& wsfilename);
};

#endif
