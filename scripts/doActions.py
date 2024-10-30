#!/usr/bin/env python


from argparse import ArgumentParser
import BatchMgr as Mgr
import os, re, itertools, ROOT
from contextlib import contextmanager

try:
    from analysisBatchConfig import BatchConfig
except ImportError:
    print("analysis did not define own batch settings, using defaults")
    from batchConfig import BatchConfig

@contextmanager
def dir_exist_ok():
    try:
        yield
    except OSError:
        pass

# ---------------------------------------------------
# here are all definitions of the individual jobs
# ---------------------------------------------------

# to build the actual workspace
class BuildWorkspaceTask(Mgr.AtomicTask):

    ID = "build_workspace"

    def __init__(self, conf_file, outputversion, log_dir, submit_dir, other_tasks, settings):

        def get_prerequisites(other_tasks):
            # this job does not depend on anything else
            return []

        commands = f"MakeWorkspace {conf_file} {outputversion}"

        super().__init__(name = BuildWorkspaceTask.ID, commands = commands, submit_dir = submit_dir,
                                                 log_dir = log_dir, prerequisites = get_prerequisites(other_tasks), settings = settings)

# to run FitCrossChecks
class FCCTask(Mgr.AtomicTask):

    ID = "FCC"

    def __init__(self, fcc_options, log_dir, submit_dir, other_tasks, settings):

        def get_prerequisites(other_tasks):
            # need to have an existing workspace
            return [task for task in other_tasks if task.ID == BuildWorkspaceTask.ID]

        executable = os.path.join(os.environ["WORKDIR"], "scripts/runFitCrossCheck.py")

        if '@' in fcc_options:
            conf = str(fcc_options).split('@')
            obsDataName = "obsData"
            if len(conf) > 2:
                obsDataName = conf[2]
            for mass in conf[1].split(','):
                commands = "python {executable} {ws_name} {conf} {mass} {data_name}".format(executable = executable, ws_name = ws_name, 
                                                                                            conf = str(conf[0]), mass = str(mass), data_name = str(obsDataName))
        else:
            commands = "python {executable} {ws_name} {conf} {mass}".format(executable = executable, ws_name = ws_name, conf = str(options.fcc), mass = "125")

        super().__init__(name = FCCTask.ID, commands = commands, submit_dir = submit_dir, log_dir = log_dir, 
                                      prerequisites = get_prerequisites(other_tasks), settings = settings)

class doPlotFromWSTask(Mgr.AtomicTask):

    ID = "doPlotFromWS"

    def __init__(self, plot_options, log_dir, submit_dir, other_tasks, settings):

        def get_prerequisites(other_tasks):
            # need to have existing fit results
            return [task for task in other_tasks if task.ID == FCCTask.ID]

        tokens = re.split('(;|@|!|&)', plot_options)
        mass = tokens[tokens.index('@')+1] if '@' in tokens else ''
        fccdir = tokens[tokens.index('!')+1] if '!' in tokens else ''
        doSum = '&' in tokens
        plot_types = tokens[0]
        pass_to_user = tokens[-1]
        if pass_to_user == str(mass): pass_to_user = ''

        commands = []

        for opt in plot_types.split(','):
            a = ["python", os.path.join(os.environ["WORKDIR"], "scripts/doPlotFromWS.py"), '-p', str(opt), '-m', mass, ws_name]
            if not fccdir == '':
                a.insert(2, fccdir)
                a.insert(2, '-f')
            if doSum:
                a.insert(2, '-s')

            if not pass_to_user == '':
                for user_arg in re.split(',', pass_to_user):
                    if not user_arg == ',' or not user_arg == ';':
                        a.append(user_arg)

            commands.append(" ".join(a))

        super().__init__(name = doPlotFromWSTask.ID, commands = commands, submit_dir = submit_dir, log_dir = log_dir, 
                                               prerequisites = get_prerequisites(other_tasks), settings = settings)        


