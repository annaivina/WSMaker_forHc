#!/usr/bin/env python
""" A script to plot the nuisance parameter pulls from different workspaces 

Usage, basic: 
       python scripts/comparePulls.py -w wsName -a fit type 

       Given a single workspace name it will plot the pulls for the fit type
       provided and for its data/Asimov counterpart
       EX: python scripts/comparePulls.py -w wsName -a 2  (-> Will compare to fit 7)

Usage, WS list: 
       Given a list of workspace names and fit type it will plot the pulls
       for the different workspaces
       EX: python scripts/comparePulls.py -w wsNamev1 wsNamev2 -a 4

Usage, WS version list: 
       Given a base workspace name (version wildcarding with {0}) and a few versions
       it will plot the pulls for the different workspace versions
       EX: python scripts/comparePulls.py -w wsName{0} -v v1 v2 -a 4

Usage, Legends from command line:
       Attributes a legend for each comparison case
       EX: python scripts/comparePulls.py -w wsNamev1 wsNamev2  -a 4 -l legWS1 legWS2 
       EX: python scripts/comparePulls.py -w wsName{0} -v v1 v2 -a 4 -l legv1  legv2 (legend default is the version names)
"""

import sys
import os
import argparse
import array 

import ROOT
from ROOT import gDirectory, gROOT

import runFitCrossCheck
import makeReducedDiagPlots
import analysisPlottingConfig

