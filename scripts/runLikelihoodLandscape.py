#!/usr/bin/env python
"""
A small wrapper script around LikelihoodLandscape to offer a more convenient interface.

Author: Philipp Windischhofer
Date:   August 2019
Email:  philipp.windischhofer@cern.ch

Description:
    This script runs LikelihoodLandscape.C on the provided input workspace in order to
    perform a PNLL scan. The script automatically performs the PNLL scan over all parameters
    that are set as "POIs" in the RooStats::ModelConfig. The scan is performed within the
    bounds set by the ranges of these POIs (as defined in the workspace).
"""

import ROOT
ROOT.gSystem.Load("libRooFit")
ROOT.gSystem.Load("libRooFitCore")

import os, sys, subprocess
import xml.etree.ElementTree as ET
from argparse import ArgumentParser

import BatchMgr as Mgr
from runFitCrossCheck import wait_all

try:
    from analysisBatchConfig import BatchConfig
except ImportError:
    print("analysis did not define own batch settings, using defaults")
    from batchConfig import BatchConfig

class LikelihoodScanJob(Mgr.WSMakerJob):

    ID = "likelihood_scan"

    def __init__(self, rootcmd, job_ind, log_dir, submit_dir, settings):

        super().__init__(name = f"{LikelihoodScanJob.ID}_job_{job_ind}", commands = rootcmd, submit_dir = submit_dir,
                                                log_dir = log_dir, prerequisites = [], settings = settings)

class LikelihoodMergeJob(Mgr.WSMakerJob):

    ID = "likelihood_merge"

    def __init__(self, outputdir, job_ind, log_dir, submit_dir, other_jobs, settings):

        def get_prerequisites(other_jobs):
            # need to have all the completed scans
            return [job for job in other_jobs if job.ID == LikelihoodScanJob.ID]

        mergefile_path = os.path.join(outputdir, "LikelihoodLandscape_out.root")
        command = " ".join(["hadd", mergefile_path, f"{outputdir}/*.root"])

        super().__init__(name = LikelihoodMergeJob.ID + "_" + job_ind, commands = command, submit_dir = submit_dir, log_dir = log_dir,
                                                 prerequisites = get_prerequisites(other_jobs), settings = settings)

def BuildLikelihoodScanJobs(submit_dir, log_dir, infile_path, outputdir, WorkspaceName, ModelConfigName, ObsDataName, useAsimov = False, doPostFit = False, poiValue = 1.0, numberSubjobs = 16, density = None):

    PrepareRun()

    # prepare the output directory
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    batchconf = BatchConfig()
    job_type = f"asimov_{int(useAsimov)}_postfit_{int(doPostFit)}_poi_{poiValue}"

    jobs = []
    for job_number, rootcmd in enumerate(GetLikelihoodLandscapeCmds(infile_path, outputdir, WorkspaceName, ModelConfigName, ObsDataName, useAsimov, doPostFit, poiValue, numberSubjobs, density)):
        cmd = 'root -l -b -q "{}"'.format(rootcmd.replace('"', '\\"'))
        jobs.append(LikelihoodScanJob(cmd, job_ind = f"{job_type}_{job_number}", log_dir = log_dir, submit_dir = submit_dir,
                                      settings = batchconf.default_settings))

    return jobs

def BuildMergeJob(outputdir, useAsimov, doPostFit, poiValue, log_dir, submit_dir, other_jobs):

    batchconf = BatchConfig()
    job_type = f"asimov_{int(useAsimov)}_postfit_{int(doPostFit)}_poi_{poiValue}"

    return LikelihoodMergeJob(outputdir, job_type, log_dir, submit_dir, other_jobs, settings = batchconf.default_settings)

def WriteXMLConfig(outfile_path, start_vertex, end_vertex, opts = {}):
    # ensure that all data variables are indeed strings
    start_vertex = {cur_key: str(cur_val) for cur_key, cur_val in start_vertex.items()}
    end_vertex = {cur_key: str(cur_val) for cur_key, cur_val in end_vertex.items()}

    root = ET.Element("root")
    start_section = ET.SubElement(root, "start_vertex", attrib = start_vertex)
    end_section = ET.SubElement(root, "end_vertex", attrib = end_vertex)
    end_section = ET.SubElement(root, "opts", attrib = opts)

    tree = ET.ElementTree(root)
    tree.write(outfile_path)

def GetPOIInformation(infile_path, WorkspaceName, ModelConfigName):
    infile = ROOT.TFile(infile_path, 'READ')
    ROOT.SetOwnership(infile, False)
    w = infile.Get(WorkspaceName)
    mc = w.obj(ModelConfigName)
    POIs = mc.GetParametersOfInterest()

    # iterate over the RooArgSet and extract the POI names:
    POI_information = {}
    it = POIs.createIterator()
    var = it.Next()
    while var:
        POI_name = var.GetName()
        rangeLow = var.getMin()
        rangeHigh = var.getMax()
        if abs(rangeLow) > 100:
            print(f"WARNING: your low POI range for '{POI_name}' looks weird (rangeLow = {rangeLow}). Are you sure this is correct?")
        if abs(rangeHigh) > 100:
            print(f"WARNING: your upper POI range for '{POI_name}' looks weird (rangeHigh = {rangeHigh}). Are you sure this is correct?")
        POI_information[POI_name] = {"RangeLow": rangeLow, "RangeHigh": rangeHigh}
        var = it.Next()

    infile.Close()
    return POI_information