class ReducedDiagPlotsTask(Mgr.AtomicTask):

    ID = "makeReducedDiagPlots"

    def __init__(self, plot_options, log_dir, submit_dir, other_tasks, settings):

        def get_prerequisites(other_tasks):
            # need to have existing fit results
            return [task for task in other_tasks if task.ID == FCCTask.ID]

        tokens = re.split('(;|@)', plot_options)
        fcc_types = tokens[0]
        fcc_types = fcc_types.replace(",", " ")

        executable = os.path.join(os.environ["WORKDIR"], "scripts/makePullPlots.py")
        
        a = ["python", executable, 'plot', '-a', fcc_types, "--", ws_name]

        super().__init__(name = ReducedDiagPlotsTask.ID, commands = " ".join(a), submit_dir = submit_dir, log_dir = log_dir, 
                                                   prerequisites = get_prerequisites(other_tasks), settings = settings)        


class BreakdownJob(Mgr.WSMakerJob):

    ID = "breakdown"

    def __init__(self, options, poi, num_total_jobs, num_job, slices, log_dir, submit_dir, settings):
            
        muhatopts = str(options).split(',')
        is_expected = muhatopts[0]
        mass = "125"
        mode = "1"
        if len(muhatopts) > 1:
            mass = muhatopts[1]
        if len(muhatopts) >2:
            mode = muhatopts[2]

        command = " ".join(["python", os.path.join(os.environ["WORKDIR"], "scripts/runMuHat.py"), ws_name, "--exp", is_expected, "--mode", mode, "--mass", mass, "--poi", poi, "--slices", slices, "--num_total_slices", str(num_total_jobs), "--num_slice", str(num_job)])

        super().__init__(name = f"{BreakdownJob.ID}_{poi}_job_{num_job + 1}_of_{num_total_jobs}", commands = command, submit_dir = submit_dir, log_dir = log_dir, 
                                           prerequisites = [], settings = settings)                
        
class BDOutputCombinerJob(Mgr.WSMakerJob):

    ID = "bd_combine"

    def __init__(self, options, ws_name, log_dir, submit_dir, other_jobs, settings):

        def get_prerequisites(other_jobs):
            # need to have the ouput of the breakdown jobs
            return [job for job in other_jobs if job.ID == BreakdownJob.ID]
            
        commands = [
            " ".join(["python", os.path.join(os.environ["WORKDIR"], "scripts/combineBreakdown.py"), ws_name]),
            " ".join(["python", os.path.join(os.environ["WORKDIR"], "scripts/BreakdownTxtToTex.py"), ws_name])
        ]

        super().__init__(name = BDOutputCombinerJob.ID, commands = commands, submit_dir = submit_dir, log_dir = log_dir, prerequisites = get_prerequisites(other_jobs), settings = settings)               

class BreakdownTask(Mgr.Task):

    ID = "breakdown"

    def __init__(self, options, categories_per_job, log_dir, submit_dir, other_tasks, settings):

        def get_prerequisites(other_jobs):
            # need to have an existing workspace
            return [task for task in other_jobs if task.ID == BuildWorkspaceTask.ID]

        def job_generator():
            jobs = []

            ROOT.gROOT.SetBatch(True)
            if os.path.exists(os.environ["ANALYSISDIR"]+"/scripts/muHatModes.C"):
                ROOT.gROOT.ProcessLine(".L $ANALYSISDIR/scripts/muHatModes.C++")
            else:
                ROOT.gROOT.ProcessLine(".L $WORKDIR/muHatModes.C++")
            # need to get mode
            muhatopts = str(options).split(',')
            is_expected = muhatopts[0]
            mode = "1"
            mass = "125"
            if len(muhatopts) > 1:
                mass = muhatopts[1]
            if len(muhatopts) >2:
                mode = muhatopts[2]

            mhm = ROOT.MuHatModes(int(mode))
            nCat = mhm.get_nCat()
            cps = categories_per_job

            #get poi names
            poi_strings = []
            print(f"Will open workspace {ws_name}")
            f = ROOT.TFile.Open(f"$ANALYSISDIR/output/{ws_name}/workspaces/combined/{mass}.root")
            w = f.Get("combined")
            mc = w.obj("ModelConfig")
            pois = mc.GetParametersOfInterest()
            print(f"Number of POIs: {pois.getSize()}")
            it = pois.createIterator()
            n = it.Next()
            while n:
                poi_strings.append(n.GetName())
                n = it.Next()


            if (cps == -1) or (cps >= nCat) or (nCat <= 3):
                slice_string = "-1" # all in one job
                for poi in poi_strings:
                    jobs.append(BreakdownJob(options = options, poi = poi, slices = slice_string, num_total_jobs = 1, num_job = 0, log_dir = log_dir, submit_dir = submit_dir, settings = settings))
            else:
                if cps < 3:
                    list_range = list(range(3, nCat)) # 0, 1 and 2 always together (total, data stat., full syst)
                    slice_lists = [ list_range[i:i+cps] for i in range(0, len(list_range), cps) ]
                    slice_lists.insert(0, [0,1,2]) 
                else:
                    list_range = list(range(0, nCat))
                    slice_lists = [ list_range[i:i+cps] for i in range(0, len(list_range), cps) ]
                    
                num_jobs = len(slice_lists)
                cur_job = 0
                
                for slice_list in slice_lists:
                    slice_string = ""
                    for s in slice_list:
                        slice_string += str(s)+","
                    slice_string = slice_string[:-1]
                    for poi in poi_strings:
                        jobs.append(BreakdownJob(options = options, poi = poi, num_total_jobs = num_jobs, num_job = cur_job, slices = slice_string, log_dir = log_dir, submit_dir = submit_dir, settings = settings))
                    cur_job += 1

                #combine output
                jobs.append(BDOutputCombinerJob(options = "", ws_name = ws_name, log_dir = log_dir, submit_dir = submit_dir, other_jobs = jobs, settings = settings))

            return jobs

        super().__init__(taskname = BreakdownTask.ID, job_generator = job_generator, prerequisites = get_prerequisites(other_tasks))

