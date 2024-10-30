<<<<<<< HEAD

WSMaker: the HSG5 package for statistical analysis {#mainpage}
==================================================

Setup
-----

This is the "core" WSMaker. It does not contain any analysis-specific files any longer.

Clone an existing analysis and have this package included as a dependency (submodule)

For instance for VHbb

    git clone --recursive ssh://git@gitlab.cern.ch:7999/atlas-physics/higgs/hbb/WSMaker_VHbb.git

### Todo list and issues

 They are collected on gitlab: 
 https://gitlab.cern.ch/atlas-physics/higgs/hbb/WSMaker/issues

 Please report bugs, give feedback on issues, and consider participating in the
 shared development of the package by working on some of them. Improving the
 documentation is one of the key aspects !

### Development model

The master should be used to do your analysis.
To make code changes or develop new features, use merge requests (no direct push to master). So, develop features in branches of the main repo (preferred) or in forks of the repo (allowed), then open merge requests.
If you get "Developer" access (required to create a branch actually), you can approve merge requests.

When you develop code specific to your own analysis, feel free to self-approve (it gives you a chance to glance at the diff one last time).
When you change something  which may affect other analyses, seek approval from others. No formal procedure is in place, but discussion over new features is always helpful, even in hard pressing times.`

### Template Analysis helper

As a complement to the information discussed in this README, a template analysis is available at:
https://gitlab.cern.ch/atlas-physics/higgs/hbb/wsmaker_templateanalysis
It provides a working dummy example of an analysis using WSMaker.

It is used it as an illustration of how to build your own analysis (see the template analysis README). You'll also find there some details on certain aspects of the code useful when it comes to debugging you analysis code.

It can also serve as a working example to train new commers.




Philosophy
----------

This package performs the statistical analysis for the VHbb analysis.

It has two quite independent parts:
 * It creates workspaces from input files (ROOT files filled with histograms)
 * It performs fits, computes limits/p0, makes postfit plots, and performs all
 kinds of profile likelihood and fit checks.

This page describes some basic principles and features of the package. For practical
advice about performing some actions, go to the [How-To page](HowTo.md)

Creation of workspaces
----------------------

VH workspaces use MC-based PDF everywhere, and so are based on the HistFactory tool.
However, given the complexity of the analysis, a heavy treatment is performed on
the inputs prior to the call to `hist2workspace`

### Requirements
The basic role of WSMaker is to take input files, write corresponding XML files,
and call `hist2workspace`.

It actually addresses a list of complex requirements:

 * Easy configuration of the analysis regions that should enter the fit model
 * Even for a super complex fit model, in terms of regions involved, with
 different discriminant distributions used (BDT, Mjj, MV1c)
 * Easy creation of workspaces with other distributions in the same analysis
 regions, to make postfit plots of any distribution
 * Use of complex rebinning schemes, to optimize fit performance while keeping
 the total number of bins in the fit model as low as possible
 * Smoothing of energy scale and energy resolution systematics, to avoid
 unphysical shapes in the likelihood
 * Various flavours of pruning of systematics, to keep the fit model as lightweight
 as possible while keeping the full precision of the results
 * Configure as simply as possible the systematics in the fit model:
   + Restrict the application of systematics to some analysis regions or some
   samples
   + Add user-defined flat systematics on some samples, in some regions
   + Allow for (sometimes complex) decorrelations of systematics between regions
   or samples
   + Easy creation of alternate workspaces with other decorrelations, to investigate
   the fit.
 * Can look for Higgs peak as well as diboson VZ peak, or both at the same time
 (choice of parameter of interest)
 * Optimization of the fit model through the merging of samples that can be fit
 together, while keeping the model mathematically equivalent to the fully split
 mode.

### Concepts

Below are listed some key concepts around which the code is built. Understanding
these concepts gives an overview of the main classes in the code, and of their
relations.

#### Splitting of input files

This is now analysis-dependent

##### Fetching Input Files
The executable for this is
	
	 SplitInputs -r (Run2 | Run1) -indir ($inputs) -v (provide this!)

Run2 is the default, and the input directory default is in SplitInputs.C, where you can modify the default to wherever you store your inputs files.

	TString inDir = "root://eosatlas//eos/atlas/atlascerngroupdisk/phys-higgs/HSG5/Run1Paper/“;// 
in int main(int arg, char* argv[]) this has been export’d to $inputs
src/splitter_Run2.cpp

A version must be specified.  After splitting inputs, root files are created of the form

	% inputs/(version)/(Energy)_(Zero|One|Two)Lepton_(ntag)tag(njet)jet_(ptv region)_(SR|topemucr|etc)_(variable).root

#### Data structure
To easily perform the actions required on the input histograms, one needs an internal
representation of the fit model.

The code uses a "matrix" representation, where the rows
are the samples used in the analysis (class `Sample`), and the columns are the
analysis regions (class `Category`). The cells are then `SampleInCategory`, where
each one then holds one nominal histogram. A third dimension arises in each cell,
which is made of all the systematic variations attached to the nominal histogram.

Depending on the task that needs be performed, an access through rows (browsing
samples) or through columns (browsing categories) will be made.

The `SampleHandler` manages the rows, while `CategoryHandler` manages the columns.

#### Keywords
In order to merge similar samples, or perform decorrelations of systematics for
groups of samples, it is useful to be able to easily refer to a given group of
samples.

In `SampleHandler`, keywords can be attached to samples, for instance the keyword
`Zjets` is attached to Zl, Zcl, Zcc, Zbc and Zbb samples.

This mechanism fulfills the requirement mentioned above.

#### %Properties

#### %Configuration of systematics

### Workflow

### Further documentation
The header files themselves are documented usign Doxygen syntax. All the details
can be found there, as well as lists of allowed configuration flags, and explanations
of the configuration syntax when it is complex.


Fits and postfit scripts
------------------------

After you have everything setup, you are ready to make workspaces and run fits.  You can do 
this manually using the executables that come with WSMaker, but it is much easier to use the 
python scripts that are wrappers for these and do a lot of the nitty gritty configuration for you.

In the following, the VHbbRun2 analysis will be taken as the model, but other analyses have
their own analagous scripts, and the VHbbRun2 workflow can be used as an example if none exist
for your particular anlaysis.

Whatever your method, your workflow will resemble the follwing:

1. Configure your workspace (above)
2. Create or import a workspace
3. Schedule algorithms
4. Unpack results
5. Make plots

### Defining Regions
The regions that enter into your analysis are defined via a class derived from scripts/AnalysisMgr. 
In your worker script (more on this later), you will find a function call to something like 
Mgr.append_regions() where you can specify which lepton channels to include, the 2 and 1 tag variables, etc.
For everything that is not an arugment, you specify region specifics (e.g. which pTV and nJet bins
in a given subchannel) in a script like scripts/VHbbRun2/AnalysisMgr_VHbbRun2.py

### The Main Worker Script
For VHbbRun2, this is `scripts/VHbbRun2/launch_default_jobs.py`  This script is really a wrapper for:

 * `scripts/AnalysisMgr.py` and its derived classes (in charge of configuration—the `configs/*.config` files
    control which regions are included in the fit, as well as configurable parameters) 
 * `scripts/doActions.py` (the `BatchMgr.py` methods `run_(local|lxplus)_batch` pass configuration files to
    a set of algorithms (command line options for doActions.py, which itself is a wrapper for the main
    executables)

The main worker script will have the option to define useful parameters.  For VHbbRun2, some of these
are:

 * channels: an array of strings with lepton channels; the full bucket is `[‘0’,’1’,’2’,’012’]`
 (each individual sub-channel and the combined; arbitrary combinations are in principle possible)
 * InputVersion: the version of inputs to use; same as SplitInputs version, files MUST exist in `inputs/(InputVersion)/13TeV_(lep)Lepton_(region)_(var).root`
 * outversion: this is the mandatory command line option--helps you label things
 * A bunch of flags: `big_switch` does all the flags mentioned below 
 * `Diboson fits`: This is VZ instead of VH--choose an InputVersion with “db” in the name
 (and make sure your inputs are split with mvadiboson)
 * `doExp`: 0 for observed, 1 for asimov (“expected”)

We now describe some of the things you might want to do with the worker script.  Note that the flags 
schedule things with scripts/doActions.py.  In the default versions, `-w` (make the workspace) is called 
for all of these.  If you want to work off an existing workspace, you'll need to properly format the `-k`
option.  The arrays for command line options in what follows will omit these for the sake of brevity.

#### Running FitsCrossChecks (`runPulls = True`)

runPulls is the flag; what you’re doing is  calling sripts/doActions.py with options

	["--fcc", "2,5,7,9@{MassPoint}", "-m", "2,5,7,9", "-p", "0,2,3@{MassPoint}", "-t", "0,1@{MassPoint}"]

 * `--fcc` makes the actual FCC file (2,5,7,9 is (global unconditional, global conditional mu=1; then Asimov))
DON’T USE OPTION 2 IF YOU’RE SUPPOSED TO BE BLINDED  
 * `-m` is makeReducedDiagPlots (correlations, pulls, etc.)
 * `-p` makes pre (0) and post (2 is unconditional, 3 is conditional) fit plots
 * `-t` makes the yield tables (run `-a` for the ratio tables)—to get postfit yields,
(user tip: you may need to run again because some scheduled algorithms fail for these on batch at slightly higher 
rates than others)

If on SLURM or any other batch system requiring manual allocation of memory:
 schedule A LOT of memory for this (bad things (i.e. premature failure) have been known to happen)


#### Simple Workspaces (`createSimpleWorkspace=True`)
Creates a workspace and does nothing else.  This can be co-opted to work exclusively for making workspaces for postfit plots
 (Nicolas has kindly made DefaultFitConfig work for this purpose, and, hence, turning this option on will set DefaultFitConfig
 (normally False) to True).

#### Breakdowns on mu (`runBreakdown=True`)
The flag will run the standard breakdown

	["-u", doExp+",{MassPoint}"]

If you need to run a non-standard breakdown, the command is

	% python scripts/runMuHat.py [ws] [2 for asimov with mu=mu_asimov, 1 for asimov (unconditional), 0 for observed] [mode] [mass] [mu_asimov]

The results will be stored `output/(ws_name)/plots/breakdown/muHatTable_(ws_name_usu_w_breakdown)_mode(1 | whatever)_Asimov(0|1)_(poi_name).(tex|txt)`

The primary modes for the ICHEP 2016 SMVHbb result are as follows 
(you can find all of them in newGetMuHat.C; Total, DataStat, FullSyst always included):

 * Mode 1: default: Total, DataStat, FullSyst, Floating normalizations, All normalizations, All but normalizations, Jets MET, BTag, Leptons, Luminosity, Diboson, Zjets, Wjets, Model ttbar, Model Single Top, Model Multi Jet, Signal Systematics, MC stat
 * Mode 5 (default): Total, DataStat, FullSyst, Top shape systematics
 * Mode 5 (deprecated): Total, DataStat, Fully Syst, MC stat
 * Mode 6: Total, Datastat, FullSyst

#### Ranks (`runRanks=True`)
	  ['-r','{{MassPoint}},{0}’.format(doExp)]
 This is typically done in multiple jobs (how many will depend on the specifics of your batch stystem).  Results are stored in

	output/(ws_name_with_job\*of*_and_rank)_(pulls | breakdown_add)/root-files

If you run use `Batch.run_lxplus_batch`, you'll have to use `getResults.py` to get results in this way.  You can also do this manually

Note: the only python scripts that explicitly accept the jobXofY splitting are `scripts/makeNPrankPlots.py`, `scripts/mergeFCCToys.py`, and `scripts/mergeNLLscans.py`
      
#### Limits (`runLimits=True`)
	  ["-l", doExp+",{MassPoint}"]
 Results are stored in `output/(ws_name_usu_w_limits)/logs/output_getLimit_(mass).log`
 * Result is at the end of the log
 * Should also be tucked away in the workspace

#### Significances (p0, runP0=True)
      ["-s", doExp+",{MassPoint}"]
 Results are stored in `output/(ws_name_usu_w_sigs)/logs/output_getSig_(mass).log`
 * Result is at the end of the log (look for "Observed significance: " for observe, and "Median significance: " for Asimov)

#### Yield and Ratio Tables
	% python scripts/makeTables.py -t2 [combined ws name]
 * Results are stored in `output/(ws_name)/tables/postfit/Yields_(Global|Asimov)Fit_(un)?conditionnal_mu(mu).tex`

To produce ratio tables between a workspace1 and a workspace2 you need to run:
% python scripts/makeRatioTables.py -t 5 workspacename1 workspacename2

The `-t 5` option corresponds to the conditional, mu=1 data fit, but you have a whole bunch of possibilities you can check out looking at the macro.

When `workspacename1 == workspacename2`, then the SF are the post/pre-fit ones.

#### Workspace reparametrisation
Sometimes it is useful to change the parameters of interest of a workspace after its creation. Typical examples are interpretations of measurements within the Kappa framework or in an effective field theory. The reparametrisation is analysis-dependent and handled by the `PostProcessingTool`. A template is defined in `src/postprocessing.cpp`. An analysis wishing to perform some postprocessing of a workspace is required to implement a class derived from this template.

As an example, the [boosted](https://gitlab.cern.ch/atlas-physics/higgs/hbb/wsmaker_boostedvhbb/-/blob/master/src/postprocessing_eft_vhbbrun2.cpp) and [resolved](https://gitlab.cern.ch/atlas-physics/higgs/hbb/WSMaker_VHbb/-/blob/master/src/postprocessing_eft_vhbbrun2.cpp) VHbb analyses published in 2020 use postprocessing to reparametrise an STXS workspace in terms of Wilson coefficients of SMEFT operators.

#### Likelihood scans
It is often necessary to evaluate the shape of the likelihood for a certain range of the parameters of interest, e.g. in the context of a Kappa- or EFT interpretation. `LikelihoodLandscape.C` performs this evaluation in a parallelised way. It is accessible with `doActions.py --nll_landscape`.

### Plots

#### Ranking Plots 
The command you will use is:

	% python scripts/makeNPranks.py [ws_name_with_job*of(N_jobs) to job(N_jobs)of(N_jobs)] > sensible log file name (e.g. output/(ws_name)/logs/rankplts.txt)

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

#### Pull Comparisons
The `comparePulls.py` script plots the nuisance parameter pulls from different workspaces. Usage below:

	% python scripts/comparePulls.py -w wsName [wsName1 ...] -a fit type
Given a single workspace name it will plot the pulls for the fit type provided and for its data/Asimov counterpart

        % python scripts/comparePulls.py -w wsNamev1 wsNamev2 -a 4
Given a list of workspace names and fit type it will plot the pulls for the different workspaces
        
        % python scripts/comparePulls.py -w wsName{0} -v v1 v2 -a 4
Given a base workspace name (version wildcarding with `{0}`) and a few versions it will plot the pulls for the different workspace versions

        % python scripts/comparePulls.py -w wsNamev1 wsNamev2  -a 4 -l legWS1 legWS2
 Attributes a legend for each comparison case

 Other options are:
  * `-s` or `--special`: List of patterns to create a special plot with only the NPs matching the patterns in the list
  * `-p` or `--plotdir`: Output plot directory 


#### Decorations
For the following, modify scripts/VHbbRun2/`analysisPlottingConfig.py`
`vh_fit` flag to toggle which type of fit you’re doing for proper display
`self.ATLAS_suffix` for ATLAS “Internal,” “Simulation,” “Preliminary”
`get_run_info` for lumi

#### Postfit Plots
There are three ways you can do this---either use the standard script for small jobs (recomended) or the VHbbRun2 automatic script
	
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

The second option is to use:
	
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

The third option is to use: (EPS2017 analysis, further question changqiao.li@cern.ch)
	
	% source scripts/VHbbRun2/parallelPostFit.sh (it is submitting the standard script but parallelly)
This assumes simple workspaces and FCCs have been made following the `launch_default_jobs.py` syntax like the second option, doPostFit = True to generate the simple workspaces and also:
* generate CBA mBB simple workspaces: vs2tag = ['mBB'] and doCutBase = True
* generate MVA simple workspaces: vs2tag = ['mva'] and doCutBase = False
* generate VHbb simple workspaces: doDiboson = False
* generate VZbb simple workspaces: doDiboson = True

In parallelPostFit.sh:

* FitSource          the FCC we use as the fit result in making the postfit plots (should be the name of the corresponding ws)
* ConditionCode      used with grep to identify the workspaces to generate the postfit plots
* CollectionDir      the folder to collection the postfit plots
* doCollection       the trigger to switch on or off the collection functiom

More one needs to pay attention on in scripts/VHbbRun2/analysisPlottingConfig.py:
* vh_fit=True        True means fit regarding VHbb as signal, otherwise VZbb as signal
* vh_cba=False       True means fit on the mBB spectrum, otherwise on mva, will affect the scale factors for the dashed signal lines shown on the plots

#### SoB Plots
	% python scripts/plotSoB.py [ws_name_for_combined_fit] 2

You might have to fiddle the limits (which are set by hand):

        self.cfg.set_y_range(first_h, 3,  1.0, the_max, True, self.properties)
in:
    
    def make_SoB_plot(self, can_name = "",do_ratio = True, Ratioybounds=(0.4, 1.6), ratioType = 0):
    (plotMaker.py)

#### Nice Plots
	% python scripts/VHbbRun2/Nice_XXX.py
These are the mu summary plots, and you have to put the numbers in by hand.  Arguments 2--8 in the lines aren’t used,
 the ones after are muhat, total error +/-, stat error +/-.  Pull new numbers from the breakdowns (first two lines)

#### Plots of likelihood profile

* To make plots of the shape of the likelihood as a function of the parameters of interest (1D profile plots and 2D contour plots are supported), use `scripts/plotLikelihoodLandscape.py`. Also accessible via `doActions.py --nll_plots`.

* To compare the shapes of two (or more) likelihood scans to aid in diagnostics: `scripts/compareLikelihoodLandscapes.py`.

* Nice likelihood plots that went into the VHbb-boosted and resolved publications :`scripts/paperCompLikelihoodLandscapes.py`. See [here](https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/HIGG-2018-51/) and [here](https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/HIGG-2018-52/) for some examples generated with this script.

#### Extraction of confidence intervals

* Utility to extract 68% and 95% CL confidence intervals from a 1D likelihood scan in tabular form: `scripts/getConfidenceInterval.py`

#### Limits summary plots and tables

* To generate a summary plot of confidence intervals, like [here](https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/HIGG-2018-52/figaux_20.png): `scripts/make1DLimitsSummaryPlot.py`

* Same as the above, but generate a tex-style table instead: `scripts/make1DLimitsSummaryTable.py`

=======
