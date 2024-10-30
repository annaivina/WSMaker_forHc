# Changelog
## [12-05-04] - 2023-07-28
### Changed/Updated/Improved
  - Move to LCG 103(ROOT 6.28/00)
  - Improved plotting scripts for pull plots and correlation matrices

## [12-05-03] - 2023-07-14
### Added
  - `.clang-format` for consistent formatting of C/C++ code.
  - Added `ntaus` as a property 

### Changed/Updated/Improved
  - python 3 migration of the code
  - Move to LCG 99
  - Updated compatibility with new systematics folder structure from CxAODReader (one folder per variation instead of one `Syst` folder)
  - Re-introducing `TagTypes` as a property for use in the VH(bb/cc) legacy analysis
  - Added capability to split inputs by year 
  - Make likelihood plot labels configurable 
  - Increased stack size to `unlimited`
  - Fixed STXS signal strength and correlation plots 
  - Initialise floating normalisations at 1.1 to improve fit stability

### Fixed
  - Remove error check in `binning.cpp` which caused the code to crash in some cases 
  - Change `sh` to `bash` in `BatchMgr.py` for compatibility
  - Make `getHist` a `const` function

### Analysis-specific changes
  - Increase tolerance for VH(bb/cc) legacy analysis
  - Decrease text size in pull plots for AZHeavyH analysis 

## [12-05-02] - 2021-12-22
Tag master before upgrading to python3

### Added
  - Automatic conversation of brakdown tables to tex
  - Allow renaming of NPs in plots (FCC, ranking) from `analysisPlottingConfig`
  - Add expected data stat to control plots

### Changed/Updated/Improved
  - Move to LCG 99python2 (ROOT 6.22/06)
  - First part of python3 upgrade, with changes still compatible with python2
  - Use `std::isnan`
  - Improve Workspace creation speed by working around ROOT GetObject bug
  - Improve makeTables.py
  - Remove empty plots from comparePulls

### Fixed
  - fix logfiles for manual likelihood scan
  - Changing job submission sequence to run pulls job only after FCC one
  - Bugfix for condor jobs submission
  - Fix macro compilation
  - Compute normalization factors only when performing a Syst or a FloatOnly fit

### Analysis-specific changes
  - Setting correct tolerance for VHcc
  - Add VBS semileptonic analysis
  - Plotting changes for VH(cc)
  - Add template analysis


## [12-05-01] - 2021-03-30
### Changed/Updated/Improved
  - Complete rework of batch systems. Allow for deeper parallelisation of breakdown and ranking. Currently supported batch managers are HTCondor and Torque.

### Added
  - New `SysConfig::scaleFactor` member that is used for easy scaling of a histogram systematic by a constant factor
  - New `SysConfig::scale(float sf)` function to easily scale a systematic
  - `ComplexFunctions::CategoryFunction` used to select arbitrary categories using boolean operations. Can be used when selecting reference regions for renormalization of systematics.

### Removed
  - Buggy `BinningTool::scaleHistoSys` implementation (replaced by `SampleInCategory::scaleHistoSys`)

### Analysis-specific changes
  - Text sizes for VHqq
  - Change fit tolerance for VHcc

## [12-05-00] - 2020-10-07
### Fixed
  - Blinding in runAsymptoticsCLs no longer hardcoded to be off (env var used instead)
  - Setting floating parameters to constant when using decorrelation tags now works as intended
  - Ranking run iterator increased to cover all RooArgSets (hopefully)

### Changed/Updated/Improved
  - multi-POI handling in runSig and runAsymptoticsCLs:
	- float all NPs when fitting data to determine the NP values for post-fit Asimov creation (+ blinding the printout)
	- create post-fit Asimov as well with all POIs = 1
  - multi-POI handling in FCC:
	- loop over all POIs instead of only taking the first one (e.g. when running conditional and setting them to 1)
  - conditionnal multi-POI in doPlotsFromWS:
	- fix all POIs to muhat when forcing a value
  - new mechanism to veto individual samples in some fit regions
	- users can specify in analysis-specific code (`samplesbuilder_*`) which categories a sample should not be added to
  - new way to define the set of regions that systematic uncertainties apply to
	- now possible in a more flexible way via callback functions (similar to decorrelations), see inline documentation in `systematic.hpp` for an example
	- logical `AND` with `PropertiesSets` to select regions is supported
  - add mechanism to select the symmetrisation algorithm used for a given systematic based on the fit region and the sample affected by that systematic, see inline documentation in `systematic.hpp` for more details
  - compare pull now also can compare cond and uncond pulls
  - possibilty to add pre/post-fit ratio post-fit lower pads
  - new syst debugging entries : sum in normVals, shape sums in syst/ output