class RankingJob(Mgr.WSMakerJob):

    ID = "ranking"

    def __init__(self, options, num_total_jobs, num_job, log_dir, submit_dir, settings):

        npopts = str(options).split(',')
        mass = npopts[0]
        dataName = "obsData"
        if len(npopts) > 1:
            dataName=npopts[1]
        if len(npopts) > 2:
            dataName += "," + npopts[2]

        command = " ".join(["python", os.path.join(os.environ["WORKDIR"], "scripts/runNPranking.py"), ws_name, "--mass", mass, "--model_config", "ModelConfig", "--data", dataName, 
                            "--num_total_slices", str(num_total_jobs), "--num_slice", str(num_job)])

        super().__init__(name = f"{RankingJob.ID}_job_{num_job + 1}_of_{num_total_jobs}", commands = command, submit_dir = submit_dir, log_dir = log_dir,
                                         prerequisites = [], settings = settings)

class RankingTask(Mgr.Task):

    ID = "ranking"

    def __init__(self, options, number_jobs, log_dir, submit_dir, other_tasks, settings):

        def get_prerequisites(other_tasks):
            # need to have existing workspace
            return [task for task in other_tasks if task.ID == BuildWorkspaceTask.ID]
    
        def job_generator():
            jobs = []

            for cur_job in range(number_jobs):
                jobs.append(RankingJob(options = options, log_dir = log_dir, submit_dir = submit_dir,
                                       num_total_jobs = number_jobs, num_job = cur_job,
                                       settings = settings))

            return jobs

        super().__init__(taskname = RankingTask.ID, prerequisites = get_prerequisites(other_tasks), job_generator = job_generator)

class RankingPlotTask(Mgr.AtomicTask):

    ID = "ranking_plot"

    def __init__(self, options, ws_name, log_dir, submit_dir, other_tasks, settings):

        def get_prerequisites(other_tasks):
            # need to wait for all ranking jobs to have finished
            return [task for task in other_tasks if task.ID == RankingTask.ID]

        command = " ".join(["python", os.path.join(os.environ["WORKDIR"], "scripts/makeNPrankPlots.py"), ws_name, "2.3", str(options)])

        super().__init__(name = RankingPlotTask.ID, commands = command, submit_dir = submit_dir, log_dir = log_dir,
                                              prerequisites = get_prerequisites(other_tasks), settings = settings)

class SignificanceTask(Mgr.AtomicTask):

    ID = "significance"

    def __init__(self, options, log_dir, submit_dir, other_tasks, settings):

        def get_prerequisites(other_tasks):
            # need to have existing workspace
            return [task for task in other_tasks if task.ID == BuildWorkspaceTask.ID]

        executable = os.path.join(os.environ["WORKDIR"], "scripts/getSig.py")

        commands = []

        conf = str(options).split(',')
        if len(conf)>1:
            for mass in conf[1:]:
                commands.append(" ".join(["python", executable, ws_name, str(conf[0]), str(mass)]))
        else:
            commands.append(" ".join(["python", executable, ws_name, str(options.sig), "125"]))

        super().__init__(name = SignificanceTask.ID, commands = commands, submit_dir = submit_dir, log_dir = log_dir,
                                               prerequisites = get_prerequisites(other_tasks), settings = settings)        