def main(cfg, versions, basedir_fcc, plotdir = '.', specialGroup=[], legend="None", show_pulls=True, comp_cond=False):

    if len(versions)<1:
        print( "Nothing to merge, aborting")
        return
    os.system("mkdir -vp "+plotdir)
    gROOT.SetBatch(True)
    ROOT.gSystem.Load("libMatrix.so")
    ROOT.gSystem.Load("libRooFit.so")
    ROOT.gSystem.Load("libWSMaker.so")
    pullplots = []
    axiss = []
    nuiss = []
    pullss = []
    isAsimov = []

    #print "versions ", versions
    for v in versions:
        directory = basedir_fcc.format(v)
        fname = f"{directory}/FitCrossChecks.root"
        print( "Will use fcc file ", fname)
        pull, corr = get_nuis_corr(cfg, fname, is_asimov = cfg._is_asimov, inv_cond = False)
        isAsimov.append(cfg._is_asimov)
        pullplots.append(pull)
        nuis, pulls = initial_sort(pull)
        nuiss.append(nuis)
        pullss.append(pulls)
        # If only one workspace is provided get the fit counterpart (if data: get asimov; if asimov: get data)
        if len(versions) == 1 and comp_cond:
            if legend == "None":
                legend = []
                # make the proper legend
                legend.append("#splitline{{{asimov}}}{{#bf{{{un}cond. fit}}{mu}}}".format
                              (asimov="Asimov (#mu="+str(cfg._mu)+")" if cfg._is_asimov else "Data", 
                               un="un" if not cfg._is_conditional else "",
                               mu=" #mu="+str(cfg._mu) if cfg._is_conditional else ""))
                legend.append("#splitline{{{asimov}}}{{#bf{{{un}cond. fit}}{mu}}}".format
                              (asimov="Asimov (#mu="+str(cfg._mu)+")" if cfg._is_asimov else "Data", 
                               un="" if not cfg._is_conditional else "un", 
                               mu=" #mu="+str(cfg._mu) if not cfg._is_conditional else ""))
                              
            pull, corr = get_nuis_corr(cfg, fname, is_asimov = cfg._is_asimov, inv_cond = comp_cond)
            pullplots.append(pull)
            nuis, pulls = initial_sort(pull)
            nuiss.append(nuis)
            pullss.append(pulls)
            isAsimov.append(cfg._is_asimov)
        elif len(versions) == 1:
            if legend == "None":
                legend = []
                # make the proper legend
                legend.append("#splitline{{{asimov}}}{{#bf{{{un}cond. fit}}{mu}}}".format
                              (asimov="Asimov (#mu="+str(cfg._mu)+")" if cfg._is_asimov else "Data", 
                               un="un" if not cfg._is_conditional else "",
                               mu=" #mu="+str(cfg._mu) if cfg._is_conditional and not cfg._is_asimov else ""))
                legend.append("#splitline{{{asimov}}}{{#bf{{{un}cond. fit}}{mu}}}".format
                              (asimov="Data" if cfg._is_asimov else "Asimov (#mu="+str(cfg._mu)+")", 
                               un="un" if not cfg._is_conditional else "", 
                               mu=" #mu="+str(cfg._mu) if cfg._is_conditional and cfg._is_asimov else ""))
                              
            pull, corr = get_nuis_corr(cfg, fname, is_asimov = not cfg._is_asimov, inv_cond = False)
            pullplots.append(pull)
            nuis, pulls = initial_sort(pull)
            nuiss.append(nuis)
            pullss.append(pulls)
            isAsimov.append(not cfg._is_asimov)

    res = ROOT.std.vector('TGraph*')()
    pulls = ROOT.std.vector('TGraph*')()
    for n in nuiss:
        res.push_back(n)
    ROOT.PU.mergeTGraphAxis(res, True)
    for p in pullss:
        pulls.push_back(p)
    ROOT.PU.mergeTGraphAxis(pulls, True)
    for n in nuiss:
        axiss.append(n.GetXaxis())

    # if config says so, drops the pulls
    if not show_pulls:
        for i in range(len(pullss)):
            pullss[i].Delete()
            pullss[i] = None

    # play with canvas of NP
    # reference:
    g_2s = pullplots[0].GetListOfPrimitives().At(1)
    g_1s = pullplots[0].GetListOfPrimitives().At(2)
    amin = axiss[0].GetXmin()
    amax = axiss[0].GetXmax()
    length = int(amax-amin)+1

    for i in range(length):
        g_2s.SetPoint(i,amin+i,-2)
        g_1s.SetPoint(i,amin+i,-1)
    for i in range(length):
        g_2s.SetPoint(2*length-i-1,amin+i,2)
        g_1s.SetPoint(2*length-i-1,amin+i,1)

    # then plot only interesting things
    res = reduce_all(nuiss, g_2s, g_1s, axiss, excludes=ROOT.std.vector(ROOT.TString)(), pullss=pullss)
    nuiss = [n.Clone() for n in res[0]]
    axiss = [nuis.GetXaxis().Clone() for nuis in res[0]]
    nuis_plot(cfg, plotdir, "all", *res, isAsimov=isAsimov, hmin=-3, hmax=3, legend=legend)
    res = reduce_all(nuiss, g_2s, g_1s, axiss, excludes=makeReducedDiagPlots.vector_TString("bin"), pullss=pullss)
    nuis_plot(cfg, plotdir, "allExceptGammas", *res, isAsimov=isAsimov, hmin=-3, hmax=3, legend=legend)

    #New classification

    # Modified by Elias, so it reads in the cfg (copied from makeReducedDiagPlots
    for key in cfg.cov_classification:
        
        name = key
        zero = cfg.cov_classification[key][0]
        inc_args = cfg.cov_classification[key][1]
        exc_args = cfg.cov_classification[key][2]
        gammaStyle=False
        if len(cfg.cov_classification[key])>3: gammaStyle = cfg.cov_classification[key][3]

        #print "key ", key
        #print "Including arguments ", inc_args
        #print "Excluding arguments ", exc_args

        if len(inc_args) > 0 and len(exc_args) > 0:
            res = reduce_all(nuiss, g_2s, g_1s, axiss,
                    includes=makeReducedDiagPlots.vector_TString(*inc_args), excludes=makeReducedDiagPlots.vector_TString(*exc_args), pullss=pullss)
        elif len(inc_args) > 0:
            res = reduce_all(nuiss, g_2s, g_1s, axiss, includes=makeReducedDiagPlots.vector_TString(*inc_args), pullss=pullss)
        elif len(exc_args) > 0:
            res = reduce_all(nuiss, g_2s, g_1s, axiss, excludes=makeReducedDiagPlots.vector_TString(*exc_args), pullss=pullss)
        else:
            res = reduce_all(nuiss, g_2s, g_1s, axiss, pullss=pullss)

        if "Gamma" in name or gammaStyle:
            nuis_plot(cfg, plotdir, name, *res, isAsimov=isAsimov, hmin=0.8, hmax=1.2, legend=legend)
        else:
            nuis_plot(cfg, plotdir, name, *res, isAsimov=isAsimov, legend=legend)

    suspicious_NP = []
    for nuis,axis in zip(nuiss, axiss):
        suspicious_NP.extend(makeReducedDiagPlots.flag_suspicious_NP(cfg, nuis, axis, .5, .5))
    res = reduce_all(nuiss, g_2s, g_1s, axiss, includes=makeReducedDiagPlots.vector_TString(*suspicious_NP), pullss=pullss)
    nuis_plot(cfg, plotdir, "Suspicious", *res, isAsimov=isAsimov, hmin=-3, hmax=3, legend=legend)

    for i in range(0,len(specialGroup)):
        special = []
        specialGroup[i] = specialGroup[i].replace("ATLAS_", "")
        special.append(specialGroup[i])
        #print " Making plot for special category: ", specialGroup[i]
        #print " Including arguments ", special
        res = reduce_all(nuiss, g_2s, g_1s, axiss, includes=makeReducedDiagPlots.vector_TString(*special), pullss=pullss)
        nuis_plot(cfg, plotdir, specialGroup[i], *res, isAsimov=isAsimov, hmin=-3, hmax=3, legend=legend)


