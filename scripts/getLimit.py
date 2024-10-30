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
ROOT.gROOT.ProcessLine(".L $WORKDIR/runAsymptoticsCLs.C+")

if is_expected:
    ROOT.doExpected(True)
    suff = "exp"
else:
    ROOT.doExpected(False)
    suff = "obs"

#FIXME should be an option
ROOT.doBetterBands(False)
#ROOT.doBetterBands(True)

ROOT.doInjection(False)

print("Will open workspace", ws)
f = ROOT.TFile.Open(f"output/{ws}/workspaces/combined/{mass}.root")
w = f.Get("combined")
mc = w.obj("ModelConfig")
pois = mc.GetParametersOfInterest()
print("Number of POIs:", pois.getSize())
it = pois.createIterator()
n = it.Next()
while n:
    poiname = n.GetName()
    outdir = "output/"+ws+"/root-files/"+suff
    ROOT.runAsymptoticsCLs("output/"+ws+"/workspaces/combined/"+mass+".root", "combined",
                           "ModelConfig", "obsData", "", outdir, mass, 0.95, poiname)
    n = it.Next()

    f=ROOT.TFile(outdir+"/"+mass+"_"+poiname+".root")
    lim = f.Get("limit")
    med = lim.GetBinContent(2)
    p2 = lim.GetBinContent(3)
    p1 = lim.GetBinContent(4)
    m1 = lim.GetBinContent(5)
    m2 = lim.GetBinContent(6)
    obs = lim.GetBinContent(1)
    inj = lim.GetBinContent(7)

    print( f"POI = {poiname}")
    print( "-->Injected limit:", inj)
    print( "-->Expected limit:", med, "+", p1-med, "-", med-m1)
    print( "-->Observed limit:", obs)
    print( f"-->{med:.2f}")

    
    outfname = outdir+'/limits_'+mass+'.txt'
    
    if poiname == pois.first().GetName():
        os.system('echo "POI: '+poiname+'" > '+ outfname)
    else:
        os.system('echo "POI: '+poiname+'" >> '+ outfname)
    os.system('echo "-->Injected limit: '+str(inj)+'" >> '+ outfname)
    os.system('echo "-->Expected limit: '+str(med)+' +'+str(p1-med)+' -'+str(med-m1)+'" >> '+ outfname)
    os.system('echo "-->Observed limit: '+str(obs)+'" >> '+outfname)
    os.system(f'echo "-->Expected limit: {med:.2f}^{{+{p1-med:.2f}}}_{{-{med-m1:.2f}}}" >> {outfname}')
    os.system(f'echo "-->Observed limit: {obs:.2f}" >> {outfname}')
    os.system(f'echo " " >> {outfname}')
    os.system(f'echo "-->obs -2s -1s exp +1s _2s" >> {outfname}')
    os.system(f'echo "-->{obs:.2f} & {m2:.2f} &  {m1:.2f} & {med:.2f} & {p1:.2f} & {p2:.2f} \\\\" >> {outfname}')


    print( "Now adding asimov data with mu at expected limit.")
    ROOT.RooWorkspace.rfimport = getattr(ROOT.RooWorkspace, 'import')

    f = ROOT.TFile("output/"+ws+"/workspaces/combined/"+mass+".root")
    wsm = f.Get("combined")

    print( "Data contained in the original workspace: ")
    allData = wsm.allData()
    alreadyExists = False
    while allData.size() > 0:
        data = allData.front()
        allData.pop_front()
        print( "   ==>",data.GetName())
        if data.GetName() == "asimovDataAtLimitfor"+poiname:
            alreadyExists = True

    if alreadyExists:
        print( f"asimovDataAtLimitfor{poiname} already exists")
    else:
        data = wsm.data("obsData")
        
        mc = wsm.obj("ModelConfig")

        tmpit = pois.createIterator()
        tmpn = tmpit.Next()
        while tmpn:
            tmpname = tmpn.GetName()
            if tmpname == poiname:
                poi = tmpn
            tmpn = tmpit.Next()

        poi.setVal(med);

        allParams = mc.GetPdf().getParameters(data);
        ROOT.RooStats.RemoveConstantParameters(allParams)

        globObs = ROOT.RooArgSet("globObs")
        asimov_data = ROOT.RooStats.AsymptoticCalculator.MakeAsimovData(mc, allParams, globObs)

        asimov_data.SetName(f"asimovDataAtLimitfor{poiname}")
        wsm.rfimport(asimov_data)

        print( "Data contained in the modified workspace: ")
        allData = wsm.allData()
        while allData.size() > 0:
            data = allData.front()
            allData.pop_front()
            print( "   ==>",data.GetName())
    
        wsm.writeToFile("output/"+ws+"/workspaces/combined/"+mass+".root",False)