class TablesTask(Mgr.AtomicTask):

    ID = "tables"

    def __init__(self, options, log_dir, submit_dir, other_tasks, settings):

        def get_prerequisites(other_tasks):
            # need to have existing fit results
            return [task for task in other_tasks if task.ID == FCCTask.ID]

        tokens = re.split('(;|@)', options)
        mass = tokens[tokens.index('@')+1] if '@' in tokens else ''
        table_types = tokens[0]
        pass_to_user = tokens[-1]
        if pass_to_user == str(mass): pass_to_user = ''        

        a = ["python", os.path.join(os.environ["WORKDIR"], "scripts/makeTables.py"), '-t', table_types, '-m', mass, ws_name]
        if not pass_to_user == '':
            for user_arg in re.split('(,|;)', pass_to_user):
                if not user_arg == ',' or not user_arg == ';':
                    a.append(user_arg)

        super().__init__(name = TablesTask.ID, commands = " ".join(a), submit_dir = submit_dir, log_dir = log_dir,
                                         prerequisites = get_prerequisites(other_tasks), settings = settings)        

class RatiosTask(Mgr.AtomicTask):

    ID = "ratios"

    def __init__(self, options, ws_name, log_dir, submit_dir, other_tasks, settings):

        def get_prerequisites(other_tasks):
            # need to have the yield files from the WS plots
            return [task for task in other_tasks if task.ID == doPlotFromWSTask.ID]

        tokens = re.split('(;|@)', options)
        ws_name2 = tokens[0]
        if ws_name2.lower() == "current": ws_name2 = ws_name
        fcc_types = tokens[2]
        pass_to_user = tokens[-1]
        if pass_to_user == fcc_types: pass_to_user = ''

        executable = os.path.join(os.environ["WORKDIR"], "scripts/makeRatioTables.py")

        a = ["python", executable, '-t', fcc_types, ws_name, ws_name2]
        if not pass_to_user == '':
            for user_arg in re.split('(,|;)', pass_to_user):
                if not user_arg == ',' or not user_arg == ';':
                    a.append(user_arg)

        super().__init__(name = RatiosTask.ID, commands = " ".join(a), submit_dir = submit_dir, log_dir = log_dir,
                                         prerequisites = get_prerequisites(other_tasks), settings = settings)

class LimitTask(Mgr.AtomicTask):

    ID = "limit"

    def __init__(self, options, ws_name, log_dir, submit_dir, other_tasks, settings):

        def get_prerequisites(other_tasks):
            # need to have existing workspace
            return [task for task in other_tasks if task.ID == BuildWorkspaceTask.ID]

        executable = os.path.join(os.environ["WORKDIR"], "scripts/getLimit.py")

        conf = str(options).split(',')
        if len(conf)>1:
            for mass in conf[1:]:
                res = ["python", executable, ws_name, str(conf[0]), str(mass)]
        else:
            res = ["python", executable, ws_name, str(options.limit), "125"]

        super().__init__(name = LimitTask.ID, commands = " ".join(res), submit_dir = submit_dir, log_dir = log_dir,
                                        prerequisites = get_prerequisites(other_tasks), settings = settings)


class ComparePullTask(Mgr.AtomicTask):

    ID = "compare_pulls"

    def __init__(self, options, ws_name, log_dir, submit_dir, other_tasks, settings):

        def get_prerequisites(other_tasks):
            # need to have existing FCC file (which in turn needs a workspace)
            return [task for task in other_tasks if task.ID == FCCTask.ID]
            
        tokens = re.split('(;|!)', options)
        fcc_types = tokens[0]
        fcc_types = fcc_types.replace(",", " ")
        
        if fcc_types == '2 7': name = 'output/'+ ws_name +'/plots/PullComp_A-D'
        if fcc_types == '5 9': name = 'output/'+ ws_name +'/plots/PullComp_A-CD'
        else: name = 'output/'+ ws_name +'/plots/PullComp'

        executable = os.path.join(os.environ["WORKDIR"], "scripts/makePullPlots.py")
        
        a = ["python", executable, 'compare_fits', '-a', fcc_types, '-p', name, '--slides', ws_name]

        super().__init__(name = ComparePullTask.ID, commands = " ".join(a), submit_dir = submit_dir, log_dir = log_dir,
                                              prerequisites = get_prerequisites(other_tasks), settings = settings)

