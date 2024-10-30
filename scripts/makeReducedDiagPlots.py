#!/usr/bin/env python


import sys
import os
import argparse
import ctypes

import ROOT
from ROOT import gDirectory, gROOT, gStyle
#from ROOT import PU

import runFitCrossCheck
import analysisPlottingConfig

def main(cfg, version):#, directory, is_conditional=False, is_asimov=False, mu=None):
    # TODO this initialization is UGLY
    plotdir = f"$WORKDIR/../output/{version}/plots"
    try:
        os.system("mkdir -vp "+plotdir)
    except OSError:
        pass
    plotdir = f"$WORKDIR/../output/{version}/plots/fcc"
    try:
        os.system("mkdir -vp "+plotdir)
    except OSError:
        pass
    if cfg._is_asimov:
        dirname = "AsimovFit_"
        if cfg._mu is None:
            cfg._mu = 1 # default value
    else:
        dirname = "GlobalFit_"
        if cfg._mu is None:
            cfg._mu = 0 # default value
    if cfg._is_conditional:
        condname = "conditionnal_"
    else:
        condname = "unconditionnal_"
    muname = f"mu{cfg._mu}"
    mu = str(cfg._mu)

    plotdir = f"$WORKDIR/../output/{version}/plots/fcc/{dirname}{condname}{muname}"
    try:
        os.system("mkdir -vp "+plotdir)
    except OSError:
        pass

    gROOT.SetBatch(True)
    ROOT.gSystem.Load("libWSMaker.so")
    f = ROOT.TFile.Open(f"{cfg._fcc_directory}/FitCrossChecks.root")
    if cfg._is_asimov:
        f.cd("PlotsAfterFitToAsimov")
    else:
        f.cd("PlotsAfterGlobalFit")
    if cfg._is_conditional:
        gDirectory.cd(f"conditionnal_MuIsEqualTo_{mu}")
    else:
        gDirectory.cd("unconditionnal")

    p_chi2 = gDirectory.Get("Chi2PerChannel")
    if p_chi2 != None:
        hchi2 = p_chi2.GetListOfPrimitives().At(0)
        c2 = ROOT.TCanvas("c2","c2")
        hchi2.Draw()
        for ext in cfg.formats:
            c2.Print(f"{plotdir}/Chi2PerChannel.{ext}")

    p_nuis = gDirectory.Get(f"can_NuisPara_{dirname}{condname}{muname}")
    p_corr = gDirectory.Get(f"can_CorrMatrix_{dirname}{condname}{muname}")

    # Nice colors for correlation plots
    gROOT.ProcessLine("Int_t nRGBs = 5;")
    gROOT.ProcessLine("Double_t m_stops[5] = { 0.00, 0.25, 0.50, 0.75, 1.00};")
    gROOT.ProcessLine("Double_t m_red[5]   = { 0.00, 0.00, 1.00, 1.00, 1.00};")
    gROOT.ProcessLine("Double_t m_green[5] = { 0.00, 0.75, 1.00, 0.25, 0.00};")
    gROOT.ProcessLine("Double_t m_blue[5]  = { 1.00, 1.00, 1.00, 0.00, 0.00};")
    gROOT.ProcessLine("TColor::CreateGradientColorTable(nRGBs, m_stops, m_red, m_green, m_blue, 255);")
    gROOT.ProcessLine("gStyle->SetNumberContours(255);")
    #gStyle.SetPalette(104)

    # play with canvas of NP
    h = p_nuis.GetListOfPrimitives().At(0)
    axis = h.GetXaxis()
    axis_pulls = h.GetXaxis().Clone("atemp")
    g_2s = p_nuis.GetListOfPrimitives().At(1)
    g_1s = p_nuis.GetListOfPrimitives().At(2)
    nuis = p_nuis.GetListOfPrimitives().At(3)
    pulls = None
    try:
        pulls = p_nuis.GetListOfPrimitives().At(4)
    except:
        pass
    # first try to reproduce the existing plot
    #nuis_plot("origin", nuis.Clone(), g_2s.Clone(), g_2s.Clone(), h.Clone())
    # then sort the NP
    # NOTE: this #include statement is needed for ROOT v6 
    #       (ROOT v5 is fine without it)
    gROOT.ProcessLine("#include \""+os.environ["WORKDIR"]+"/WSMaker/plotUtils.hpp\"")
    # function pointers not supported in PyROOT... have to workaround
    gROOT.ProcessLine("n = (TGraph*)"+str(ROOT.AddressOf(nuis)[0]))
    gROOT.ProcessLine("a = (TAxis*)"+str(ROOT.AddressOf(axis)[0]))
    gROOT.ProcessLine("PU::sortTGraphAxis(n, a, true, PU::comp_sysNames)")
    if pulls:
        gROOT.ProcessLine("p = (TGraph*)"+str(ROOT.AddressOf(pulls)[0]))
        gROOT.ProcessLine("a2 = (TAxis*)"+str(ROOT.AddressOf(axis_pulls)[0]))
        gROOT.ProcessLine("PU::sortTGraphAxis(p, a2, true, PU::comp_sysNames)")
    #nuis_plot("sorted", nuis.Clone(), g_2s.Clone(), g_2s.Clone(), h.Clone())
    # then plot only interesting things
    res = reduce_all(nuis, g_2s, g_1s, axis, excludes=vector_TString(cfg.exclude_str), pulls=pulls)
    nuis_plot(cfg, plotdir, "all", *res)
    nuis = res[0]
    g_2s = res[1]
    g_1s = res[2]
    pulls = res[3]
    axis = nuis.GetXaxis().Clone()
    res = reduce_all(nuis, g_2s, g_1s, axis, excludes=vector_TString("bin"), pulls=pulls)
    nuis_plot(cfg, plotdir, "allExceptGammas", *res)
    #    res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("SysJetE", "SysJetF", "SysJetM",
    #                                                                  "SysBJet", "SysJetBE"))
    #    nuis_plot(plotdir, "Jet1", *res)
    #    res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("SysJetN", "SysJetP", "SysJVF",
    #                                                                   "METReso", "METTrig"))
    #    nuis_plot(plotdir, "Jet2", *res)
    #    res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("TruthTagDR", "BTagB"))
    #    nuis_plot(plotdir, "BTagB", *res)
    #    res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("BTagC"))
    #    nuis_plot(plotdir, "BTagC", *res)
    #    res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("BTagL"))
    #    nuis_plot(plotdir, "BTagL", *res)
    #    res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("Elec", "Muon","Lep"))
    #    nuis_plot(plotdir, "Lepton", *res)
    #    res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("norm"))
    #    nuis_plot(plotdir, "Norm1", *res)
    #    res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("Norm","Ratio"))
    #    nuis_plot(plotdir, "Norm2", *res)
    #    res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("DPhi", "WMbb", "WbbMbb", "ZMbb", "ZPt", "WPt"))
    #    nuis_plot(plotdir, "ModelWZ", *res)

    #    res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("VVJet", "VVMbb", "TopP", "Ttbar", "ttbarHigh", "TChan",
    #                                                                 "WtChan", "SChan"))
    #    nuis_plot(plotdir, "ModelTopVV", *res)
    #res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("norm"))
    #nuis_plot(plotdir, "norm", *res, hmin=0, hmax=2.5)
    #res = reduce_all(nuis, g_2s, g_1s, axis, excludes=vector_TString("SysJetE", "SysJetF", "SysJetM", "SysBJet",
    #                                                              "SysJetBE", "SysJetN",
    #                                                              "SysJetP", "SysJVF", "MET",
    #                                                              "TruthTagDR", "BTag", "norm", "Norm",
    #                                                              "Ratio", "Elec", "Muon", "Lep", "DPhi", "WMbb",
    #                                                              "WbbMbb", "ZMbb", "ZPt", "WPt", "VVJet",
    #                                                              "VVMbb", "TopP", "Ttbar", "ttbarHigh", "TChan", "WtChan",
    #                                                              "SChan"))
    #nuis_plot(plotdir, "Rest", *res)

    # Only plot NPs with pulls/constrains
    if((hasattr(cfg, 'problematic_constr_thres')) and (hasattr(cfg, 'problematic_pull_thres'))):
        npbins = nuis.GetN()
        pullconst = set() 
        for i in range(0, npbins):
            ilabel = nuis.GetXaxis().GetBinLabel((int)(nuis.GetX()[i]+0.5))
            if(('norm' in ilabel) or ('bin' in ilabel)):
                continue
            if (abs(nuis.GetY()[i])>cfg.problematic_pull_thres):
                pullconst.add(ilabel)
            if((abs(nuis.GetErrorYhigh(i))<cfg.problematic_constr_thres) or (abs(nuis.GetErrorYlow(i))<cfg.problematic_constr_thres)):
                pullconst.add(ilabel)
        res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString(*pullconst), pulls = pulls)
        nuis_plot(cfg, plotdir, "problematic", *res)

    # New clasification
    for key in cfg.cov_classification:
        name = key
        zero = cfg.cov_classification[key][0]
        inc_args = cfg.cov_classification[key][1]
        exc_args = cfg.cov_classification[key][2]
        if zero:
            tmp = shift_to_zero(nuis, axis)
        else:
            tmp = nuis

        if len(inc_args) > 0 and len(exc_args) > 0:
            res = reduce_all(tmp, g_2s, g_1s, axis, includes=vector_TString(*inc_args), excludes=vector_TString(*exc_args), pulls = pulls)
        elif len(inc_args) > 0:
            res = reduce_all(tmp, g_2s, g_1s, axis, includes=vector_TString(*inc_args), pulls=pulls)
        elif len(exc_args) > 0:
            res = reduce_all(tmp, g_2s, g_1s, axis, excludes=vector_TString(*exc_args), pulls=pulls)
        else:
            res = reduce_all(tmp, g_2s, g_1s, axis)

        if "Gamma" in name:
            nuis_plot(cfg, plotdir, name, *res, hmin=0.5, hmax=1.5)
        else:
            nuis_plot(cfg, plotdir, name, *res)


    # res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("SysFT_EFF_Eigen", "SysFT_EFF_extrapolation"))
    # nuis_plot(plotdir, "BTag", *res)
    #
    #
    # res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("SysWt", "SysTop", "SysTtbar"))
    # nuis_plot(plotdir, "Top", *res)
    #
    #
    # res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("SysVV", "SysWM","SysZM","SysWD","SysZD","SysWP","SysZP"))
    # nuis_plot(plotdir, "ModelBoson", *res)
    #
    #
    # res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("Norm","Ratio"))
    # nuis_plot(plotdir, "Norm", *res)
    #
    # res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("norm"))
    # nuis_plot(plotdir, "norm", *res)
    #
    # res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("SysMUON","SysEL","SysEG"))
    # nuis_plot(plotdir, "Lepton", *res)
    #
    # res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("SysJET","FATJET"))
    # nuis_plot(plotdir, "Jet", *res)
    #
    # res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("SysMET"))
    # nuis_plot(plotdir, "MET", *res)
    #
    #
    # res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString("LUMI"))
    # nuis_plot(plotdir, "LUMI", *res)
    #
    #
    # tmp = shift_to_zero(nuis, axis)
    # res = reduce_all(tmp, g_2s, g_1s, axis, excludes=vector_TString("blablabla"))
    # nuis_plot(plotdir, "Shifted", *res)


    suspicious_NP = []
    suspicious_NP.extend(flag_suspicious_NP(cfg, nuis, axis, .5, .5))
    res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString(*suspicious_NP), pulls=pulls)
    #res = reduce_all(nuis, g_2s, g_1s, axis, includes=vector_TString(*flag_suspicious_NP(nuis, axis)))
    nuis_plot(cfg, plotdir, "Suspicious", *res)

    # play with correlation matrix
    h2 = p_corr.GetListOfPrimitives().At(0)
    corr_plot(cfg, plotdir, "origin", h2.Clone())
    # function pointers not supported in PyROOT... have to workaround
    gROOT.ProcessLine("c = (TH2*)"+str(ROOT.AddressOf(h2)[0]))
    gROOT.ProcessLine("PU::sortTHAxis(c, true, PU::comp_sysNames)")
    gROOT.ProcessLine("PU::sortTHAxis(c, false, PU::comp_sysNames, true)")
    corr_plot(cfg, plotdir, "sorted", h2.Clone())
    for key in cfg.cov_special:
        name = key
        inc_args = cfg.cov_special[key][0]
        exc_args = cfg.cov_special[key][1]

        if len(inc_args) > 0 and len(exc_args) > 0:
            reduce_and_plot(cfg, plotdir, key, h2, includes=vector_TString(*inc_args), excludes=vector_TString(*exc_args))
        elif len(inc_args) > 0:
            reduce_and_plot(cfg, plotdir, key, h2, includes=vector_TString(*inc_args))
        elif len(exc_args) > 0:
            reduce_and_plot(cfg, plotdir, key, h2, excludes=vector_TString(*exc_args))
        else:
            reduce_and_plot(cfg, plotdir, key, h2)


    # reduce_and_plot(plotdir, "noMCStat", h2, excludes=vector_TString("gamma"))
    # reduce_and_plot(plotdir, "JES", h2, includes=vector_TString("SigX", "norm_", "Jet"))
    # reduce_and_plot(plotdir, "BTag", h2, includes=vector_TString("SigX", "norm_", "BTag"))
    # reduce_and_plot(plotdir, "Mbb", h2, includes=vector_TString("SigX", "norm_", "Mbb"))
    # reduce_and_plot(plotdir, "Modelling", h2, includes=vector_TString("SigX", "norm_", "Norm", "Ratio", "PtBi"))
    # reduce_and_plot(plotdir, "SF", h2, includes=vector_TString("SigX", "norm_"))
    # reduce_and_plot(plotdir, "Norm", h2, includes=vector_TString("3JNorm", "norm_", "Norm", "Ratio"))
    # find all correlations > 25%
    systs = set()
    systsNoGammas = set()
    systs.add("SigX")
    systsNoGammas.add("SigX")

    nbins = h2.GetNbinsX()
    hasOneBin = False
    hasOneBinNoGammas = False

    for i in range(1, nbins+1):
        for j in range(1, nbins+1):
            if i+j == nbins+1: # diagonal
                continue
            if abs(h2.GetBinContent(i,j))>0.25:                
                    hasOneBin = True
                    systs.add(h2.GetXaxis().GetBinLabel(i))
                    systs.add(h2.GetYaxis().GetBinLabel(j))
                    if("bin" not in h2.GetXaxis().GetBinLabel(i)) and  ("bin" not in h2.GetYaxis().GetBinLabel(j)): #removing gammas
                        hasOneBinNoGammas = True
                        systsNoGammas.add(h2.GetXaxis().GetBinLabel(i))
                        systsNoGammas.add(h2.GetYaxis().GetBinLabel(j))
                                        
    if hasOneBin :
        reduce_and_plot(cfg, plotdir, "HighCorr", h2, includes=vector_TString(*systs))
 
    if hasOneBinNoGammas :
        reduce_and_plot(cfg, plotdir, "HighCorrNoMCStat", h2, includes=vector_TString(*systsNoGammas))

    #systs = set()
    #systs.add("SigX")
    #nbins = h2.GetNbinsX()
    #for i in range(1, nbins+1):
    #    if not "LUMI" in h2.GetXaxis().GetBinLabel(i):
    #        continue
    #    for j in range(1, nbins+1):
    #        if i+j == nbins+1: # diagonal
    #            continue
    #        if abs(h2.GetBinContent(i,j))>0.1:
    #            systs.add(h2.GetXaxis().GetBinLabel(i))
    #            systs.add(h2.GetYaxis().GetBinLabel(j))
    #reduce_and_plot(plotdir, "Lumi", h2, includes=vector_TString(*systs))

    systsX = set()
    systsX.add("SigX")
    for s in cfg.syst_to_study:
        systsX.add(s)
    systsY = set()
    systsY.add("SigX")
    for s in cfg.syst_to_study:
        systsY.add(s)
    nbins = h2.GetNbinsX()
    for j in range(1, nbins+1):
        found = False
        sysname = h2.GetYaxis().GetBinLabel(j)
        for s in systsY:
            if s in sysname:
                found = True
                break
        if not found:
            continue
        for i in range(1, nbins+1):
            if i+j == nbins+1: # diagonal
                continue
            if abs(h2.GetBinContent(i,j))>0.15:
                systsX.add(h2.GetXaxis().GetBinLabel(i))
    reduce_and_plot_2D(cfg, plotdir, "HighSysts", h2, includesX=vector_TString(*systsX), includesY=vector_TString(*systsY))