def nuis_plot(cfg, plotdir, name, nuiss, yellow, green, pullss, isAsimov, h=None, hmin=-5, hmax=5, legend="None"):

    # if supported by the analysisPlottingConfig, sort everything correctly
    if hasattr(cfg, "get_NP_key"):
        nuiss = sort_TGraphs(nuiss, key = cfg.get_NP_key)
        pullss = sort_TGraphs(pullss, key = cfg.get_NP_key)

    width = 1500 if os.getenv("ANALYSISTYPE") == "MonoH" else 1000
    legX1 = 0.96 if os.getenv("ANALYSISTYPE") == "MonoH" else 0.9
    legX2 = 0.995 if os.getenv("ANALYSISTYPE") == "MonoH" else 0.98
    c = ROOT.TCanvas("c","c",width,600)
    leg = ROOT.TLegend(legX1,0.85-0.1*len(nuiss),legX2,1.)
    leg.SetLineColor(0)

    padX2 = 0.96 if os.getenv("ANALYSISTYPE") == "MonoH" else 0.9
    pad1 = ROOT.TPad("p1","p1",0.,0.,padX2,1.)
    pad1.Draw()
    if legend!="None":
        pad1.cd()
    #print "legend ",legend
    if os.getenv("ANALYSISTYPE") == "boostedVHbbRun2":
        if hmin < -1:
            hmax = hmax + 4
            hmin = hmin - 0.5
        else:
            hmax = hmax + 1
            hmin = hmin - 0.5
    elif "DDttbar" in name:
        hmin=-1.2
        hmax=4.8
    else: 
        if hmin < -1:
            hmax = hmax + 4
            hmin = hmin - 1
        else:
            hmax = hmax + 2
            hmin = hmin - 1

    if h is not None:
        h.SetMinimum(hmin)
        h.SetMaximum(hmax)
        ya = h.GetYaxis()
        h.Draw()
        nuiss[0].Draw("pz")
    else:
        nuiss[0].SetMinimum(hmin)
        nuiss[0].SetMaximum(hmax)
        nuiss[0].Draw("pza")
        ya = nuiss[0].GetYaxis()
    nuiss[0].SetTitle("")
    ya.SetTitle("pull")
    ya.SetTitleOffset(.5)
    ya.SetTickLength(0)
    if pullss[0] is not None:
        pullss[0].Draw("p")
    yellow.Draw("f")
    green.Draw("f")
    colors=[1,2,ROOT.kBlue-4,6,ROOT.kGray+1]
    markerSize = 1
    lineWidth = 3
    if name == "all" or name == "allExceptGammas":
        markerSize = 0.5
        lineWidth = 1
    markerShift = 0.18
    if os.getenv("ANALYSISTYPE") == "VHqqRun2":
        markerShift = 0.3
    

    # remove blinded NP from plot
    isBlinded=int(os.getenv("IS_BLINDED"))
    removeLeg=[]
    if isBlinded:
        for iF in range(0,len(isAsimov)):
            if isAsimov[iF]: continue
            # first pass: if all np removed in nuiss[0], all drawing properties fail
            # if that is the case, keep all points but set size to 0 instead
            nRemove=0
            nNuis=nuiss[iF].GetXaxis().GetNbins()
            for i in range(1,nNuis+1):
                npname=nuiss[iF].GetXaxis().GetBinLabel(i)
                remove=False
                for exclude in cfg.cov_blind:
                    if not exclude in npname: continue
                    remove=True
                    break
                if remove: nRemove+=1
            if nRemove == nNuis:
                nuiss[iF].SetMarkerSize(0)
                nuiss[iF].SetLineWidth(0)
                removeLeg.append(iF)
            else:
                # if not all points removed, apply removal
                for i in range(1,nNuis+1):
                    npname=nuiss[iF].GetXaxis().GetBinLabel(i)
                    #print "-> ",npname
                    remove=False
                    for exclude in cfg.cov_blind:
                        #print exclude," in ",npname," ?"
                        if not exclude in npname: continue
                        #print "yes"
                        remove=True
                        break
                    if not remove: continue
                    #print iF," ",i,": remove ",npname
                    # special loop, name order =/= point order ...
                    # use GetN here: x-axis contain name of NP not
                    # necessarily present in fit, GetN access nPoints in TGRaph
                    nPoints=nuiss[iF].GetN()
                    for j in range(0,nPoints):
                        x=nuiss[iF].GetX()[j]
                        if x<i and i-1<x:
                            #print "Dead: ",i," at ",x
                            nuiss[iF].RemovePoint(j)
                            break
                    #print "After remove: ",nuiss[iF].GetX()," =?= ", nuiss[iF].GetN()

    for num,nuis in enumerate(nuiss):
        if num == 0:
            continue
        if num == 1:
            ROOT.PU.shiftTGraph(nuis, markerShift, True)
            if pullss[num] is not None:
                ROOT.PU.shiftTGraph(pullss[num], markerShift, True)
        if num == 2:
            ROOT.PU.shiftTGraph(nuis, -markerShift, True)
            if pullss[num] is not None:
                ROOT.PU.shiftTGraph(pullss[num], -markerShift, True)
        if num > 2:
            print( "WARNING: this is going to be ugly and hard to read")
            ROOT.PU.shiftTGraph(nuis, (num-1)*markerShift, True)
            if pullss[num] is not None:
                ROOT.PU.shiftTGraph(pullss[num], (num-1)*markerShift, True)
        col = colors[num]
        if not num in removeLeg:
            nuis.SetMarkerSize(markerSize)
            nuis.SetLineWidth(lineWidth)
        nuis.SetMarkerColor(col)
        nuis.SetLineColor(col)
        nuis.Draw("pz")
        
        if len(legend)>num and not num in removeLeg:
            leg.AddEntry(nuis,legend[num],"ep")
        
        if pullss[num] is not None and not num in removeLeg:
            pullss[num].SetMarkerSize(markerSize)
            pullss[num].SetMarkerColor(col)
            pullss[num].Draw("pz")

    if not 0 in removeLeg:
        nuiss[0].SetMarkerSize(markerSize)
        nuiss[0].SetLineWidth(lineWidth)
    nuiss[0].Draw("pz")
    
    if legend != "None" and not 0 in removeLeg:
        leg.AddEntry(nuiss[0],legend[0],"ep")

    if pullss[0] is not None and not 0 in removeLeg:
        pullss[0].SetMarkerSize(markerSize)
        pullss[0].Draw("p")
    nuiss[0].GetXaxis().LabelsOption("v")

    label = ROOT.TLatex()
    label.SetTextSize(0.045)
    offset = 0
    if  nuiss[0].GetXaxis().GetNbins() > 0:
        offset = 0.2 * nuiss[0].GetXaxis().GetNbins() * label.GetTextSize()
    if name == "Jet" or name == "VH" or name == "largeRJet" or name == "smallRJet" or "Gamma" in name or "DDttbar" in name:
        label.SetTextSize(0.027)
    if os.getenv("ANALYSISTYPE") == "VHqqRun2":
        if name == "MET" or name == "Lepton" or name == "MJ" or name == "Zjets" or name == "Wjets" or name == "Norm" or name == "Top" or name == "BTag":
            label.SetTextSize(0.028)
        elif name=="FloatNorm":
            label.SetTextSize(0.034)
        else:
            label.SetTextSize(0.023)
    if os.getenv("ANALYSISTYPE") == "VHbbRun2":
        if name == "MET" or name == "Lepton" or name == "MJ" or name == "Zjets" :
            label.SetTextSize(0.036)
        elif name == "Top" :
            label.SetTextSize(0.034)
    if os.getenv("ANALYSISTYPE") == "VHccRun2":
        if name == "MET" or name == "Lepton" or name == "MJ" or name == "Zjets" or name == "Wjets" or name == "Norm" or name == "Top" or name == "BTag":
            label.SetTextSize(0.034)
        elif "Gamma" in name:
            label.SetTextSize(0.025)
        elif "DTnorm" in name or "DTshape" in name or "DTall" in name:
            label.SetTextSize(0.025)
    if name == "all" or name == "allExceptGammas":
        if os.getenv("ANALYSISTYPE") == "boostedVHbbRun2":
            label.SetTextSize(0.018)
        elif os.getenv("ANALYSISTYPE") == "VHbbRun2" or os.getenv("ANALYSISTYPE") == "VHqqRun2" or os.getenv("ANALYSISTYPE") == "MonoH":
            label.SetTextSize(0.014)
        else:
            label.SetTextSize(0.023)
        offset = 0.4 

    label.SetTextAngle(90)
    label.SetTextFont(42)
    for i in range(1, nuiss[0].GetXaxis().GetNbins() + 1):
        labelStr = ROOT.TString(nuiss[0].GetXaxis().GetBinLabel(i))
        nuiss[0].GetXaxis().SetBinLabel(i, "")
        xpos = nuiss[0].GetXaxis().GetBinCenter(i) + offset

        # keep old renaming around for backward compatibility
        if not hasattr(cfg, "get_nice_NP_name"):
            get_nice_NP_name(labelStr)

        if os.getenv("ANALYSISTYPE") == "VHbbRun2":
            if "Gamma" in name and "allExceptGammas" not in name:
                label.DrawText(xpos, 1.5, labelStr.Data())
            else :
                label.DrawText(xpos, 2.2, labelStr.Data())

        if os.getenv("ANALYSISTYPE") == "VHccRun2":
            if "Gamma" in name and "allExceptGammas" not in name:
                label.DrawText(xpos, 2.0, labelStr.Data())
            else :
                label.DrawText(xpos, 2.2, labelStr.Data())

        if os.getenv("ANALYSISTYPE") == "boostedVHbbRun2":
            if "Gamma" in name and "allExceptGammas" not in name:
                label.DrawText(xpos, 1.5, labelStr.Data())
            else: 
                label.DrawText(xpos, 2.2, labelStr.Data())
        elif os.getenv("ANALYSISTYPE") != "VHbbRun2" and os.getenv("ANALYSISTYPE") != "VHccRun2":
            label.DrawText(xpos, 2.2, labelStr.Data())  

    label.SetTextSize(0.03)
    for num,nuis in enumerate(nuiss):
        if num in removeLeg: continue
        # add values in all cases by commenting the following 2 lines
        #if name is "all":
        #    continue
        xVals = nuis.GetX()
        yVals = nuis.GetY()
        yErr = nuis.GetEYhigh()
        xShift=0
        if (os.getenv("ANALYSISTYPE") == "VHbbRun2" or os.getenv("ANALYSISTYPE") == "MonoH") and len(nuiss)==2 and len(xVals)>1 :
            if num==0 : xShift = -abs(xVals[0]-xVals[1])/9.
            else : xShift = abs(xVals[0]-xVals[1])/9.
        for i in range(0, nuis.GetN()):
            yPos = hmin + 0.2
            labelStr = f"{abs(yVals[i]):.2f} #pm {yErr[i]:.2f}"
            if (os.getenv("ANALYSISTYPE") == "VHqqRun2") and name=="FloatNorm" :
                labelStr = f"{abs(yVals[i]):.3f} #pm {yErr[i]:.3f}"
            if name == "all" or name == "allExceptGammas":
                if os.getenv("ANALYSISTYPE") == "MonoH" or os.getenv("ANALYSISTYPE") == "AZHeavyH":
                    label.SetTextSize(0.007)
                else:
                    label.SetTextSize(0.018)
            if name == "BTag" or name == "Jet" and os.getenv("ANALYSISTYPE") == "VHbbRun2":
                label.SetTextSize(0.022)
            if os.getenv("ANALYSISTYPE") == "VHbbRun2" and (name == "all" or name == "allExceptGammas"):
                label.SetTextSize(0.014)
            label.DrawLatex(xVals[i]+xShift, yPos, labelStr)
            if yVals[i] < 0:
                label.DrawLatex(xVals[i]+xShift, yPos-0.11, "-")

    ROOT.gPad.SetTopMargin(ROOT.gPad.GetTopMargin()*0.15)
    ROOT.gPad.SetBottomMargin(ROOT.gPad.GetBottomMargin()*0.15)
    ROOT.gPad.SetLeftMargin(ROOT.gPad.GetLeftMargin()*.4)
    ROOT.gPad.SetRightMargin(ROOT.gPad.GetRightMargin()*.05)
    ROOT.gPad.Update()
    if legend!="None":
        c.cd()
        leg.Draw()
    for ext in cfg.formats:
        c.Print(f"{plotdir}/NP_{name}.{ext}")

    for n in nuiss:
        n.Delete()