class LikelihoodScanTask(Mgr.Task):

    ID = "likelihood_scan"

    def __init__(self, options, ws_name, log_dir, submit_dir, other_tasks):
        
        def get_prerequisites(other_jobs):
            # need to have an existing workspace
            return [job for job in other_jobs if job.ID == BuildWorkspaceTask.ID]

        def job_generator():

            from runLikelihoodLandscape import BuildLikelihoodScanJobs, BuildMergeJob

            def parse_alg(alg, output_dir):
                if alg == 0:
                    # postfit Asimov built with POI set to 0
                    useAsimov = True
                    doPostFit = True
                    poiValue = 0.0
                    cur_output_dir = os.path.join(output_dir, "Asimov_postfit_poi_0")
                elif alg == 1:
                    # postfit Asimov built with POI set to 1
                    useAsimov = True
                    doPostFit = True
                    poiValue = 1.0
                    cur_output_dir = os.path.join(output_dir, "Asimov_postfit_poi_1")
                elif alg == 2:
                    # prefit Asimov
                    useAsimov = True
                    doPostFit = False
                    poiValue = 1.0
                    cur_output_dir = os.path.join(output_dir, "Asimov_prefit")
                elif alg == 3:
                    # data unconditional
                    useAsimov = False
                    cur_output_dir = os.path.join(output_dir, "Data")
                else:
                    raise NotImplementedError("Error: algorithm not implemented!")

                return cur_output_dir, useAsimov, doPostFit, poiValue
        
            jobs = []

            obsDataName = "obsData"
            output_dir = os.path.join("output", ws_name, "LikelihoodLandscape")
            if '@' in options:
                conf = str(options).split('@')
                if len(conf) > 2:
                    obsDataName = conf[2]
                for mass in conf[1].split(','):
                    infile_path = os.path.join("output", ws_name, "workspaces", "combined", f"{mass}.root")
                    
                    for alg in conf[0].split(','):
                        alg = int(alg)
                        alg_jobs = []

                        cur_output_dir, useAsimov, doPostFit, poiValue = parse_alg(alg, output_dir)
                        print("doPostFit {}".format(doPostFit))
                        print("poiValue {}".format(poiValue))
                        alg_jobs += BuildLikelihoodScanJobs(submit_dir = submit_dir, log_dir = log_dir, infile_path = infile_path, outputdir = cur_output_dir, WorkspaceName = "combined", 
                                                            ModelConfigName = "ModelConfig", ObsDataName = obsDataName, useAsimov = useAsimov, doPostFit = doPostFit, poiValue = poiValue, numberSubjobs = 16, density = None)
                        alg_jobs.append(BuildMergeJob(outputdir = cur_output_dir, useAsimov = useAsimov, doPostFit = doPostFit, poiValue = poiValue, log_dir = log_dir, submit_dir = submit_dir, other_jobs = alg_jobs))
                        jobs += alg_jobs
            else:
                infile_path = os.path.join("output", ws_name, "workspaces", "combined", "125.root")
                        
                for alg in options.split(','):
                    alg = int(alg)
                    alg_jobs = []

                    cur_output_dir, useAsimov, doPostFit, poiValue = parse_alg(alg, output_dir)
                    print("doPostFit {}".format(doPostFit))
                    print("poiValue {}".format(poiValue))
                    cur_output_dir, useAsimov = extract_data_type_from_alg(alg, output_dir)
                    alg_jobs += BuildLikelihoodScanJobs(submit_dir = submit_dir, log_dir = log_dir, infile_path = infile_path, outputdir = cur_output_dir, WorkspaceName = "combined", 
                                                        ModelConfigName = "ModelConfig", ObsDataName = obsDataName, useAsimov = useAsimov, doPostFit = doPostFit, poiValue = poiValue, numberSubjobs = 16, density = None)
                    alg_jobs.append(BuildMergeJob(outputdir = cur_output_dir, useAsimov = useAsimov, doPostFit = doPostFit, poiValue = poiValue, log_dir = log_dir, submit_dir = submit_dir, other_jobs = alg_jobs))
                    jobs += alg_jobs
                
            return jobs

        super().__init__(taskname = LikelihoodScanTask.ID, prerequisites = get_prerequisites(other_tasks), job_generator = job_generator)