def nuis_plot(cfg, plotdir, name, nuis, yellow, green, pulls, h=None, hmin=-5, hmax=5):

    # put things into the correct order before plotting them (if supported by analysisPlottingConfig)
    if hasattr(cfg, "get_NP_key"):
        from comparePulls import sort_TGraphs
        nuis = sort_TGraphs([nuis], key = cfg.get_NP_key)[0]
        pulls = sort_TGraphs([pulls], key = cfg.get_NP_key)[0]

    c = ROOT.TCanvas("c","c",1000,400)
    if h is not None:
        h.SetMinimum(hmin)
        h.SetMaximum(hmax)
        ya = h.GetYaxis()
        h.Draw()
        nuis.Draw("p")
    else:
        nuis.SetMinimum(hmin)
        nuis.SetMaximum(hmax)
        nuis.Draw("pa")
        ya = nuis.GetYaxis()
    ya.SetTitle("pull")
    ya.SetTitleOffset(.5)
    yellow.SetFillColor(ROOT.kYellow)
    green.SetFillColor(ROOT.kGreen)
    yellow.Draw("f")
    green.Draw("f")
    nuis.Draw("p")
    if pulls is not None:
        pulls.SetMarkerStyle(25)
        pulls.Draw("p")
    ROOT.gPad.SetBottomMargin(ROOT.gPad.GetBottomMargin()*1.8)
    ROOT.gPad.SetLeftMargin(ROOT.gPad.GetLeftMargin()*.5)
    ROOT.gPad.SetRightMargin(ROOT.gPad.GetRightMargin()*.3)
    ROOT.gPad.Update()
    for ext in cfg.formats:
        c.Print(f"{plotdir}/NP_{name}.{ext}")
    

