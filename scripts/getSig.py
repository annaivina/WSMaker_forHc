#!/usr/bin/env python


import sys
import ROOT
import os

if len(sys.argv)<2:
    print( """
Usage:
  python %prog [workspace] [exp/obs] [mass]

    expected = 1
    observed = 0
    default mass point = 125
""")
    sys.exit()

ws = sys.argv[1]
if len(sys.argv)>2:
    is_expected = bool(int(sys.argv[2]))
else:
    is_expected = False
if len(sys.argv)>3:
    mass = sys.argv[3]
else:
    mass = "125"
ROOT.gROOT.SetBatch(True)
ROOT.gROOT.ProcessLine(".L $WORKDIR/runSig.C+")

if is_expected:
    suff = "exp"
else:
    suff = "obs"

outdir = "output/"+ws+"/root-files/"+suff+"_p0"
print (outdir)

datname='obsData'
if '@' in mass:
    mass,datname=mass.split('@')

print("Will open workspace", ws)
f = ROOT.TFile.Open(f"output/{ws}/workspaces/combined/{mass}.root")
w = f.Get("combined")
mc = w.obj("ModelConfig")
pois = mc.GetParametersOfInterest()
print("Number of POIs:", pois.getSize())
it = pois.createIterator()
n = it.Next()
results = {}
while n:
    res = ROOT.runSig("output/"+ws+"/workspaces/combined/"+mass+".root", "combined", "ModelConfig",
                datname, "asimovData_1", "conditionalGlobs_1", "nominalGlobs", n.GetName(),
                mass, outdir, is_expected)
    results[n.GetName()] = res
    n = it.Next()

print("Printing results for all POI:")
for poi, r in results.items():
    print('\n\n')
    print(f"Results for POI {poi}")
    print(f"Observed significance: {r.obs_sig:.6f}")
    print(f"Observed pValue: {r.obs_pValue:.6f}")
    print(f"Median significance: {r.med_sig:.6f}")
    print(f"Median pValue: {r.med_pValue:.6f}")
    print(f"Injected significance: {r.inj_sig:.6f}")
    print(f"Injected pValue: {r.inj_pValue:.6f}")
    print('\n\n')