def reduce_all(nuiss, yellow, green, axiss, excludes=None, includes=None, pullss=None):
    new_nuis = []
    new_pulls = []
    for nuis,pulls,axis in zip(nuiss, pullss, axiss):
        if includes is not None and excludes is not None:
            tmp_nuis = ROOT.PU.reduceTGraphAxisInclude(nuis, axis, True, includes)
            if tmp_nuis.GetN() > 0:
                new_nuis.append(ROOT.PU.reduceTGraphAxisExclude(tmp_nuis, tmp_nuis.GetXaxis(), True, excludes))
            else:
                new_nuis.append(tmp_nuis)
            if pulls is not None:
                tmp_pulls = ROOT.PU.reduceTGraphAxisInclude(pulls, axis, True, includes)
                if tmp_pulls.GetN() > 0:
                    new_pulls.append(ROOT.PU.reduceTGraphAxisExclude(tmp_pulls, tmp_pulls.GetXaxis(), True, excludes))
                else:
                    new_pulls.append(tmp_pulls)
            else:
                new_pulls.append(None)
        elif excludes is not None:
            new_nuis.append(ROOT.PU.reduceTGraphAxisExclude(nuis, axis, True, excludes))
            if pulls is not None:
                new_pulls.append(ROOT.PU.reduceTGraphAxisExclude(pulls, axis, True, excludes))
            else:
                new_pulls.append(None)
        elif includes is not None:
            new_nuis.append(ROOT.PU.reduceTGraphAxisInclude(nuis, axis, True, includes))
            if pulls is not None:
                new_pulls.append(ROOT.PU.reduceTGraphAxisInclude(pulls, axis, True, includes))
            else:
                new_pulls.append(None)
    max_axis = new_nuis[0].GetXaxis().GetXmax()
    new_y = yellow.Clone(yellow.GetName()+"_reduced")
    new_g = green.Clone(yellow.GetName()+"_reduced")
    ROOT.PU.removeTGraphPointsAbove(new_y, True, max_axis)
    ROOT.PU.removeTGraphPointsAbove(new_g, True, max_axis)
    return [new_nuis, new_y, new_g, new_pulls]