def corr_plot(cfg, plotdir, name, hist):
    c = ROOT.TCanvas("c","c")
    hist.GetXaxis().LabelsOption("v")
    if hist.GetNbinsX() > 0:
        if os.getenv("ANALYSISTYPE") == "VHqqRun2" : hist.GetXaxis().SetLabelSize(min(1.0/hist.GetNbinsX(), 0.03))
        else : hist.GetXaxis().SetLabelSize(min(1.6/hist.GetNbinsX(), 0.03))
    if hist.GetNbinsY() > 0:
        if os.getenv("ANALYSISTYPE") == "VHbbRun2" : hist.GetYaxis().SetLabelSize(min(1.1/hist.GetNbinsY(), 0.03))
        elif os.getenv("ANALYSISTYPE") == "VHqqRun2" : hist.GetYaxis().SetLabelSize(min(1.0/hist.GetNbinsY(), 0.03))
        else : hist.GetYaxis().SetLabelSize(min(1.4/hist.GetNbinsY(), 0.03))
        
    if hasattr(cfg, "get_nice_NP_name"):
        # use analysis specific renaming ...
        from comparePulls import rename_NPs
        rename_NPs(hist.GetXaxis(), cfg.get_nice_NP_name)
        rename_NPs(hist.GetYaxis(), cfg.get_nice_NP_name)
    else:
        # ... and fall back to original naming if not available
        purge_label_names(hist.GetXaxis(), name)
        purge_label_names(hist.GetYaxis(), name)

    gStyle.SetPaintTextFormat("1.2f");
    if os.getenv("ANALYSISTYPE") == "VHbbRun2" : hist.SetMarkerSize(0.6)
    elif os.getenv("ANALYSISTYPE") == "VHqqRun2" : hist.SetMarkerSize(0.5)
    else : hist.SetMarkerSize(0.7)
    hist.Draw("colztext")
    ROOT.gPad.SetBottomMargin(ROOT.gPad.GetBottomMargin()*1.7)
    ROOT.gPad.SetLeftMargin(ROOT.gPad.GetLeftMargin()*1.2)
    ROOT.gPad.Update()
    for ext in cfg.formats:
        c.Print(f"{plotdir}/corr_{name}.{ext}")

