A generic How-To for the WSMaker package {#HowTo}
========================================

This attemps to answer the most frequent cases one faces when
setuping a fit model or performing the statistical analysis of
a fit model already setup.

It is based on the real
[SM VHbb ICHEP 2016 analysis](https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/CONFNOTES/ATLAS-CONF-2016-091/),
and uses its configuration and high-level scripting files as an example.

WSMaker twiki page: [WorkspaceMaker](https://twiki.cern.ch/twiki/bin/viewauth/AtlasProtected/WorkspaceMaker)

For any questions, use the mailing list:
mailto:atlas-phys-stat-wsmaker@cern.ch


High-level control
------------------

### How to setup the package ?
 * Checkout
 * Add yourself to setup.sh (for determining the desired analysis script folder)
 * Run: `source setup.sh`
 * Compile the package: `cd build && cmake .. && make -j5`

### How to reproduce the main analysis results ?
After you have everything setup, you are ready to make workspaces and run fits.  You can do 
this manually using the executables that come with WSMaker, but it is much easier to use the 
python scripts that are wrappers for these and do a lot of the nitty gritty configuration for you.  The main example is `scripts/VHbbRun2/launch_default_jobs.py` (python scripts will henceforth be typically referred to by their titles without directory or suffix)

Whatever your method, your workflow will resemble the follwing:

1. Configure your workspace (`src/*_(your_analysis).cpp`)
2. Create or import a workspace
3. Schedule algorithms
4. Unpack results
5. Make plots

#### How to Read and Modify the Main Worker Script
For VHbbRun2, this is `scripts/VHbbRun2/launch_default_jobs.py`  This script is really a wrapper for:

 * `scripts/AnalysisMgr.py` and its derived classes (in charge of configuration—the `configs/*.config` files
  control which regions are included in the fit, as well as configurable parameters) 
 * `scripts/doActions.py` (the `BatchMgr.py` methods `run_(local|lxplus)_batch` pass configuration files to
  a set of algorithms (command line options for `doActions.py`, which itself is a wrapper for the main
  executables)

The main worker script will have the option to define useful parameters.  For VHbbRun2, some of these
are:

 * `channels`: an array of strings with lepton channels; the full bucket is `[‘0’,’1’,’2’,’012’]`
 (each individual sub-channel and the combined; arbitrary combinations are in principle possible)
 * `InputVersion`: the version of inputs to use; same as SplitInputs version, files MUST exist in `inputs/(InputVersion)/13TeV\_(lep)Lepton\_(region)_(var).root`
 * `outversion`: this is the mandatory command line option--helps you label things
 * A bunch of flags: big_switch does all the flags mentioned below 
 * Diboson fits: This is VZ instead of VH--choose an InputVersion with “db” in the name
 (and make sure your inputs are split with mvadiboson)
 * `doExp`: 0 for observed, 1 for asimov (“expected”)



### How and what are actions (workspaces, fits) scheduled ?
Using `launch_default_jobs.py` as a model, we identify the flags for different tasks and also note the `doActions.py` command line options invoked.  See more for specific tasks in **Performing statistical analysis**

### How to publish fit results on a website ?
Setup a directory on lxplus (or anywhere on AFS) with the plots, etc. organized in a readable way and, in that directory, call

	% python /afs/cern.ch/user/a/atlashbb/public/createHtmlOverview.py

* This script is also in the WSMaker package: `macros/webpage/createHtmlOverview.py`
* Plot formats can be converted with: `macros/webpage/convertepstopngpdf.sh`

[Link to webpage with some ICHEP results](https://project-atlashbb-sharepoint.web.cern.ch/project-atlashbb-sharepoint/Run2/VH/)



### How to easily deal with results of batch jobs ?

The output from lxbatch jobs is stored in:
`/afs/cern.ch/work/${USER:0:1}/${USER}/analysis/statistics/batch/`

A useful script to unpack specific results from
the compressed result files is `scripts/getResults.py`.
For example, you can list some contents with (`$version` being the workspace name):

`python scripts/getResults.py list --plots --tables --fccs --NPs --restrict-to fullRes $version`

More example usage can be found in `scripts/VHbbRun2/gather_default_results.sh`.

### etc etc...


Performing statistical analysis
-------------------------------

A statistical analysis is usually composed of two steps:

* create a workspace (WS) from histograms
* run some script using the workspace as input (do a fit, run a limit calculation, ...)

For many cases, one can create a WS on the fly (`-w` option for `doActions.py`),
"link" an existing workspace (`-k`), or run the full commands "by hand".  Below, we give the options "by hand" and in `launch_default_jobs` (with the applicable `doActions` array of options).

### How to modify the regions in a fit?
The regions that enter into your analysis are defined via a class derived from `AnalysisMgr`. 
In your worker script (e.g. `launch_default_jobs`), you will find a function call to something like 
`Mgr.append_regions()` where you can specify which lepton channels to include, the 2 and 1 tag variables, etc.

For everything that is not an arugment, you specify region specifics (e.g. which pTV and nJet bins
in a given subchannel) in a script like `scripts/VHbbRun2/AnalysisMgr_VHbbRun2.py` where the modifications to make should be fairly clearly named.

### How to make a simple workspace?

Workspaces are created by the MakeWorkspace executable from histograms and a config file.
You can

1. Run `MakeWorkspace` yourself or
2. Set `createSimpleWorkspace=True` in `launch_default_jobs`.  This is just `doActions` with `-w`.

Creates a workspace and does nothing else.  This can be co-opted to work exclusively for making workspaces for postfit plots
 (Nicolas has kindly made DefaultFitConfig work for this purpose, and, hence, turning this option on will set DefaultFitConfig
 (normally False) to True).

### How to run simple fit diagnostics including pulls?

Fit diagnostics are performed by the script `FitCrossCheckForLimits.C` (FCC), using a workspace as input.
A python wrapper exists as `scripts/runFitCrossCheck.py`, which can be called manually or using `scripts/doActions.py`. You can

1. Call FCC by hand or `--fcc, '2,7,9'...` and call makeReducedDiagPlots by hand or `-m, '2,7,9'`
2. Set `runPulls=True` in `launch_default_jobs`; this is equivalent to `doActions.py` with options

	["--fcc", "2,5,7,9@{MassPoint}", "-m", "2,5,7,9", "-p", "0,2,3@{MassPoint}", "-t", "0,1@{MassPoint}"]

 * The option `--fcc` makes the actual FCC file (2,5,7,9 is (global unconditional, global conditional mu=1; then Asimov))
DON’T USE OPTION 2 IF YOU’RE SUPPOSED TO BE BLINDED  
 * The option `-m` is makeReducedDiagPlots (correlations, pulls, etc.)
 * The option `-p` makes pre (0) and post (2 is unconditional, 3 is conditional) fit plots
 * The option `-t` makes the yield tables (run `-a` for the ratio tables)—to get postfit yields,
(user tip: you may need to run again because some scheduled algorithms fail for these on batch at slightly higher 
rates than others)

If on SLURM or any other batch system requiring manual allocation of memory:
 schedule A LOT of memory for this (bad things (i.e. premature failure) have been known to happen)

### How to make readable fit comparisons ?

A fit can have many (nuisance-) parameters.
The script `comparePulls.py` can be used to compare all parameters of the fits in a graphic way. You can run:

        % python scripts/comparePulls.py -w wsName [wsName1 ...] -a fit type
		
The color correspondence of colored pulls to workspaces: black, red, blue, magenta, ... The '-l' option can be used to add legends. 

If you provide just a single WS name, the script does the data (black) to Asimov (red) comparison.

### How to check that a fit performed well ?

You can have a look at the log files from FCC in 'output/$(ws_name_usu_w_limits)/logs/output_x.log'.
In particular, you can grep for the fit status: `grep Status output/$WSName/logs/output_x.log`
This should give `Status : MINIMIZE=0 HESSE=0`, otherwise the fit might not have converged.

One particular issue arises in complex fits with strong correlations: the Hesse matrix might fail to be inverted, even if `HESSE=0` is printed afterwards. Often this can show as artificially reduced NP uncertainties. This can be spotted in the log file by comparing the uncertainties before and after Hesse. There is an script to check for this (`scripts/checkHesse.sh`), but it is not functional atm.


### How to compute a limit ?

Limits are calculated by `runAsymptoticsCLs.C` using a workspace as input.
A python wrapper exists as `scripts/getLimit.py`.
You can

1. Call by hand `getLimit.py` or
2. Set `runLimits=True` This is the same as `doActions` with:

		["-l", doExp+",{MassPoint}"] #doExp is 0 or 1

Results are stored in `output/(ws_name_usu_w_limits)/logs/output_getLimit_(mass).log`

 * Result is at the end of the log
 * Should also be tucked away in the workspace

### How to compute significances?

Limits are calculated by `runSig.C` using a workspace as input.
A python wrapper exists as `scripts/getSig.py`.
You can

1. Call by hand `getSig.py` or
2. Set `runP0=True` in `launch_default_jobs`, which is the same as `doActions` with:

	     ["-s", doExp+",{MassPoint}"]

Results are stored in `output/(ws_name_usu_w_sigs)/logs/output_getSig_(mass).log`

* Result is at the end of the log (look for "Observed significance: " for observe, and "Median significance: " for Asimov)

### How to run a breakdown of the signal strength?

A breakdown of the signal strength (POI) uncertainties is performed by script `newGetMuHat.C`
using a workspace as input.
A python wrapper exists as `scripts/runMuHat.py`.

The `runBreakdown` flag in `launch_default_jobs` will run the standard breakdown and corresponds to `doActions` with:

	["-u", doExp+",{MassPoint}"]

If you need to run a non-standard breakdown, the command is

	% python scripts/runMuHat.py [ws] [2 for asimov with mu=mu_asimov, 1 for asimov (unconditional), 0 for observed] [mode] [mass] [mu_asimov]

The results will be stored `plots/(ws_name)/breakdown/muHatTable_(ws_name_usu_w_breakdown)_mode(1 | whatever)_Asimov(0|1)_(poi_name).(tex|txt)`

The primary modes for the ICHEP 2016 SMVHbb result are as follows 
(you can find all of them in newGetMuHat.C; Total, DataStat, FullSyst always included):

 * Mode 1: default: Total, DataStat, FullSyst, Floating normalizations, All normalizations, All but normalizations, Jets MET, BTag, Leptons, Luminosity, Diboson, Zjets, Wjets, Model ttbar, Model Single Top, Model Multi Jet, Signal Systematics, MC stat
 * Mode 5 (default): Total, DataStat, FullSyst, Top shape systematics
 * Mode 5 (deprecated): Total, DataStat, Fully Syst, MC stat
 * Mode 6: Total, Datastat, FullSyst
 
### How to make pre/postfit plots ?
There are two ways you can do this---either use the standard script for small jobs (recomended) or the VHbbRun2 automatic script
	
	% python scripts/doPlotFromWS.py -s [for sum plots] -m <mass> -p <plotmode> -f <fitresultsName> <workspaceName>
Keep in mind you MUST use workspaces created with DefaultFitConfig True to get sensible plots! 

 `-p`: Comma-separated list of plots to create (the comma separated mode has not been validated in Run 2; running in sequence
is advised):

 * 0: prefit plots
 * 1: bkg-only postfit plots
 * 2: s+b postfit plots (the big shebang, don’t touch until the end)
 * 3: s+b conditional postfit plots
The -f is the directory where FitCrossChecks.root may be found; this usually looks like `output/(ws_name_usu_w_sigs)/fccs/FitCrossChecks.root`; normally, this will be a combined fit result.  The mass defaults to 125, so you probably don’t need to touch it.

For sum plots, you’ll have to modify `make_sum_plots` in `scripts/VHbbRun2/analysisPlottingConfig.py`; right now (2016-08-08),
 we’ve summed pTV (no need to split distributions by pTV) and mBB (all regions specifically for bkg subtraction plots):
 
       #merge pTV into one plot                                                                                                                                                                                                             
        for nJet in ['2','3']:
            func("Region_BMin0_T2_L2_J{}_Y2015_distpTV_DSR".format(nJet), rt=['_distpTV',"_L2", "_J{}".format(nJet)],ea=[])
        # mBB for sums                                                                                                                                                                                                                       
        func("Region_T2_Y2015_distmBB_DSR", rt=['_distmBB'],ea=[])
        func("Region_T2_Y2015_distmUnBB_DSR", rt=['_distmUnBB'],ea=[])
        func("Region_T2_Y2015_distmCorrBB_DSR", rt=['_distmCorrBB'],ea=[])

The other option is to use:
	
	% python scripts/VHbbRun2/postfit_plots.py -h (this will tell you how it works)
This assumes simple workspaces and FCCs have been made following the `launch_default_jobs.py` syntax
Top of the script:
***********************************
	VZ=False
	fcc_tag ='flumi-puw' # this is the 'outversion' (following the convention of launch_default_jobs.py) attached to the FCC we use as the fit result in making the postfit plots                                                               
	fcc_version='SMVH_mva_v14b' # this is the 'InputVersion' (following the convention of launch_default_jobs.py and inputConfigs) of the FCC we use as the fit result in making the postfit plots                                              
	fcc_mva='mva' # mva variable used in the FCC                                                                                                                                                                                                
	dist_tag='ws2' # this is the 'outversion' attached to the workspaces with distributions used as the basis of the postfit plots (i.e. the prefit distributions)                                                                              d
	ist_version='SMVH_mva_v14b' # 'InputVersion' of the distribution workspaces                                                                                                                                                                ***********************************
Turning on VZ will change the stuff for inputs; double check that the VZ setting here matches the opposite of `vh_fit` or whatever at the top of analysisPlottingConfig.py
The dictionaries corresponding to full, main, and back (full=main+back or at least should) are for what was available in ICHEP 2016 inputs.  The main distributions are the major variables per channel that really drive the MVA.  Right now (2016-08-08), supported options are:

* `-f, --full `        Use the full hash
*  `-m, --main `        Use the main hash
*  `-b, --back`         Use the back hash
*  `-l LEP, --lep LEP`  Which lep case to do
* `-o, --override`     Overwrite plots
*  `-s, --sums `        Just do the special S/B sub mBB plots
*  `-c, --conditional`  Do conditional postfit plots
* `--postfit`          Just do the postfit plots (skip prefit)

There is also an option which allows to save postfit distributions and uncertainties
for all processes in all channels: set `save_h = true` within scripts/doPlotFromWS.py .

### How to make pre/postfit tables ?
	% python scripts/makeTables.py -t2 [combined ws name]
 * Results are stored in `output/(ws_name)/tables/postfit/Yields_(Global|Asimov)Fit_(un)?conditionnal_mu(mu).tex`

To produce ratio tables between a workspace1 and a workspace2 you need to run:

	% python scripts/makeRatioTables.py -t 5 workspacename1 workspacename2

The `-t 5` option corresponds to the conditional, mu=1 data fit, but you have a whole bunch of possibilities you can check out looking at the macro.

When `workspacename1 == workspacename2`, then the SF are the post/pre-fit ones.

### How to rank the NPs?
You can

1. Call by hand `runNPranking`
2. Set `runRanks=True` in `launch_default_jobs` (same as `doActions` with:
	
		  ['-r','{{MassPoint}},{0}’.format(doExp)]

This is typically done in multiple jobs (how many will depend on the specifics of your batch stystem).  Results are stored in

	output/(ws_name_with_job\*of*_and_rank)_(pulls | breakdown_add)/root-files

If you run use `Batch.run_lxplus_batch`, you'll have to use `getResults.py` to get results in this way.  You can also do this manually

Note: the only python scripts that explicitly accept the jobXofY splitting are `scripts/makeNPrankPlots.py`, `scripts/mergeFCCToys.py`, and `scripts/mergeNLLscans.py`

#### How to plot the results of NP ranking?
The command you will use is:

	% python scripts/makeNPranks.py [ws_name_with_job*of(N_jobs) to job(N_jobs)of(N_jobs)] > sensible log file name (e.g. output/(ws_name_usu_w_sigs)/logs/output_rankplts.txt)

The standard ranking script produces workspaces with the usual scripts/BatchMgr.py naming convention, the usual workspace name with
job[0--N-1]of[N], where N is the number of jobs you've configured.  The workspace you call for the ranking script is NofN (which
should not exist---this pulls the results in the correct way).  Some points:

 * The output is the full ranking in nicely formatted text; this is why you typically pipe the output to a log since your plot only gives the you first 25 or so NPs (you can set how many in macrs/drawPlot_pulls.C)
 * Things you’ve also had to set in the macro:
 * prefit impact bars: (true for understanding, false for papers)
 * Energy and Luminosity: global variables at the top
 * NP renaming this is at the bottom of the file in TString translateNPname(TString internalName, bool isMVA): 
the argument is the automatic name, the return is meant to be a human readable TLatex type thing
 * ATLAS label: "\nInternal" for starter and then "\nPreliminary" (this is NOT affected by the analysisPlottingConfig.py 
for these plots, so you have to do it again * note that you modified AtlasLabels.C to accept new lines)
 * Other labels: just search for the obvious TLatex text and modify

#### How to make SoB Plots?
	% python scripts/plotSoB.py [ws_name_for_combined_fit] 2

You might have to fiddle the limits (which are set by hand):

        self.cfg.set_y_range(first_h, 3,  1.0, the_max, True, self.properties)
in:
    
    def make_SoB_plot(self, can_name = "",do_ratio = True, Ratioybounds=(0.4, 1.6), ratioType = 0):
    (plotMaker.py)

#### How to make "Nice Plots?"
	% python scripts/VHbbRun2/Nice_XXX.py
These are the mu summary plots, and you have to put the numbers in by hand.  Arguments 2--8 in the lines aren’t used,
 the ones after are muhat, total error +/-, stat error +/-.  Pull new numbers from the breakdowns (first two lines)
### etc etc...


Creating workspaces
-------------------

### How to add a new region to a fit ?

There are two steps for defining a region in MakeWorkspace:

* Parsing  of the config file and building the internal representation (PropertiesSet).
* Using the internal representation to create the filename to use. This part is in inputshandler_xxx.

Each region corresponds to an input file.
MakeWorkspace prints the filename which tried to be read, which can be used for debugging.

Each input file is required to contain a 'data' histogram.

(TODO:
Need to talk about naming conventions a little bit
Then about adding what is needed in the python high level scripts
)

### How to adjust the binning ?
`binning_xxx.cpp`
Modify BinningTool_xxx::getCategoryBinning.
Modify BinningTool_xxx::changeRange if you want to change the range as well.
Recompile (make) the WSMaker.

Another way is to set "ForceBinning 2" in configs/yourConfiguration.config.
This overwrites the binning that is set in src/binning_xxx.cpp.

The binning can depend on the category. For example, you can use
Category(Property::<prop>) where <prop> can be "dist" (for distribution, like mBB, MET etc.)
or "nJet" etc. Or you simple use Category::name() for specific binning choices.

Particular binnings are chosen as a vector<int> in getCategoryBinning.
Here indices of the input histogram bins are used to define new bin boundaries,
starting at the upper edge. For instance if the input histogram has 500 equidistant
bins between 1 and 500 GeV, then {500, 200, 100, 1} would result in three new bins
with upper boundaries at 100, 200 and 500 GeV.

### How to control systematics ?

An example of defining a list of systematic uncertainties can be found in
`src/systematiclistsbuilder_vhbbrun2.cpp`.

`sampleNormSys("<proc>",delta)` introduces a normalisation uncertainty delta
for the background <proc>.

`normFact(<name>,{"procA", "procB", ...}, 1.0, 0.0, 100.0)` introduces an
unconstrained normalisation factor for the processes "procA", "procB", ...
There is only one such scale factor for all of these processes (100% correlation).

`normSys("name", <size>, <SysConfig>)` introduces additional uncertainties
on processes chosen within the constructor of the SysConfig argument.
This option can be used in order to decorrelate process normalisations
between different channels to an extent defined by <size>.
Examples of this option can be found e.g. in `src/systematiclistsbuilder_vhbbrun2.cpp`.
It is helpful to cross-check the outcome by explicitly checking the resulting xml
files from which the workspace is built (see output/<workspace name>/xml) in order
to make sure that the workspace truly implements the desired model.

`m_histoSysts.emplace( <"SystName"> , SysConfig{...});` introduces a shape variation.
The input root files must contain variations with the name tag "SystName" accordingly.
Via the SysConfig argument, different implementations can be chosen.
For instance, it is possible to choose a `shapeonly` variation, so that the input
systematics histograms are renormalised according to the nominal event yield.
Whether this is the right choice or not depends on the meaning of the input
systematic histograms.

(TODO: add more info, probably subdivide into smaller chunks)
#### How to de-correlate different regions in WSMaker?
Everything related to systematics correlation schemes is handled through [SysConfig objects](https://nmorange.web.cern.ch/nmorange/WSMaker/html/structSysConfig.html#a520f1edb148522accd6b320a4dc4e6f8).
For example, if you want to decorrelate in number of jets for all categories, you can change the code in `src/systematiclistsbuilder_vhbbrun2.cpp` to the following:
`SysConfig{T::shape, S::noSmooth, Sym::noSym}.applyTo("ttbar").decorrIn({ (P::nLep==2),(P::nLep==1)&&(P::binMin==75)}).decorr(P::nJet)`
Then after you run `launch_default_jobs.py`, you can see variables like `alpha_SysTTbarPTV_J2` in the ranking plot, which indicates that 2-jet and 3-jet region are de-correlated.

### How to scale arbitrarily a sample to perform e.g extrapolations to high lumi ?

In your list of systematics (see above) you can add:

`normFact("lumirescale", {"MC"}, factor, -10, 10, true);`

Here, factor is an arbitrary scale for all MC samples.

### What is "smoothing of systematics" and how to control it ?

Smoothing of systematic variations aims to alleviate statistical fluctuations
in experimental uncertainties (bin migrations).

The smoothing (`getLocalExtremaBinning`)
is called from `sampleincategory.cpp`
and the algorithm is defined `binning.cpp`.

### How can I control that the creation of my workspace went well ?

Basic control plots in can be found in output/(workspace_name)/plots.
They consists of stacked plots of the backround + signal, etc.
In the configurution more detailed plots can requested:
* doShapePlots: create plot of the shapes of systematic variations (can be many!)
* doSystsPlots: create summary plots of the impact / pruning of systematic variations

The input to the actual workspace making for `hist2workspace` can be found in
output/(workspace_name)/xml
and can be investigated manually.

### What is merging of samples, and why ?

Samples, which share one floating scale factor (or have no scale factor) can be merged. In this case, the effect of nuisance parameters is propagated the sum of these samples. This improves the fit convergence.

### Why are some systematics pruned away ?

Systematics with negligible effect on the measurement
can be removed to improve the fit convergence.

Pruning consists of several steps,
which are called in `src/engine.cpp`
(containing the main routine of `MakeWorkspace`).
The various steps are defined in `sampleincategory.cpp`.
The latter class involves also another pruning step
in its function `addSyst` where normalisation
variations are required to be larger than 1e-3.

### etc etc...


Adding a new analysis in the package
------------------------------------

### The necessary classes
The analysis-level code is embedded in 6 classes, that have to comply
to some interface. They are completely independent bricks. If an existing
subclass already meets your needs, don't reimplement it, just use it.
(see `analysishandler` below).  This is esspecially true of `regionnamesparser_xxx` 
and `inputshandler_xxx`, where you can use the default if you follow the normal 
naming convention.

#### `samplesbuilder_xxx`: list of data, signal, background samples to be loaded
#### `systematiclistsbuilder_xxx`: list of histogram-based and user-defined systematics
#### `binning_xxx`:ranges and rebinning of the input hostograms
#### `regionnamesparser_xxx`: convert the defintion of regions into a PropertySet
#### `inputshandler_xxx`: convert the PropertySet into the file name to be read
#### `regiontracker_xxx`: keep track of what regions are being used in the fit

### Code changes
#### `samplesbuilder_xxx`, `systematiclistsbuilder_xxx`, `binning_xxx`
- Copy from one of existing analyses and update to your list of samples and systematics

#### `configuration`
- Add a new enum for your analysis to `AnalysisType`
- Add the mapping bettwen the name of the analysis and the type enum to `AnalysesTypes::names`

#### `analysishandler`
- Add the necessary include statements for the new `xxx` versions of your analysis packages
- Create a new `using` statement defining an alias for the `Analysis_Impl` template for your analysis and which `xxx` version of the analysis packages it uses
- Add a new `case` to the `Configuration::analysisType())` switch statement to construct your analysis using the `Analysis_Impl` name

#### `Makefile`
- Add object files (.o) for your new `xxx` classes to `m_wOBJ` list

### High level scripting and automation

You should create a subdirectory inside the `scripts` directory for the setup for your analysis.  
The subdirectory should be named the same as you called your analysis above.  You should then 
update `setup.sh` to map your username to the correct `ANALYSISTYPE` so python files are imported 
from the correct path

#### `AnalysisMgr_xxx.py`
- This controls the regions you want to fit, whcih are specificed in `set_regions`.  These are the 
  names of the root files after splitting wit the .root extension removed.    
- Also the Analysis name should be updated here

#### `Analysis_XX.py`

- This is the main driver for running tasks like limits, pulls, rankings etc.
- It should import `AnalysisMgr_xxx.py` and create the config files based on the input and output version
- It contains a list of the tasks to apply, the possibilities for each are in `doActions.py`

#### `analysisPlottingConfig.py`

- This class holds all analysis-dependent code needed in the various python scripts.
- Please use the version from VHbbRun2 has a starting point.
- It then controls:
 * How are NP split in many subplots by `comparePulls` and `makeReducedDiagPlots`
 * How postfit plots are made (samples, colors, order, and many small functions to override
 to set many small things, like blinding)
 * How postfit tables are made (order)

This class is unfortunately not super well documented yet. Some documentation strings
exist in `scripts/plottingConfig.py`, but many are cryptic.