def get_nuis_corr(cfg, tfile, is_asimov, inv_cond):
    f = ROOT.TFile.Open(tfile)
    mu = "1"
    print( "POI", cfg._mu, cfg._is_asimov)

    if is_asimov:
        stub = "Asimov"
        f.cd("PlotsAfterFitToAsimov")
        mu = str(cfg._mu)
    else:
        stub = "Global"
        f.cd("PlotsAfterGlobalFit")
        mu = str(cfg._mu)
    if cfg._is_conditional:
        condStr="conditionnal"
        if inv_cond :
            condStr="unconditionnal"
            gDirectory.cd(condStr)
        else :
            gDirectory.cd(condStr+"_MuIsEqualTo_"+mu)
        p_nuis = gDirectory.Get("can_NuisPara_"+stub+"Fit_"+condStr+"_mu"+mu)
        p_corr = gDirectory.Get("can_CorrMatrix_"+stub+"Fit_"+condStr+"_mu"+mu)
    else:
        condStr="unconditionnal"
        if inv_cond :
            condStr="conditionnal"
            gDirectory.cd(condStr+"_MuIsEqualTo_"+mu)
        else :
            gDirectory.cd(condStr)
        p_nuis = gDirectory.Get("can_NuisPara_"+stub+"Fit_"+condStr+"_mu"+mu)
        p_corr = gDirectory.Get("can_CorrMatrix_"+stub+"Fit_"+condStr+"_mu"+mu)

    return p_nuis, p_corr