def SliceHypercube(start_vertex, end_vertex, slice_dim, number_slices):
    """
    Slice the hyperrectangle parametrised by 'start_vertex' and 'end_vertex'
    into 'number_slices' smaller hyperrectangles along the dimension specified by
    'slice_dim'.
    """

    start_vertices = []
    end_vertices = []

    def linspace(start, end, length):
        start, end = float(start), float(end)
        if length > 1:
            stepsize = (end - start) / (length - 1)
            return [start + stepsize * cur for cur in range(length)]
        else:
            return [start]

    cut_positions = linspace(start_vertex[slice_dim], end_vertex[slice_dim], number_slices + 1) # need to place one more cut than slices

    for cut_position in cut_positions:
        cur_start_vertex = dict(start_vertex)
        cur_start_vertex[slice_dim] = cut_position
        start_vertices.append(cur_start_vertex)

        cur_end_vertex = dict(end_vertex)
        cur_end_vertex[slice_dim] = cut_position
        end_vertices.append(cur_end_vertex)

    # now need to shift them by one to have each hypercube span
    # a nonzero volume
    start_vertices = start_vertices[:-1]
    end_vertices = end_vertices[1:]

    return start_vertices, end_vertices

def PartitionHypercube(start_vertex, end_vertex, requested_partitions):
    """
    Partition a hyperrectangle into 'requested_partitions' smaller hyperrectangles,
    along all dimensions.
    """
    dimensions = start_vertex.keys()
    partitions_per_dimension = int(pow(requested_partitions, 1.0 / len(dimensions)))

    print(f"Using {partitions_per_dimension} partitions per dimension.")

    start_vertices = [start_vertex]
    end_vertices = [end_vertex]
    for cur_slice_dim in dimensions:
        cur_start_vertices = []
        cur_end_vertices = []

        for cur_start_vertex, cur_end_vertex in zip(start_vertices, end_vertices):
            cur_sliced_start_vertices, cur_sliced_end_vertices = SliceHypercube(cur_start_vertex, cur_end_vertex,
                                                                                slice_dim = cur_slice_dim, number_slices = partitions_per_dimension)

            cur_start_vertices += cur_sliced_start_vertices
            cur_end_vertices += cur_sliced_end_vertices

        start_vertices = cur_start_vertices
        end_vertices = cur_end_vertices

    return start_vertices, end_vertices

def GetLikelihoodLandscapeCmds(infile_path, outputdir, WorkspaceName, ModelConfigName, ObsDataName, useAsimov = False, doPostFit = False, poiValue = 1.0, numberSubjobs = 16, density = None):

    # ----------------------------------------------------------------------
    # prepare the XML file that holds the configuration for the NLL scan
    # ----------------------------------------------------------------------
    # extract the names of the POIs from the workspace: these are the
    # parameters that should be scanned over
    POI_info = GetPOIInformation(infile_path, WorkspaceName, ModelConfigName)
    POI_names = POI_info.keys()

    if density is None:
        # did not get anything, make up some value based on the number of POIs:
        number_dimensions = len(POI_names)
        #density_guess = {1: 10, 2: 70, 3: 60}
        density_guess = {1: 10, 2: 100, 3: 60}

        if number_dimensions > 3:
            print("Warning: do you *really* want to do a scan in more than 3 dimensions? How are you going to plot it, anyways?")
            density = 100
        else:
            density = density_guess[number_dimensions]

    print(f"using density = {density}")

    # this is the "density" of the evaluation points for the NLL, i.e.
    # points per unit (hyper)volume
    scan_opts = {"density": str(density)}

    # build the start and end points
    start_vertex = {POI_name: POI_info[POI_name]["RangeLow"] for POI_name in POI_names}
    end_vertex = {POI_name: POI_info[POI_name]["RangeHigh"] for POI_name in POI_names}

    print("using the following start point:")
    print(start_vertex)

    print("using the following end point:")
    print(end_vertex)

    # partition the parameter range such that the subjobs each have some work to do
    start_vertices, end_vertices = PartitionHypercube(start_vertex, end_vertex, requested_partitions = numberSubjobs)

    print(f"start_vertices = {start_vertices}")
    print(f"end_vertices = {end_vertices}")

    # run all these jobs
    firstJob = True
    for ind, (cur_start_vertex, cur_end_vertex) in enumerate(zip(start_vertices, end_vertices)):
        # make sure to do the (potentially time-consuming) search for the best-fit value only once
        doBestFit = firstJob
        firstJob = False

        config_path = os.path.join(outputdir, f"LikelihoodLandscape_config_{ind}.xml")
        outfile_path = os.path.join(outputdir, f"LikelihoodLandscape_out_{ind}.root")

        WriteXMLConfig(outfile_path = config_path, start_vertex = cur_start_vertex, end_vertex = cur_end_vertex, opts = scan_opts)

        args = [infile_path, outfile_path, config_path, WorkspaceName, ModelConfigName, ObsDataName]
        args = [f'"{cur}"' for cur in args] # add the proper quotes to signify strings

        # add the boolean arguments
        args.append(str(useAsimov).lower())
        args.append(str(doPostFit).lower())
        args.append(str(poiValue))
        args.append(str(doBestFit).lower())
        rootcmd = "$WORKDIR/LikelihoodLandscape.C+({arglist})".format(arglist = ", ".join(args))
        yield rootcmd

