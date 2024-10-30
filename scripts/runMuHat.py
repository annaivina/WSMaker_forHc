#!/usr/bin/env python


import sys, os, ROOT
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("ws")
parser.add_argument("--mass", dest = "mass", action = "store", default = 125, type = int)
parser.add_argument("--data", dest = "data", action = "store", default = "obsData")
parser.add_argument("--exp", dest = "exp", action = "store", default = 0, type = int)
parser.add_argument("--mode", dest = "mode", action = "store", default = 2, type = int)
parser.add_argument("--mu", dest = "mu", action = "store", default = 1, type = int)
parser.add_argument("--slices", dest = "slices", action = "store", default = "", type = str)
parser.add_argument("--num_total_slices", dest = "num_total_slices", action = "store", default = 1, type = int)
parser.add_argument("--num_slice", dest = "num_slice", action = "store", default = 1, type = int)
parser.add_argument("--poi", dest = "poi", action = "store", default = "SigXsecOverSM", type = str)
args = parser.parse_args()

ROOT.gROOT.SetBatch(True)
ROOT.gROOT.ProcessLine(".L $WORKDIR/newGetMuHat.C+")

dataName = "obsData"
if args.exp == 2:
    dataName = "asimovDataAtLimit"
    
slice_list = args.slices.split(',')
print(f"Running categories {tuple(slice_list)} (-1: ALL)")

a_cat = ROOT.TArrayI(len(slice_list))
for i in range(0, len(slice_list)):
    a_cat[i] = int(slice_list[i])

ROOT.newGetMuHat(args.ws, a_cat, args.num_total_slices, args.num_slice, args.exp==1, args.mode, str(args.mass), args.poi,"combined","ModelConfig",dataName,False,False,args.mu)