def get_nice_NP_name(name):
    name.ReplaceAll("Sys","")
    name.ReplaceAll("FT_EFF_Eigen","FT")
    name.ReplaceAll("stat_Region_","Gamma_")
    name.ReplaceAll("MCStat_","ddttbar_")
    name.ReplaceAll("extrapolation","extrap")
    name.ReplaceAll("JET_21NP_","")
    name.ReplaceAll("JET_23NP_","")
    name.ReplaceAll("JET_CR_JET_JER","JER")
    name.ReplaceAll("JET_CR_JET","JET")
    name.ReplaceAll("JET_JER_SINGLE_NP","JER")
    name.ReplaceAll("JET_GroupedNP","JET")
    name.ReplaceAll("EtaIntercalibration","EtaIntercal")
    name.ReplaceAll("Flavor_Composition","FlavComp")
    name.ReplaceAll("Pileup","PU")
    name.ReplaceAll("SoftTerms","ST")
    name.ReplaceAll("multijet","QCDMJ")
    name.ReplaceAll("Multijet","QCDMJ")
    name.ReplaceAll("dist","d")
    name.ReplaceAll("MedHighPtv","Ptv")
    name.ReplaceAll("RatioHP", "R_HP")
    name.ReplaceAll("RatioPtv", "R_Ptv")
    name.ReplaceAll("RatioSR", "R_SR")
    name.ReplaceAll("Ratiottbar", "R_ttbar")
    name.ReplaceAll("L_BMin400", "L_400")
    name.ReplaceAll("Ptv_BMin400", "Ptv_400")
    name.ReplaceAll("FATJET","FJ")
    name.ReplaceAll("MJJMR", "FJ_JMR")
    name.ReplaceAll("Medium_JET_Comb","JMSJES")
    name.ReplaceAll("_Kin","")
    name.ReplaceAll("MbbBoosted","mJShape")
    name.ReplaceAll("DSRnoaddbjetsr","SR")
    name.ReplaceAll("DSRtopaddbjetcr","CR")
    name.ReplaceAll("Y2015_","")
    name.ReplaceAll("_TOTAL_1NPCOR_PLUS_UNCOR","_TOTAL")
    name.ReplaceAll("MJVHPH7","TheoryUEPSShape")

    if os.getenv("ANALYSISTYPE") == "VHbbRun2":
        name.ReplaceAll("Gamma_", "")
        name.ReplaceAll("ddttbar_", "")
        name.ReplaceAll("Y6051_","")
        name.ReplaceAll("incJet1_","")
        name.ReplaceAll("T2_","")
        name.ReplaceAll("BMax150_BMin75","75-150")
        name.ReplaceAll("BMax250_BMin150","150-250")
        name.ReplaceAll("BMin250","250-inf")
        name.ReplaceAll("BMin75", "75-150")
        name.ReplaceAll("BMin150", "150-250")

    if os.getenv("ANALYSISTYPE") == "VHccRun2":
        name.ReplaceAll("bveto", "btagging")
        name.ReplaceAll("Gamma_", "")
        name.ReplaceAll("DT2", "DTnorm")
        name.ReplaceAll("DT3", "DTshape")
        name.ReplaceAll("DT4", "DTcorr")
        name.ReplaceAll("Y6051_","")
        name.ReplaceAll("MUR_BMin75_Ttbar", "FSR_75_Ttbar")
        name.ReplaceAll("MUR_BMin150_Ttbar", "FSR_150_Ttbar")
        name.ReplaceAll("MUR_BMin75_Stop", "FSR_75_Stop")
        name.ReplaceAll("MUR_BMin150_Stop", "FSR_150_Stop")
        name.ReplaceAll("norm_Wmf_BMin150", "norm_Wmf")
        name.ReplaceAll("norm_Whf_BMin150", "norm_Whf")
        name.ReplaceAll("incJet1_","")
        name.ReplaceAll("BMin150", "150-inf")
        name.ReplaceAll("BMax150_BMin75","75-150")
        name.ReplaceAll("BMax250_BMin150","150-250")
        name.ReplaceAll("BMin250","250-inf")
        name.ReplaceAll("BMin75", "75-150")
        name.ReplaceAll("norm_Ttbar", "norm_Ttbar_L2")
        name.ReplaceAll("TtbarNorm_L0_Topbq", "TopbqNorm_L0")
        name.ReplaceAll("TtbarNorm_L0_Toplq", "ToplqNorm_L0")
        name.ReplaceAll("WtauNorm", "WtauNorm_L0")
        name.ReplaceAll("shape_ShMGPy8_mCC", "ShMGPy8")
        name.ReplaceAll("shape_mCC_Pow_aMC", "Pow_aMC")
        name.ReplaceAll("shape_mCC_Her_Pyt", "Her_Pyt")
        name.ReplaceAll("Top_shape_mCC_ISR_Topbq", "Topbq_ISR")
        name.ReplaceAll("Top_shape_mCC_ISR_Toplq", "Toplq_ISR")
        name.ReplaceAll("shape_PwPy8_mCC", "PwPy8")
        name.ReplaceAll("TAUS_TRUEHADTAU_SME_TES_DETECTOR", "TAUS_DETECTOR")
        name.ReplaceAll("TAUS_TRUEHADTAU_SME_TES_INSITU", "TAUS_INSITU")
        name.ReplaceAll("TAUS_TRUEHADTAU_SME_TES_MODEL", "TAUS_MODEL")
        name.ReplaceAll("Wmftau", "Wmf")
        if "Gamma" in name and "allExceptGammas" not in name:
            name.ReplaceAll("dmBB_","")
            name.ReplaceAll("DSR_","")

    if os.getenv("ANALYSISTYPE") == "boostedVHbbRun2":
        name.ReplaceAll("Gamma_", "")
        if "Gamma" in name and "allExceptGammas" not in name:
            name.ReplaceAll("Y6051_","")
            name.ReplaceAll("incJet1_","")
            name.ReplaceAll("dmBB_","")
            name.ReplaceAll("BMin400_","400_")
            name.ReplaceAll("BMin250_BMax400_","250_")
            name.ReplaceAll("Fat1_","")
            name.ReplaceAll("T2_","")
            name.ReplaceAll("J0_L2_DSR_inc250","L2_SR_250-400_")
            name.ReplaceAll("400_incDSR_L2_J0","L2_SR_400_")
            name.ReplaceAll("BMax400_BMin250_incSR_L1_J0_","L1_HPSR_250-400_")
            name.ReplaceAll("400_incSR_L1_J0_","L1_HPSR_400_")
            name.ReplaceAll("400_incCR_L1_J0_","L1_CR_400_")
            name.ReplaceAll("400_incSR_L1_J1_","L1_LPSR_400_")
            name.ReplaceAll("J0_L1_CR_inc250_","L1_CR_250-400_")
            name.ReplaceAll("J1_L1_SR_inc250_","L1_LPSR_250-400_")
            name.ReplaceAll("J0_L0_CR_inc250_","L0_CR_250-400_")
            name.ReplaceAll("J1_L0_SR_inc250_","L0_LPSR_250-400_")
            name.ReplaceAll("BMax400_BMin250_incSR_L0_J0_","L0_HPSR_250-400_")
            name.ReplaceAll("400_incSR_L0_J0","L0_HPSR_400_")
            name.ReplaceAll("400_incSR_L0_J1","L0_LPSR_400_")
            name.ReplaceAll("400_incCR_L0_J0","L0_CR_400_")