def RunLikelihoodLandscape(infile_path, outputdir, WorkspaceName, ModelConfigName, ObsDataName, useAsimov = False, doPostFit = False, poiValue = 1.0, numberSubjobs = 16, density = None):
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    pids = []
    logfiles = []

    for ind, rootcmd in enumerate(GetLikelihoodLandscapeCmds(infile_path, outputdir, WorkspaceName, ModelConfigName, ObsDataName, useAsimov, doPostFit, poiValue, numberSubjobs, density)):

        cur_logfile_path = os.path.join(outputdir, f"output_{ind}.log")
        cur_logfile = open(cur_logfile_path, 'w')

        cmds = ["root", "-l", "-b", "-q", rootcmd]
        pid = subprocess.Popen(cmds, stderr = cur_logfile, stdout = cur_logfile)
        pids.append(pid)

    wait_all(pids)
    for cur_logfile in logfiles:
        cur_logfile.close()

    print("all jobs finished - merging output ...")
    mergefile_path = os.path.join(outputdir, "LikelihoodLandscape_out.root")
    subprocess.check_output(["hadd", mergefile_path, f"{outputdir}/LikelihoodLandscape_out_*.root"])
    print("done!")

def PrepareRun():
    # compile the source
    def compile_source():
        import ROOT
        return ROOT.gROOT.ProcessLine(".L $WORKDIR/LikelihoodLandscape.C+")

    if compile_source():
        raise Exception("Error: problem with compilation.")

if __name__ == "__main__":

    # can also use it in standalone mode
    parser = ArgumentParser(description = "run LikelihoodLandscape.C")
    parser.add_argument("--infile_path", action = "store", dest = "infile_path", help = "path to file with input workspace")
    parser.add_argument("--outputdir", action = "store", dest = "outputdir", help = "path to directory holding the output")
    parser.add_argument("--WorkspaceName", action = "store", dest = "WorkspaceName", default = "combined", help = "name of RooFit workspace")
    parser.add_argument("--ModelConfigName", action = "store", dest = "ModelConfigName", default = "ModelConfig", help = "name of ModelConfig embedded in workspace")
    parser.add_argument("--ObsDataName", action = "store", dest = "ObsDataName", default = "obsData", help = "name of the dataset embedded in workspace")
    parser.add_argument("--algs", action = "store", dest = "algs", help = "Algorithms to run -> 0: postfit Asimov built with poi = 0, 1: postfit Asimov built with poi = 1, 2: prefit Asimov, 3: data unconditional")
    parser.add_argument("--density", action = "store", dest = "density", default = None, help = "number of evaluation points per unit (hyper)volume. Use larger values for better scan quality. If no value given, try to make an educated guess based on the number of POIs")
    parser.add_argument("--subjobs", action = "store", dest = "numberSubjobs", default = "16", help = "number of subjobs to use: the volume in parameter space over which the scan should be run is partitioned into this many subjobs, which are then executed concurrently")
    args = vars(parser.parse_args())

    PrepareRun()

    for alg in args["algs"].split(','):
        alg = int(alg)

        if alg == 0:
            # postfit Asimov built with POI set to 0
            useAsimov = True
            doPostFit = True
            poiValue = 0.0
            outputdir = os.path.join(args["outputdir"], "Asimov_postfit_poi_0")
        elif alg == 1:
            # postfit Asimov built with POI set to 1
            useAsimov = True
            doPostFit = True
            poiValue = 1.0
            outputdir = os.path.join(args["outputdir"], "Asimov_postfit_poi_1")
        elif alg == 2:
            # prefit Asimov
            useAsimov = True
            doPostFit = False
            poiValue = 1.0
            outputdir = os.path.join(args["outputdir"], "Asimov_prefit")
        elif alg == 3:
            # data unconditional
            doPostFit = False
            useAsimov = False
            poiValue = 1.0
            outputdir = os.path.join(args["outputdir"], "Data")
        else:
            raise NotImplementedError("Error: algorithm not implemented!")

        RunLikelihoodLandscape(infile_path = args["infile_path"],
                               outputdir = outputdir,
                               WorkspaceName = args["WorkspaceName"],
                               ModelConfigName = args["ModelConfigName"],
                               ObsDataName = args["ObsDataName"],
                               useAsimov = useAsimov,
                               doPostFit = doPostFit,
                               poiValue = poiValue,
                               numberSubjobs = int(args["numberSubjobs"]))