def purge_label_names(axis, name):
    for i in range(1, axis.GetNbins()+1):
        label = axis.GetBinLabel(i)
        label = label.replace("alpha_","").replace("ATLAS_","").replace("Sys","")
        if os.getenv("ANALYSISTYPE") == "VHbbRun2" or os.getenv("ANALYSISTYPE") == "boostedVHbbRun2":
            label = label.replace("FT_EFF_Eigen","FT")
            label = label.replace("stat_Region_","Gamma_")
            label = label.replace("MCStat_","ddttbar_")
            label = label.replace("extrapolation","extrap")
            label = label.replace("JET_CR_JET_JER","JER")
            label = label.replace("JET_CR_JET","JET")
            label = label.replace("EtaIntercalibration","EtaIntercal")
            label = label.replace("Flavor_Composition","FlavComp")
            label = label.replace("Y2015_","")
            label = label.replace("_TOTAL_1NPCOR_PLUS_UNCOR","_TOTAL_")

            if "NoMCStat" not in name:
                label = label.replace("Y6051_","")
                label = label.replace("incJet1_","")
        
        if os.getenv("ANALYSISTYPE") == "VHccRun2":
            label = label.replace("FT_EFF_Eigen","FT")
            label = label.replace("stat_Region_","Gamma_")
            label = label.replace("extrapolation","extrap")
            label = label.replace("JET_CR_JET_JER","JER")
            label = label.replace("JET_CR_JET","JET")
            label = label.replace("EtaIntercalibration","EtaIntercal")
            label = label.replace("Flavor_Composition","FlavComp")
            label = label.replace("_TOTAL_1NPCOR_PLUS_UNCOR","_TOTAL_")
            label = label.replace("DT2", "DTnorm")
            label = label.replace("DT3", "DTshape")
            label = label.replace("DT4", "DTcorr")
            label = label.replace("Y6051_","")
            label = label.replace("incJet1_","")
            label = label.replace("BMax150_BMin75","75-150")
            label = label.replace("BMax250_BMin150","150-250")
            label = label.replace("BMin250","250-inf")
            label = label.replace("BMin75", "75-150")
            label = label.replace("BMin150", "150-250")
            label = label.replace("shape_ShMGPy8_mCC", "ShMGPy8")
            label = label.replace("shape_mCC_Pow_aMC", "Pow_aMC")
            label = label.replace("shape_mCC_Her_Pyt", "Her_Pyt")
            label = label.replace("shape_mCC_rHi", "rHi")
            label = label.replace("shape_PwPy8_mCC", "PwPy8")
            label = label.replace("TAUS_TRUEHADTAU_SME_TES_DETECTOR", "TAUS_DETECTOR")
            label = label.replace("TAUS_TRUEHADTAU_SME_TES_INSITU", "TAUS_INSITU")
            label = label.replace("TAUS_TRUEHADTAU_SME_TES_MODEL", "TAUS_MODEL")
            label = label.replace("Wmftau", "Wmf")
                
        if os.getenv("ANALYSISTYPE") == "VHbbRun2":
            if "NoMCStat" not in name:
                label = label.replace("Gamma_","")
                label = label.replace("BMax250_BMin150", "150-250")
            
        if os.getenv("ANALYSISTYPE") == "boostedVHbbRun2":
            label = label.replace("Sys","")
            label = label.replace("JET_21NP_","")
            label = label.replace("JET_23NP_","")
            label = label.replace("JET_JER_SINGLE_NP","JER")
            label = label.replace("JET_GroupedNP","JET")
            label = label.replace("Pileup","PU")
            label = label.replace("SoftTerms","ST")
            label = label.replace("multijet","QCDMJ")
            label = label.replace("Multijet","QCDMJ")
            label = label.replace("dist","d")
            label = label.replace("MedHighPtv","Ptv")
            label = label.replace("RatioHP", "R_HP")
            label = label.replace("RatioPtv", "R_Ptv")
            label = label.replace("RatioSR", "R_SR")
            label = label.replace("Ratiottbar", "R_ttbar")
            label = label.replace("L_BMin400", "L_400")
            label = label.replace("Ptv_BMin400", "Ptv_400")
            label = label.replace("Gamma_", "")
            label = label.replace("FATJET","FJ")
            label = label.replace("MJJMR","FJ_JMR")
            label = label.replace("Medium_JET_Comb","JMSJES")
            label = label.replace("_Kin","")
            label = label.replace("MbbBoosted","mJShape")
            label = label.replace("DSRnoaddbjetsr","SR")
            label = label.replace("DSRtopaddbjetcr","CR")

            if "NoMCStat" not in name:
                label = label.replace("dmBB_","")
                label = label.replace("BMin400_","400_")
                label = label.replace("BMin250_BMax400_","250_")
                label = label.replace("Fat1_","")
                label = label.replace("T2_","")
                label = label.replace("J0_L2_DSR_inc250","L2_SR_250-400_")
                label = label.replace("400_incDSR_L2_J0","L2_SR_400_")
                label = label.replace("BMax400_BMin250_incSR_L1_J0_","L1_HPSR_250-400_")
                label = label.replace("400_incSR_L1_J0_","L1_HPSR_400_")
                label = label.replace("400_incCR_L1_J0_","L1_CR_400_")
                label = label.replace("400_incSR_L1_J1_","L1_LPSR_400_")
                label = label.replace("J0_L1_CR_inc250_","L1_CR_250-400_")
                label = label.replace("J1_L1_SR_inc250_","L1_LPSR_250-400_")
                label = label.replace("J0_L0_CR_inc250_","L0_CR_250-400_")
                label = label.replace("J1_L0_SR_inc250_","L0_LPSR_250-400_")
                label = label.replace("BMax400_BMin250_incSR_L0_J0_","L0_HPSR_250-400_")
                label = label.replace("400_incSR_L0_J0","L0_HPSR_400_")
                label = label.replace("400_incSR_L0_J1","L0_LPSR_400_")
                label = label.replace("400_incCR_L0_J0","L0_CR_400_")
                

        axis.SetBinLabel(i, label)