def rename_NPs(axis, renamer):
    for i in range(1, axis.GetNbins() + 1):
        axis.SetBinLabel(i, renamer(axis.GetBinLabel(i)))

    return axis

def get_point_coords(graph, ind):
    x = array.array('d', [0])
    y = array.array('d', [0])
    graph.GetPoint(ind, x, y)
    x, y  = x[0], y[0]            
    return x, y
    
def get_point_labels(graph, axis):
    labels = []

    for cur_ind in range(graph.GetN()):
        cur_x, cur_y = get_point_coords(graph, cur_ind)
        cur_label = axis.GetBinLabel(axis.FindBin(cur_x))
        labels.append(cur_label)

    return labels

def reorderAxis(graph, axis, sorted_labels): 
    axis_new = axis.Clone()
    ROOT.SetOwnership(axis_new, False)

    # sort the axis
    for ind, cur_label in enumerate(sorted_labels):
        axis_new.SetBinLabel(ind + 1, cur_label)

    # sort the graph accordingly
    for cur_ind in range(graph.GetN()):

        cur_point_x, cur_point_y = get_point_coords(graph, cur_ind)
        cur_label = axis.GetBinLabel(axis.FindBin(cur_point_x))
        cur_bin_x = axis.GetBinCenter(axis.FindBin(cur_point_x))

        target_ind = sorted_labels.index(cur_label)
        target_bin_x = axis.GetBinCenter(target_ind + 1)

        graph.SetPoint(cur_ind, cur_point_x + (target_bin_x - cur_bin_x), cur_point_y)

    if sorted_labels:
        axis.GetLabels().Rehash(axis.GetNbins() + 2)

    return graph, axis_new

def sort_TGraphs(graphs, key):

    # give up right away if everything is empty
    if all([graph is None for graph in graphs]):
        return graphs

    # remove graphs that don't exit
    empty_graph_inds = [ind for ind in range(len(graphs)) if graphs[ind] is None]
    graphs = [graph for graph in graphs if graph is not None]

    axes = [graph.GetXaxis() for graph in graphs]

    # get all available labels ...
    all_labels = []
    for graph, axis in zip(graphs, axes):
        all_labels += get_point_labels(graph, axis)
    all_labels = list(set(all_labels)) # remove duplicates

    # ... sort them ...
    sorted_labels = sorted(all_labels, key = key)
        
    # ... and rearrange the graphs
    sorted_graphs = []
    for graph, axis in zip(graphs, axes):
        sorted_graph, sorted_axis = reorderAxis(graph, axis, sorted_labels)
        ROOT.PU.setTGraphAxis(sorted_graph, sorted_axis, True)
        sorted_graphs.append(sorted_graph)

    # put any empty graphs back
    for ind in empty_graph_inds:
        sorted_graphs.insert(ind, None)

    return sorted_graphs

