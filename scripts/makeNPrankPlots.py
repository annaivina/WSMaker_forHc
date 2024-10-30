#!/usr/bin/env python


import sys
import ROOT
import os

ws = sys.argv[1]
if len(sys.argv)>2:
    SF = sys.argv[2]
else:
    SF = 2.3
if len(sys.argv)>3:
    mass = sys.argv[3]
else:
    mass = "125"
if len(sys.argv)>4:
    cardname = sys.argv[4]
else:
    cardname = "test"
if len(sys.argv)>5:
   remakeascii = sys.argv[5]
else:
   remakeascii = 1

# if the WS name contains "_jobYofY" merge jobs:
# assuming "_jobXofY" with X = 0..Y-1

nJobs = 1
pat = ROOT.TPRegexp(".*_job(\\d+)of(\\d+).*");
res = ROOT.TObjArray(pat.MatchS(ws));
if res.GetSize() >= 3:
    if res.At(1) and res.At(2):
        nJobsTmp = int(((ROOT.TObjString)(res.At(2))).GetString().Data());
        iJobTmp = int(((ROOT.TObjString)(res.At(1))).GetString().Data());
        if nJobsTmp == iJobTmp and nJobsTmp > 1:
            nJobs = nJobsTmp

miss = 0
if nJobs > 1:
    print("Merging jobs: " + str(nJobs))
    outdir = "output/"+ ws +"/root-files/"
    os.system( "mkdir -vp " + outdir + "breakdown_add" )
    os.system( "mkdir -vp " + outdir + "pulls" )
    jobStr = "job%iof%i" % (nJobs, nJobs)
    for iJob in range(0, nJobs):
        jobStr2 = "job%iof%i" % (iJob, nJobs)
        ws2 = ws.replace(jobStr, jobStr2)
        outdir2 = "output/"+ ws2 +"/root-files/"
        print("Copying root-files for job " + str(iJob))
        status = os.system( "cp " + outdir2 + "breakdown_add/*.root " + outdir + "breakdown_add/" )
        os.system( "cp " + outdir2 + "pulls/*.root " + outdir + "pulls/" )
        if status != 0:
            miss += 1

ROOT.gROOT.SetBatch(True)
ROOT.gROOT.ProcessLine(".L $WORKDIR/macros/drawPlot_pulls.C+")

print("\n    Running drawPlot_pulls for PRE-FIT order:\n")
ROOT.drawPlot_pulls(mass, ws, float(SF), remakeascii, "", False)
print("\n    Running drawPlot_pulls for POST-FIT order:\n")
ROOT.drawPlot_pulls(mass, ws, float(SF), remakeascii, "", True)

if miss != 0:
    print("")
    print("WARNING: Missing " + str(miss) + " of " + str(nJobs) + " jobs. Corresponding Nuisance parameter will be missing from the plot!")
    print("")