class LikelihoodScanPlotsTask(Mgr.AtomicTask):

    ID = "likelihood_scan_plots"

    def __init__(self, options, ws_name, log_dir, submit_dir, other_tasks, settings):
        
        def get_prerequisites(other_tasks):
            # need to have the merged output files ready
            from runLikelihoodLandscape import LikelihoodMergeJob
            return [task for task in other_tasks if task.ID == LikelihoodMergeJob.ID]
        
        options = options.lower().split(',')

        plot_output_dir = os.path.join("output", ws_name, "plots", "LikelihoodLandscape")
        data_input_file = os.path.join("output", ws_name, "LikelihoodLandscape", "Data", "LikelihoodLandscape_out.root")
        asimov_input_file = os.path.join("output", ws_name, "LikelihoodLandscape", "Asimov", "LikelihoodLandscape_out.root")
           
        inputs = []
        if "asimov" in options:
            inputs += ["--asimov_infile", asimov_input_file]
        if "data" in options:
            inputs += ["--data_infile", data_input_file]

        executable = os.path.join(os.environ["WORKDIR"], "scripts/plotLikelihoodLandscape.py")

        res = ["python", executable, "--outdir", plot_output_dir] + inputs

        super().__init__(name = LikelihoodScanPlotsTask.ID, commands = " ".join(res), submit_dir = submit_dir,
                                                      log_dir = log_dir, prerequisites = get_prerequisites(other_tasks), settings = settings)

# ---------------------------------------------------
# Parse the command line options and schedule the jobs
# ---------------------------------------------------