def initial_sort(can_pulls):
    h = can_pulls.GetListOfPrimitives().At(0)
    axis = h.GetXaxis()
    axis_pulls = h.GetXaxis().Clone("atemp")
    nuis = can_pulls.GetListOfPrimitives().At(3)
    pulls = can_pulls.GetListOfPrimitives().At(4)

    # rename all NPs to something nicer, if this is supported by the analysisPlottingConfig
    if hasattr(cfg, "get_nice_NP_name"):
        axis = rename_NPs(axis, renamer = cfg.get_nice_NP_name)
        axis_pulls = rename_NPs(axis_pulls, renamer = cfg.get_nice_NP_name)

    # function pointers not supported in PyROOT... have to workaround
    gROOT.ProcessLine("#include \""+os.environ["WORKDIR"]+"/WSMaker/plotUtils.hpp\"")
    gROOT.ProcessLine("n = (TGraph*)"+str(ROOT.AddressOf(nuis)[0]))
    gROOT.ProcessLine("a = (TAxis*)"+str(ROOT.AddressOf(axis)[0]))
    gROOT.ProcessLine("PU::sortTGraphAxis(n, a, true, PU::comp_sysNames)")
    gROOT.ProcessLine("p = (TGraph*)"+str(ROOT.AddressOf(pulls)[0]))
    gROOT.ProcessLine("a2 = (TAxis*)"+str(ROOT.AddressOf(axis_pulls)[0]))
    gROOT.ProcessLine("PU::sortTGraphAxis(p, a2, true, PU::comp_sysNames)")
    ROOT.PU.setTGraphAxis(nuis, axis, True)
    ROOT.PU.setTGraphAxis(pulls, axis_pulls, True)
    return nuis,pulls


if __name__ == "__main__":
    
    class MyParser(argparse.ArgumentParser):
        def error(self, message):
            sys.stderr.write('error: %s\n' % message)
            self.print_help()
            sys.exit(2)

    parser = MyParser(description='Compare nuisance parameter pulls from different workspaces', formatter_class=argparse.RawTextHelpFormatter)
    
    parserReq = parser.add_argument_group(title='required arguments')
    parserReq.add_argument('-w', '--workspace', nargs = '+', 
                        help = 'nominal workspace: output/{WSname}/fccs/FitCrossChecks.root -> pass {WSname}',
                        required=True, dest = 'workspace')
    parserReq.add_argument('-a', '--alg_type', default = 0,
                        help = """Fit number (or list of fits), from the following list of FCC options:
     2: unconditional ( start with mu=1 )
     4: conditional mu = 0
     5: conditional mu = 1
     6: run Asimov mu = 1 toys: randomize Poisson term
     7: unconditional fit to asimov where asimov is built with mu=1
     8: unconditional fit to asimov where asimov is built with mu=0
     9: conditional fit to asimov where asimov is built with mu=1
     10: conditional fit to asimov where asimov is built with mu=0""", 
                        required = True, dest = 'alg_type')
    parser.add_argument('-v', '--versions', nargs = '*',
                        help = "List of different workspace versions to compare (base workspace name with version wildcarded)",
                        default = [], dest = 'versions')
    parser.add_argument('-s', '--special', nargs = '*',
                        help = "List of patterns to create a special plot with only the NPs matching the patterns in the list",
                        default = [], dest = 'special')
    parser.add_argument('-l','--legend', nargs = '*',
                        help = "Legend of the workspace versions",
                        default = "None", dest = 'legend')
    parser.add_argument('-p','--plotdir',
                        help = "Output plot directory",
                        default = "output/pullComparisons", dest = 'plotdir')
    parser.add_argument('-c','--condition',
                        help = "compare an unconditional fit to its unconditional counter-part",
                        action = 'store_true', dest = 'comp_cond')
    parser.add_argument('-n','--no-pulls',
                        help = "do not show the pulls (squares)",
                        action = 'store_false', dest = 'show_pulls')
    args, pass_to_user = parser.parse_known_args()
        
    
    special = args.special
    plotdir = args.plotdir
    workspace = args.workspace
    versions = args.versions
    alg_type = args.alg_type    
    legend = args.legend
    show_pulls = args.show_pulls
    comp_cond = args.comp_cond

    if legend=="None" and len(versions)>0:
        legend = versions
   
    basedir_fcc = "output/{0}/fccs"
    if len(versions)==0:
        for i in range(0, len(workspace)):
            versions.append(workspace[i])
    else:
        basedir_fcc=f"output/{workspace[0]}/fccs" 
    print( "Running comparePulls for nominal workspace ", workspace)

    cfg = analysisPlottingConfig.Config(pass_to_user)
    alg = runFitCrossCheck.available_algs[int(alg_type)]
    mu = int(alg[1])
    is_conditional = False
    if alg[3] == "true":
        is_conditional = True
    is_asimov = False
    if "Asimov" in alg[0]:
        is_asimov = True
    cfg._is_conditional = is_conditional
    cfg._is_asimov = is_asimov
    cfg._mu = mu
    
    print( "Running for conditional? ", is_conditional, " for asimov? ", is_asimov, " what mu? ", mu)
    main(cfg, versions, basedir_fcc, plotdir = plotdir, specialGroup = special, legend = legend, show_pulls=show_pulls, comp_cond=comp_cond)
        