def reduce_all(nuis, yellow, green, axis, pulls=None, excludes=None, includes=None):

    # rename all NPs to something nicer, if this is supported by the analysisPlottingConfig
    if hasattr(cfg, "get_nice_NP_name"):
        from comparePulls import rename_NPs
        axis = rename_NPs(axis, renamer = cfg.get_nice_NP_name)

    new_pulls = None
    if includes is not None and excludes is not None:
        tmp_nuis = ROOT.PU.reduceTGraphAxisInclude(nuis, axis, True, includes)
        if tmp_nuis.GetN() > 0: #protection
            new_nuis = ROOT.PU.reduceTGraphAxisExclude(tmp_nuis, tmp_nuis.GetXaxis(), True, excludes)
        else:
            new_nuis = tmp_nuis
        if pulls is not None:
            tmp_pulls = ROOT.PU.reduceTGraphAxisInclude(pulls, axis, True, includes)
            if tmp_pulls.GetN() > 0: #protection
                new_pulls = ROOT.PU.reduceTGraphAxisExclude(tmp_pulls, tmp_pulls.GetXaxis(), True, excludes)
            else:
                new_pulls = tmp_pulls

    elif excludes is not None:
        new_nuis = ROOT.PU.reduceTGraphAxisExclude(nuis, axis, True, excludes)
        if pulls is not None:
            new_pulls = ROOT.PU.reduceTGraphAxisExclude(pulls, axis, True, excludes)
    elif includes is not None:
        new_nuis = ROOT.PU.reduceTGraphAxisInclude(nuis, axis, True, includes)
        if pulls is not None:
            new_pulls = ROOT.PU.reduceTGraphAxisInclude(pulls, axis, True, includes)
    max_axis = new_nuis.GetXaxis().GetXmax()
    new_y = yellow.Clone(yellow.GetName()+"_reduced")
    new_g = green.Clone(yellow.GetName()+"_reduced")
    ROOT.PU.removeTGraphPointsAbove(new_y, True, max_axis)
    ROOT.PU.removeTGraphPointsAbove(new_g, True, max_axis)
    return [new_nuis, new_y, new_g, new_pulls]

