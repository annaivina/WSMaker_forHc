#!/usr/bin/env python


import sys, os, ROOT
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("ws")
parser.add_argument("--mass", dest = "mass", action = "store", default = 125, type = int)
parser.add_argument("--model_config", dest = "model_config", action = "store", default = "ModelConfig")
parser.add_argument("--data", dest = "data", action = "store", default = "obsData")
parser.add_argument("--precision", dest = "precision", action = "store", default = 0.005)
parser.add_argument("--loglevel", dest = "loglevel", action = "store", default = "INFO")
parser.add_argument("--num_total_slices", dest = "num_total_slices", action = "store", default = 1, type = int)
parser.add_argument("--num_slice", dest = "num_slice", action = "store", default = 1, type = int)
args = parser.parse_args()

ROOT.gROOT.SetBatch(True)
ROOT.gROOT.ProcessLine(".L $WORKDIR/macros/runPulls.C+")

print("Running runPulls")
ROOT.runPulls("output/" + args.ws + "/workspaces/combined/" + str(args.mass) + ".root", "combined", args.model_config, args.data, args.ws, args.num_total_slices, args.num_slice)

# to compute the total uncertainty: need to do it only once
if args.num_slice == 0:
    ROOT.gROOT.ProcessLine(".L $WORKDIR/macros/runBreakdown.C+")
    ROOT.runBreakdown("output/" + args.ws + "/workspaces/combined/" + str(args.mass) + ".root", "combined", args.model_config, args.data, "config/breakdown.xml", "add", "total", args.precision, 0.0, args.ws, args.loglevel)