### Added
  - New mechanism to normalize systematics to other regions or a superset of multiple regions.
	- This addition incorporates the post-processing step within the code.
	- This allows for the implementation of SUSY-like norm-histo systematics.
  - See here for more details: https://indico.cern.ch/event/932235/contributions/3938429/
  - Added flag SymmetriseAfterSmooth to change to order of symmetrising and smoothing of systematics
	- New AnalysisType::SemileptonicVBS
  - Added `freeShape` syst type to define free floating shapes
  - mu compatibility macro

## [12-04-02] - 2019-11-28
### Fixed
  - eos copy function in SplitInput
  - script typos
  - smoothing see [linkToMR](https://gitlab.cern.ch/atlas-physics/higgs/hbb/WSMaker/merge_requests/117) and summary here [link to slides](https://indico.cern.ch/event/866461/contributions/3651050/attachments/1951400/3239638/smoothing_fix.pdf)
  - empty histo protection

### Changed/Updated/Improved
  - plotting f-tag SFs after applications of EV pulls, see [link to macros/flavTagSFunfold/README.md](https://gitlab.cern.ch/atlas-physics/higgs/hbb/WSMaker/blob/master/macros/flavTagSFunfold/README.md)
  - various bd table settings (VHbb boosted/resolved) + minor plotting labels
  - ROOT version
  - possibility to blind uncertainties in data-fit pull plots; meant for signal; using `self.cov_blind = []` parameter in `plottingConfig`
  - likelihood scan functionnalities and plotting improvements
  - reduced fit minimum estimate tolerance; reduced speed, improved precision; see [link to slides](https://indico.cern.ch/event/866461/contributions/3651051/attachments/1951522/3239876/1126noguchi_vhbb.pdf)

### Added
  - possibility to define sets of properties
  - fit results parser scripts
  - STXS plotting scripts
  - Workspace post-processing (re-parametrization), see [link to MR](https://gitlab.cern.ch/atlas-physics/higgs/hbb/WSMaker/merge_requests/103) and [link to howto](https://indico.cern.ch/event/866461/contributions/3651052/attachments/1950802/3238424/EFT4WSMaker.pdf)


## [12-04-01] - 2019-09-17
### Fixed
  - Skip sys from empty histograms in WS creation

## [12-04-00] - 2019-09-05
### Fixed
  - WSMaker now crashes if an input file is missing
  - If require SymOneSided: overwrites down if both sides exist ! Need to change to a crash when possible

### Changed
  - Breakdown: remove outdated, add STXS and boosted
  - remove ggZZ k-factor
  - doPlotFromWS can now keep track of histos entering a sum to conserve the binning

### Added
  - InputCheck script now also survey underflow/overflow

### Analysis-specific changes
  - AnalysisType::MonoS


## [12-03-00] - 2019-05-21
### Fixed
  - Flag to use Gaussian prior on MC stat NP now works properly
  - Some small plotting issues

### Added
  - Scales of ranking plot as optional parameters of the script
  - Year 2018 in parsing and plotting
  - Support for Condor batch system at CERN
  - One more entry in HowTo.md

### Removed
  - Support for LSF batch system

### Analysis-specific changes
  - AnalysisType::boostedVHbbRun2
  - Renaming gamma stat errs. in boosted VHbb analysis


## [12-02-00] - 2018-10-17
### Fixed
  - Missing doc in helper string of postfit tables script
  - Typo in comparePulls
  - Small fix in ranking plot when splitting jobs for multi-POI workspaces

### Added
  - Impact of other POI in ranking plots for multi-POI workspaces
  - ProposertiesSet can be built from strings. Useful to set big batch of systs from reading a TH1,2
  - Definition of keywords can contain other keywords. Useful for STXS with 50 signal samples


## [12-01-00] - 2018-09-13
### Fixed
  - Bugfixes and improvements in `InputsCheck.py`
  - Typos in breakdwon output (can be compiled in Latex)
  - Additional signal line in postfit plots correctly drawn
  - Wrong prefit impact not drawn for gamma stat NP
  - Multiple small fixes in python files (correct includes, python3 compatibility)
  - Memory leaks in comparePulls
  - Tiny bugfix in `runAsymptotics`, improves convergence times by 10%, does not
  change the results

### Added
  - Ability to put MC stat NP specific to given sample(s)
  - Possibility to generate pseudo-data on postfit plots
  - `getResults.py` now know about results of breakdown
  - flag in comparePull to remove the display of the real pulls (squares)
  - Significance script able to deal with multi-POI workspaces
  - Ranking plot script able to deal with multi-POI workspaces
  - Ability to do MC16a+d fits
  - New version of bkg-subtracted plots
  - Flag to draw normalization NP as red dots in ranking plots
  - Add mode 11 for newGetMuHat (STXS)
  - Possibility to change the size of some histogram-based systematics. Currently
  hardcoded in `category`, possibility to make it easily steerable by analyses if there
  is enough interest
  - Switch `UseGaussianConstraintTypeMCStat` to use Gaussian constraints for MC stat NP
  instead of default Poisson ones

### Changed
  - Various improvements in FitCrossChecks
  - New interface for comparePulls, esp. accepting legends as arguments
  - Rework blinding for some of the scripts. Introduce a `IS_BLINDED` environment variable
  in `setup.sh` which can be overwritten in analysis-specifc setup files
  - Updated default lumi in ranking plots
  - gamma stat NP run by default in ranking plots
  - Improved display of norm and shape status debug plots
  - New option to draw pull comparisons from `doActions.py`
  - Tweaks of default values in `plotMaker` and other scripts

### Analysis-specific changes
  - Added ggZZ k-factor deep in InputsHandler (VHbb)
  - Add VHcc to the list of analyses


## [12-00-00] - 2018-05-29
### Fixed
  - Small fixes to make lxbatch jobs work again
  - Bugfixes for the new pulls of NP in comparePulls and makeReducedDiagPlots
  - Small fixes for postfit plots
  - Fixes to kernel smoothing
  - Small fix to `InputsCheck.py`

### Added
  - Configuration of comparePulls/makeReducedDiagPlots can use both include and exclude
  at the same time

### Changed
  - All the output of programs and scripts has been revamped. Every workspace now has all its
  output stored in a single directory. Should make it easier for newcomers to find their way
  in the package
  - Simplification of setup script: optional argument to define $WORKDIR directly
  - Slightly improved display in comparePulls: points belonging to same NP are grouped more closely
  - Updated JES names

## [11-02-00] - 2018-05-01
### Fixed
  - Small fix in newGetMuHat to remove one spurious NP in the ModelTop block of the impact.
  - Small fixes of code documentation

### Added
  - Scripts for validation of input files. Analyses can import InputsCheck.py in their
  own python script to define the checks to perform on their files. See VHbb as an example.
  - New script `scripts/printSignificances.py` to print neat significance tables by parsing
  the logfiles of runSig.
  - Add real pulls of NP in FitCrossChecks, according to
  https://indico.cern.ch/event/716504/contributions/2985751/attachments/1640753/2621043/PullsOfNP.pdf
  Info propagated to makeReducedDiagPlots and comparePulls

### Changed
  - Separate symmetriseAverage and symmetriseOneSided as per #30. Implies changes in
  systematicslistsbuilder for all analyses, as one-sided systs should be using the new
  keyword, and symmetriseAverage should be reserved for real 'averaging' cases.
  - Allow for 13TeVmc16x in region names in config files to allow setting correct years.
  Used by VHbb analysis to set correctly the luminosity in plots.
  - Some small changes in scripts for forward compatibility with python3


## [11-01-00] - 2018-03-20
### Removed
  - RegionTracker is gone. Its functionality is superceded by functions in CategoryIndex,
  directly accessible in the systemtaticlistsbuilder functions.
  - Two specific functions which could be used only by VHbb Run1 analysis


## [11-00-00] - 2018-03-20
First tag with the new package structure
### Added
  - A "Generic" AnalysisType, can be used by analyses that don't need analysis-specific bits
  in common code

### Removed
  - All analysis-specific scripts, configs and classes (analysis-specific bits inside common
  code still exist)
  - HistFactorySchema.dtd, now fetched from $ROOTSYS instead
  - unused compile.C
  - util/, as executables are to be implemented by each analysis

### Changed
Needed changes for the new structure:
  - setup script, CMakeLists
  - scripts for submission on lxbatch
  - other scripts
  - headers are now in WSMaker/
  - Construction of the Engine, which takes the Analysis object as a parameter


## [10-04-00] - 2018-03-19
Last tag with the monolitic package structure
### Fixed
  - Minor bugfix on how the unsmoothed copies of histograms where merged (#28)
  - Remove hardcoded values of parameters in newGetMuHat. Would have affected analyses
  in their Asimov expected impact if they had parameters: `ATLAS_norm_ttbar`
  `ATLAS_norm_ttbar_J2_L2_Y` `ATLAS_norm_ttbar_J3_L2_Y` `ATLAS_norm_Wbb_J2` `ATLAS_norm_Wbb_J3`
  `ATLAS_norm_Zbb_J2` `ATLAS_norm_Zbb_J3`

### Added
  - Possibility to do pruning after merging of samples. Config switch `PruneAferMerge`
  - Possibility to do smoothing after merging of samples. Config switch `SmoothAfterMerge`
  - New functions findAll and hasMatching in CategoryIndex. Can be used to achieve
  same functionality as RegionTracker, without the need for that class. RegionTracker
  can be removed in the future.
  - Proper option `draw_error_band_on_b_only` in plottingConfig to draw the error band
  in postfit plots on S+B (false) or B only (true). Works for both regular plots and
  "sum" plots.

### Removed
  - NPRanking/ directory, which contains old, not used code

### Changed
  - Move default colors for correlation matrices. Use VHcc color palette.
  - Huge overhaul of smoothing and symmetrizing of systematics. See #7. Each smoothing alg
  is an item in an enum, so the user can select a different algo per systematic. Also
  possibility to choose the algo depending on the distribution (actually region and sample)
  it acts on (VHbb use-case). Averaging can be selected by a specific bit in SysConfig, so
  independently for each syst. Remove hardcoded symmetrization of some systs (JER), they
  should now be marked individually by the user with the symmetrization bit.
  Overall much cleaner configuration, transparent for the user and customizable.

### Changes for analyses
  - VHbb uses the new functions instead of RegionTracker. Better for readability.
  - VHbb: add code for STXS fits
  - VHbb: add mini-tutorial


## [10-03-00] - 2018-02-23
### Added
  - new API for SysConfig. Allows hopefully more readable code in systematiclistbuilders
  - syntaxic sugar for PropertiesSet, which allows more readable code in systematiclistbuilders

### Changed
  - Technical improvements. Pure code cleaning, no impact on any workspace.
  - Use variants in PropertiesSet. Simplifies the struct, with only 1 map instead of 2.

### Removed
  - Classes for the old, unmaintained VHRes and HVT analyses

### Changes for analyses
  - the VHbb systematiclistbuilder uses the new APIs for better readability


## [10-02-00] - 2018-02-20
### Fixed
  - Smoothing algorithm now works as intended. 4-y.o bug fixed.
  - bad interaction of renamed systs and SkipUnknownSysts
  - Make CoreRegions works again in Run2

### Removed
  - Lots of inputConfigs files for old analyses

### Added
  - Changelog.md

### Changes for analyses
  - VHbb: cleanup of systs config. Config for first tests with rel21/mc16ac


## [10-01-00] - 2018-02-07
### Changed
  - ROOT 6.12 version
  - build now based on CMake

### Removed
  - Makefile

### Changes for analyses
  - mono-V


## [WSMaker-10-00-00] - 2017-11-30
### First tag on git
  - Make TransformTool a git submodule of the project

### Changed
  - Small HowTo update
  - Commented out inconsistent additional column in tex table in newGetMuHat

### Changes for analyses
  - mono-V
  - HHbbtautau
  - SM Htautau
  - new Vprime and VprimeHVT analyses


## [WSMaker-07-00-00] - 2017-10-02
Corresponds to VHbb data15+16 analysis
### Last tag on SVN.
### Beginning of Changelog