def shift_to_zero(nuis, axis):
    return ROOT.PU.shiftTGraphToZero(nuis, axis, True)

def reduce_and_plot(cfg, plotdir, name, hist, excludes=None, includes=None):
    if excludes is not None:
        tmp_h = ROOT.PU.reduceTHAxisExclude(hist, True, excludes)
        final_h = ROOT.PU.reduceTHAxisExclude(tmp_h, False, excludes)
    elif includes is not None:
        tmp_h = ROOT.PU.reduceTHAxisInclude(hist, True, includes)
        final_h = ROOT.PU.reduceTHAxisInclude(tmp_h, False, includes)
    corr_plot(cfg, plotdir, name, final_h)

def reduce_and_plot_2D(cfg, plotdir, name, hist, excludesX=None, includesX=None, excludesY=None, includesY=None):
    if excludesX is not None:
        tmp_h = ROOT.PU.reduceTHAxisExclude(hist, True, excludesX)
    elif includesX is not None:
        tmp_h = ROOT.PU.reduceTHAxisInclude(hist, True, includesX)
    if excludesY is not None:
        final_h = ROOT.PU.reduceTHAxisExclude(tmp_h, False, excludesY)
    elif includesY is not None:
        final_h = ROOT.PU.reduceTHAxisInclude(tmp_h, False, includesY)
    corr_plot(cfg, plotdir, name, final_h)