if __name__ == "__main__":
    
    parser = ArgumentParser()

    # positional arguments: the configuration and the output directory
    parser.add_argument("configfile")
    parser.add_argument("outputversion")

    # optional arguments: which algorithms to run
    parser.add_argument("-w", "--workspace", dest = "ws", action = "store_true", 
                        help = "create workspace", default = False)
    parser.add_argument("-l", "--limit", dest="limit", metavar="isExpected",
                        help="compute exp (1) or obs (0) limit")
    parser.add_argument("-f", "--fcc", dest="fcc", metavar="algs",
                        help="run FitCrossChecks")
    parser.add_argument("--nll_landscape", dest = "nll_landscape", metavar = "algs",
                        help = "run LikelihoodLandscape")
    parser.add_argument("--nll_plots", dest = "nll_plots", action = "store",
                        help = "run plotLikelihoodLandscape")
    parser.add_argument("-m", "--makeReduced", dest="makered", metavar="algs",
                        help="run makeReducedDiagPlots")
    parser.add_argument("-c", "--compare-pulls", dest="comparpull", metavar="algs",
                        help="run compare pull between asimov and fit to data")
    parser.add_argument("-u", "--muhat", dest="muhat", metavar="isExpected",
                        help="run GetMuHat")
    parser.add_argument("-t", "--tables", dest="tables", metavar="modes",
                        help="make pre/postfit tables")
    parser.add_argument("-a", "--ratios", dest="ratios", metavar="modes",
                        help="make pre/postfit ratio tables")
    parser.add_argument("-p", "--plots", dest="plots", metavar="modes",
                        help="make pre/postfit plots")
    parser.add_argument("-b", "--btagPlots", dest="btagPlots", metavar="modes",
                        help="make unfolded b-tag plots")
    parser.add_argument("-s", "--sig", dest="sig", metavar="isExpected",
                        help="compute exp/obs significances and p0")
    parser.add_argument("-r", "--NPranking", dest="NPranking", metavar="mass",
                        help="compute nuisance parameter ranking")
    parser.add_argument("-n", "--NPrankingPlots", dest="NPrankingPlots", metavar="mass",
                        help="plot nuissance parameter ranking")
    parser.add_argument("--driver", dest = "driver", action = "store",
                        help = "where to run the jobs: 'local', 'condor' or 'torque'", default = "local")
    
    args = parser.parse_args()

    # prepare the correct output directory
    cutv, outv = Mgr.get_ws_name(args.configfile, args.outputversion)
    ws_name = cutv + '.' + outv
    run_dir = os.path.join("output", ws_name)
    submit_dir = os.path.join(run_dir, "submit")
    log_dir = os.path.join(run_dir, "logs")

    batchconf = BatchConfig()

    with dir_exist_ok():
        os.makedirs(run_dir)

    with dir_exist_ok():
        os.makedirs(log_dir)

    with dir_exist_ok():
        os.makedirs(submit_dir)

    tasks = []

    # now go through all the arguments and build the necessary jobs ...
    if args.ws:
        tasks.append(BuildWorkspaceTask(conf_file = args.configfile, outputversion = outv, 
                                        log_dir = log_dir, submit_dir = submit_dir, other_tasks = tasks,
                                        settings = batchconf.getJobSettings("BuildWorkspaceTask")))

    if args.fcc:
        tasks.append(FCCTask(fcc_options = args.fcc, log_dir = log_dir, submit_dir = submit_dir,
                           other_tasks = tasks, settings = batchconf.getJobSettings("FCCTask") ))

    if args.plots:
        tasks.append(doPlotFromWSTask(plot_options = args.plots, log_dir = log_dir, submit_dir = submit_dir,
                                    other_tasks = tasks, settings = batchconf.getJobSettings("doPlotFromWSTask")))

    if args.makered:
        tasks.append(ReducedDiagPlotsTask(plot_options = args.makered, log_dir = log_dir, submit_dir = submit_dir,
                                        other_tasks = tasks, settings = batchconf.getJobSettings("ReducedDiagPlotsTask")))

    if args.muhat:
        tasks.append(BreakdownTask(options = args.muhat, categories_per_job = batchconf.categories_per_breakdown_job, log_dir = log_dir, 
                                   submit_dir = submit_dir, other_tasks = tasks, settings = batchconf.getJobSettings("BreakdownTask")))

    if args.NPranking:
        tasks.append(RankingTask(options = args.NPranking, number_jobs = batchconf.number_ranking_jobs, log_dir = log_dir, submit_dir = submit_dir, 
                                 other_tasks = tasks, settings =  batchconf.getJobSettings("RankingTask")))

    if args.NPrankingPlots:
        tasks.append(RankingPlotTask(options = args.NPrankingPlots, ws_name = ws_name, log_dir = log_dir,
                                     submit_dir = submit_dir, other_tasks = tasks, settings = batchconf.getJobSettings("RankingPlotTask")))
        
    if args.sig:
        tasks.append(SignificanceTask(options = args.sig, log_dir = log_dir, submit_dir = submit_dir,
                                      other_tasks = tasks, settings = batchconf.getJobSettings("SignificanceTask")))

    if args.tables:
        tasks.append(TablesTask(options = args.tables, log_dir = log_dir, submit_dir = submit_dir,
                                other_tasks = tasks, settings = batchconf.getJobSettings("TablesTask")))        

    if args.limit:
        tasks.append(LimitTask(options = args.limit, ws_name = ws_name, log_dir = log_dir,
                               submit_dir = submit_dir, other_tasks = tasks, settings = batchconf.getJobSettings("LimitTask")))

    if args.comparpull:
        tasks.append(ComparePullTask(options = args.comparpull, ws_name = ws_name, log_dir = log_dir,
                                submit_dir = submit_dir, other_tasks = tasks, settings = batchconf.getJobSettings("ComparePullTask")))

    if args.ratios:
        tasks.append(RatiosTask(options = args.ratios, ws_name = ws_name, log_dir = log_dir,
                                submit_dir = submit_dir, other_tasks = tasks, settings = batchconf.getJobSettings("RatiosTask")))
        
    if args.nll_landscape:
        tasks.append(LikelihoodScanTask(options = args.nll_landscape, ws_name = ws_name, log_dir = log_dir,
                                        submit_dir = submit_dir, other_tasks = tasks))

    if args.nll_plots:
        tasks.append(LikelihoodScanPlotsTask(args.nll_plots, ws_name, log_dir, submit_dir, tasks, 
        settings = batchconf.getJobSettings("LikelihoodScanPlotsTask")))

    # ... and submit them
    drivers = {"local": Mgr.LocalJobSubmitter, "condor": Mgr.CondorJobSubmitter, "torque": Mgr.TorqueJobSubmitter}
    Mgr.TaskScheduler.schedule(tasks, drivers[args.driver])

    print(f"finished for {ws_name}")