def flag_suspicious_NP(cfg, nuis, axis, thresh_y=.5, thresh_err=.5):
    names = []
    x = ctypes.c_double()
    y = ctypes.c_double()
    for i in range(nuis.GetN()):
        err = nuis.GetErrorY(i)
        nuis.GetPoint(i, x, y)
        label = axis.GetBinLabel(axis.FindBin(x))
        flag = False
        for syst in cfg.suspicious_syst:
            if label.startswith(syst): flag = True
        if flag or abs(y.value)>thresh_y or err<thresh_err:
            names.append(label)
            #print label, y, err
    return names

def flag_suspicious_pulls(cfg, pulls, axis, thresh_sigma=2):
    names = []
    x = ctypes.c_double()
    y = ctypes.c_double()
    for i in range(nuis.GetN()):
        pulls.GetPoint(i, x, y)
        label = axis.GetBinLabel(axis.FindBin(x))
        flag = False
        for syst in cfg.suspicious_syst:
            if label.startswith(syst): flag = True
        if flag or abs(y.value)>thresh_sigma:
            names.append(label)
    return names

def vector_TString(*names):
    res = ROOT.std.vector(ROOT.TString)()
    for n in names:
        res.push_back(n)
    return res

# def init():
#     if len(sys.argv)<=1:
#         print "You must provide a workspace version number !"
#         return
#
#     ROOT.gROOT.LoadMacro("$WORKDIR/macros/AtlasStyle.C")
#     ROOT.SetAtlasStyle(0.03)
#     ROOT.gStyle.SetPadRightMargin(0.12)
#
#     version = sys.argv[1]
#     directory = "fccs/FitCrossChecks_{0}_combined".format(version)
#     print "Running makeReducedDiagPlots for workspace", version
#     if len(sys.argv)>2:
#         algnums = sys.argv[2]
#         for algnum in algnums.split(','):
#             alg = runFitCrossCheck.available_algs[int(algnum)]
#             mu = int(alg[1])
#             is_conditional = False
#             if alg[3] == "true":
#                 is_conditional = True
#             is_asimov = False
#             if "Asimov" in alg[0]:
#                 is_asimov = True
#             print "Running for conditional ?", is_conditional, "for asimov ?", is_asimov, "What mu ?", mu
#             main(version, directory, is_conditional, is_asimov, mu)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Create covariance matrix plots from a given workspace.')
    parser.add_argument('workspace', help = 'workspace/{name}/{something}/{mass}.root -> pass {name}')
    parser.add_argument('-p', '--plot_modes', default = '0',
                        help = """Comma-separated list of FCC options:
    2: unconditional ( start with mu=1 )
    4: conditional mu = 0
    5: conditional mu = 1
    6: run Asimov mu = 1 toys: randomize Poisson term
    7: unconditional fit to asimov where asimov is built with mu=1
    8: unconditional fit to asimov where asimov is built with mu=0
    9: conditional fit to asimov where asimov is built with mu=1
    10: conditional fit to asimov where asimov is built with mu=0""", dest = 'mode')
    parser.add_argument('-f', '--fitres', help = "", default = None, dest = 'fitres')
    args, pass_to_user = parser.parse_known_args()

    cfg = analysisPlottingConfig.Config(pass_to_user)


    ROOT.gROOT.LoadMacro("$WORKDIR/macros/AtlasStyle.C")
    ROOT.SetAtlasStyle(0.03)
    ROOT.gStyle.SetPadRightMargin(0.12)
    ROOT.gSystem.Load("libWSMaker.so")

    version = args.workspace
    modes = [int(s) for s in args.mode.split(',')]

    fitres = args.fitres
    if fitres is None:
        fitres = version

    if os.path.sep in fitres:
        fcc = fitres
    else:
        fcc = "$WORKDIR/../output/"+fitres+"/fccs"

    cfg._fcc_directory = fcc

    # NOTE: need to declare these variables out here since whenever multiple 
    #       sets of of plots are created C++ could complain of multiple 
    #       declarations
    gROOT.ProcessLine("TGraph* n;")
    gROOT.ProcessLine("TAxis* a;")
    gROOT.ProcessLine("TH2* c;")

    print( "Running makeReducedDiagPlots for workspace ", version)
    for algnum in modes:
        alg = runFitCrossCheck.available_algs[int(algnum)]
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
        main(cfg, version)
