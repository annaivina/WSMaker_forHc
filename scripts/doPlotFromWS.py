#!/usr/bin/env python


import os
import os.path
import re
import sys
import math
from array import array
import argparse
import copy
import logging
import ctypes

from ROOT import TFile, TH1, TCanvas, gROOT, gSystem, RooMsgService, gDirectory, TObject, TGraphAsymmErrors, TGraph
from ROOT import RooArgSet, RooArgList, RooAddition, RooAbsData, RooAbsReal, RooHist, RooExpandedFitResult
from ROOT import RooFit as RF
import ROOT
import plotMaker as mkplots
import analysisPlottingConfig

# TODO support toying with several workspaces
# TODO check for memleaks etc...
# TODO reorganize this script into sections:
#       dealing with / moving in workspaces
#       dealing with yields and everythgin that is integrated
#       plot retrieving and making
# FIXME script can't run with varios options and single option is required.
#       if options config: 0,1 => option 0 crash at the end producing the plots. option 1 => do not produce plots
#       if options config: 1,0 => option 1 produce the plots. option 0 plots are equal to option 1
#       O_o
#       option 0 crash at the end needs to be fix

# Spyros: Added mass as argument
def main(cfg, version, mass, doSum):
    """ main function

    Parameters:
    * version: version of the workspace which we want to make plots with
    * directory: where to find FitCrossChecks.root that contains the RooFitResult
    * is_conditional, is_asimov, mu: describe the type of fit chosen for the FitResult
    """

    ws, rfr, suffix, plotdir, g, binDir = initialize(cfg, version, mass)
    save_h = False

    cfg._main_suffix = suffix
    cfg._main_plotdir = plotdir
    cfg._main_save_hists = save_h

    logging.info("Now start plotting")
    if doSum: makePlotsSums(cfg, ws, rfr, mass, binDir)
    else: makePlots(cfg, ws, rfr, mass, restrict_to = cfg.restrict_to, excludes = cfg.excludes, bin_dir = binDir)
    for plotFunc in cfg.additionalPlots:
        plotFunc(cfg, ws, rfr, mass)
    logging.info("Plots made. Now exiting")
    cfg._save_plot_objs()
    cfg._reset()
    g.Close()


# Spyros: Added mass as argument
def initialize(cfg, version, mass):
    RooMsgService.instance().setGlobalKillBelow(RF.ERROR)
    gROOT.SetBatch(True)
    gSystem.Load("libWSMaker.so")

    ws,g = getWorkspace(version, mass)

    logging.info("Preparing NP to the requested values")
    # Make postfit plots
    if not cfg._main_is_prefit:
        rfr, suffix = getFitResult(cfg)
        transferResults(cfg, ws, rfr)
        plotdir = f"output/{version}/plots/postfit"

    # Make prefit plots
    else:
        plotdir = f"output/{version}/plots/prefit"
        rfr = getInitialFitRes(cfg, ws)
        ws.loadSnapshot("vars_initial")
        suffix = "Prefit"

    # GetBinning
    binHist = getBinningDir(g)

    os.system("mkdir -vp "+plotdir)
    cfg._yieldsfile = os.path.join(plotdir, f"Yields_{suffix}.yik")
    cfg._plot_objs_file = os.path.join(plotdir, f"plotobjs_{suffix}.yik")

    return ws, rfr, suffix, plotdir, g, binHist


def getWorkspace(version, mass):
    wsf = os.path.join("output", str(version), "workspaces" , "combined", str(mass))
    wsf += ".root"
    g = TFile.Open(wsf)
    if not g.IsOpen():
        raise RuntimeError(f"Couldn't find file {wsf}")
    ws = g.combined
    return ws,g


def getInitialFitRes(cfg, ws):
    """ Create a prefit RooExpandedFitResult for this workspace """
    mc = ws.obj("ModelConfig")
    force_mu, mu_val = cfg.force_mu_value()
    if force_mu:
        it_b = mc.GetParametersOfInterest().createIterator()
        n_b = it_b.Next()
        while(n_b):
            n_b.setVal(mu_val)
            n_b = it_b.Next()
    np = RooArgList(mc.GetNuisanceParameters())
    np.add(mc.GetParametersOfInterest())
    ws.loadSnapshot("snapshot_paramsVals_initial")
    #removeGamma(np)
    it = np.createIterator()
    n = it.Next()
    while n:
        if "alpha" in n.GetName():
            n.setError(1)
        else:
            n.setError(1.e-4)
        #if "alpha_SysJetEResol" in n.GetName():
            #n.setVal(-1)
        n = it.Next()
    ws.saveSnapshot("vars_initial", RooArgSet(np))
    re = ROOT.RooExpandedFitResult(np)
    cfg._muhat = mc.GetParametersOfInterest().first().getVal()
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        logging.debug("Expanded RooFit results")
        re.Print("v")
    return re


def transferResults(cfg, ws, rfr):
    """ Transfer results from the RooFitResult to the workspace, and make relevant snapshots """
    mc = ws.obj("ModelConfig")
    np = RooArgSet(mc.GetNuisanceParameters(), mc.GetParametersOfInterest())
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        logging.debug("Expanded RooFit results")
        np.Print("v")
    # we want to be sure that the snapshot contains all we need, including POI
    ws.loadSnapshot("snapshot_paramsVals_initial")
    ws.saveSnapshot("vars_initial", np)
    fpf = rfr.floatParsFinal().Clone()
    cp = rfr.constPars()
    fpf.add(cp) # add all const parameters of the RooFitResult to the floating ones
    if cfg.remove_gamma:
        removeGamma(fpf)
    else:
        checkBinning(np, fpf)
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        logging.debug("Expanded RooFit results")
        fpf.Print()
    np.assignValueOnly(fpf) # only sets the central value. Should be ok as VisualizeError uses errors from the RooFitResult, according to ROOT doc
    force_mu, mu_val = cfg.force_mu_value()
    if force_mu:
        # is_higgs_fit = True
        # it = np.createIterator()
        # n = it.Next()
        # while n:
        #     if cfg.transferResults_fitName in n.GetName():
        #         n.setVal(0)
        #         is_higgs_fit = False
        #         break
        #     n = it.Next()
        # cfg._muhat = 1
        # if is_higgs_fit:
        #     mc.GetParametersOfInterest().first().setVal(1)

        # cfg._muhat = mu_val
        it_b = mc.GetParametersOfInterest().createIterator()
        n_b = it_b.Next()
        while(n_b):
            n_b.setVal(mu_val)
            n_b = it_b.Next()
    # else:
    #     cfg._muhat = mc.GetParametersOfInterest().first().getVal()
    cfg._muhat = mc.GetParametersOfInterest().first().getVal()
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        logging.debug("Expanded RooFit results")
        np.Print("v")
    ws.saveSnapshot("vars_final", np)
    ws.loadSnapshot("vars_final")


def removeGamma(arglist):
    to_remove = RooArgList()
    it = arglist.createIterator()
    n = it.Next()
    while n:
        if n.GetName().startswith("gamma"):
            to_remove.add(n)
        n = it.Next()
    print( "Will remove")
    to_remove.Print()
    arglist.remove(to_remove)

def checkBinning(np_ws, np_rfr):
    gamma_ws = dict() #{region:{set of gammas}}
    gamma_rfr = dict()
    regions = set()
    regex_suffix = re.compile('_bin_[0-9]+$')

    def collect_gammas(np, gammas, regions):
        it = np.createIterator()
        n = it.Next()
        while n:
            name = n.GetName()
            if name.startswith("gamma"):
                reg = regex_suffix.sub('', name)
                regions.add(reg)
                if reg not in gammas:
                    gammas.update({reg:set()})
                gammas[reg].add(name)
            n = it.Next()

    collect_gammas(np_ws, gamma_ws, regions)
    collect_gammas(np_rfr, gamma_rfr, regions)

    for reg in regions:
        if reg not in gamma_ws:
            # sys.stderr.write('doPlotFromWS.checkBinning: The workspace you are plotting has no region named {}\n'.format(reg))
            # if reg not in gamma_rfr:
            #     sys.stderr.write('doPlotFromWS.checkBinning: The fit result you are applying has no region named {}\n'.format(reg))
            pass
        elif reg not in gamma_rfr:
            #sys.stderr.write('doPlotFromWS.checkBinning: The fit result you are applying has no region named {}\n'.format(reg))
            pass
        elif len(gamma_ws[reg].intersection(gamma_rfr[reg]))!=0 and len(gamma_ws[reg])!=len(gamma_rfr[reg]):
            sys.stderr.write('\033[31;1mdoPlotFromWS    WARNING    doPlotFromWS.checkBinning: You are applying gamma factors to inconsistent bins. Please consider to use the \'--remove-gamma\' option.\n\033[m')
            break


def getFitResult(cfg):
    """ Go and fetch RooFitResult in a FitCrossChecks.root file """

    f = TFile.Open(f"{cfg._fcc_directory}/FitCrossChecks.root")
    if not f.IsOpen():
        raise RuntimeError("Couldn't find file {}".format(f"{cfg._fcc_directory}/FitCrossChecks.root"))
    if cfg._is_asimov:
        f.cd("PlotsAfterFitToAsimov")
    else:
        f.cd("PlotsAfterGlobalFit")
    if cfg._is_conditional:
        gDirectory.cd(f"conditionnal_MuIsEqualTo_{cfg._mu}")
    else:
        gDirectory.cd("unconditionnal")
    rfr = gDirectory.Get("fitResult").Clone()
    # bonus: get a suffix corresponding to the setup
    suffix = getPostfitSuffix(cfg)
    f.Close()
    return rfr, suffix


def getComponents(cfg, w):
    """ Fetch all components (data, MC pdfs...) for a given workspace
    Organize all of this in a map
    """
    iscomb=cfg.dataname=='combData' # SKC
    mc = w.obj("ModelConfig")
    data = w.data(cfg.dataname)
    simPdf = w.pdf('combPdf'if iscomb else "simPdf")
    channelCat = simPdf.indexCat()
    chanName = channelCat.GetName()

    comps = {}

    for tt in channelCat:
        ttname = tt.first
        pdftmp  = simPdf.getPdf( ttname )
        datatmp = data.reduce(f"{chanName}=={chanName}::{ttname}")
        obs  = pdftmp.getObservables( mc.GetObservables() ).first()
        obs_set = RooArgSet(obs)
        # somehow binWidth contains the inverse of bin width... strange
        binWidth = w.obj(f"{ttname}_model_binWidth")
        logging.debug(f"    Inverse of Bin Width : {binWidth.getVal()}")
        comps[ttname] = [obs, binWidth, datatmp, {}, pdftmp]

        binning = obs.getBinning()
        stepsize = binning.averageBinWidth()
        low = binning.lowBound()
        high = binning.highBound()
        m = low
        while m<(high-1e-6):
            obs.setRange("bin"+str(m), m, m+stepsize)
            m += stepsize

        bkgList = RooArgList()
        sigList = RooArgList()
        totList = RooArgList()

        ## Analysis specific merged entries
        mrgLists = []
        for grp in cfg.yTabGrps :
            grpList = RooArgList()
            for smp in cfg.yTabGrps[grp] :
                for c in components(pdftmp, ttname, iscomb) :
                    if not smp in c.GetName() : continue
                    grpList.add(c)
                    break
            mrgLists.append([grp,grpList])

        for mrgs in mrgLists :
            sumSmp = RooAddition(mrgs[0], mrgs[0], mrgs[1])
            comps[ttname][3][mrgs[0]] = sumSmp
        
        ## Standrad mergings
        for c in components(pdftmp, ttname, iscomb):
            compname = c.GetName()
            has_mass, res = cfg.is_signal(compname)
            if has_mass:
                sigList.add(c)
            else:
                bkgList.add(c)
            totList.add(c)

            comps[ttname][3][compname] = c
        sigSum = RooAddition( "Signal", "sig_Sum", sigList)
        comps[ttname][3]["Signal"] = sigSum
        bkgSum = RooAddition( "Bkg", "bkg_Sum", bkgList)
        comps[ttname][3]["Bkg"] = bkgSum
        totSum = RooAddition( "MC", "tot_Sum", totList)
        comps[ttname][3]["MC"] = totSum

        try:
            cfg.combineComps(comps)
        except AttributeError:
            continue



    return comps


def getYields(cfg, w, rfr=None, onlyTot=False, window=None):
    """ Give map of yields (each category and total) for current snapshot of workspace
    If RooFitResult is given, the errors are computed
    If onlyTot = True, error is computed only on the sum of MC
    """
    if cfg._comps is None:
        cfg._comps = getComponents(cfg, w)

    comps = cfg._comps

    if window:
        logging.info(f"Will compute weights in window {window}")

    cfg._read_yields()
    yields = cfg._yields
    if len(cfg._yields)>0 and rfr is None:
        return cfg._yields

    if onlyTot:
        comp_rfr = None
    else:
        comp_rfr = rfr
    for ttname,comptt in comps.items():
        logging.info(f"    Computing yields for category : {ttname}")
        obs_set = RooArgSet(comptt[0])
        yieldsChan = {}
        if window:
            rname = comptt[0].GetName()+"_range"
            comptt[0].setRange(rname, window[0], window[1])
            yieldsChan["data"] = comptt[2].sumEntries("1", rname)
        else:
            yieldsChan["data"] = comptt[2].sumEntries()

        for compname, comp in comptt[3].items():
            if compname != "MC":
                yieldsChan[compname] = getValueAndError(cfg, comptt[0], comp, comptt[1], comp_rfr, ttname, window)
            else:
                yieldsChan[compname] = getValueAndError(cfg, comptt[0], comp, comptt[1], rfr, ttname, window)
            if compname == "Signal" and cfg._muhat:
                yieldsChan["SignalExpected"] = [y/cfg._muhat for y in yieldsChan[compname]]

        yieldsChan["S/B"] = yieldsChan["Signal"][0] / yieldsChan["Bkg"][0]
        yieldsChan["S/sqrt(S+B)"] = yieldsChan["Signal"][0] / (yieldsChan["Bkg"][0]+yieldsChan["Signal"][0])**.5
        yields[ttname] = yieldsChan
    cfg._yields = yields
    cfg._save_yields()

    return yields


def getValueAndError(cfg, obs, comp, binWidth, rfr, ttname, window=None):
    """ Try to be clever and not re-compute something that has already been computed """
    obs_set = RooArgSet(obs)
    compname = comp.GetName()
    bwidth = binWidth.getVal()
    compInt = None
    if ttname in cfg._yields and compname in cfg._yields[ttname]:
        Ntemp = cfg._yields[ttname][compname][0]
    else:
        if window:
            obs.setRange("myrange", window[0], window[1])
            compInt = comp.createIntegral(obs_set, RF.Range("myrange"))
        else:
            compInt = comp.createIntegral(obs_set)
        Ntemp=compInt.getVal()
    error = -1
    if rfr:
        if ttname in cfg._yields and compname in cfg._yields[ttname] \
           and cfg._yields[ttname][compname][1] != -1:
            error = cfg._yields[ttname][compname][1]
        else:
            if not compInt:
                if window:
                    obs.setRange("myrange", window[0], window[1])
                    compInt = comp.createIntegral(obs_set, RF.Range("myrange"))
                else:
                    compInt = comp.createIntegral(obs_set)
            error = ROOT.RU.getPropagatedError(compInt, rfr)
    logging.info(f"Found {Ntemp} +/- {error} for {compname} in region {ttname}")
    return [Ntemp, error]


# TODO: delete or move
def getSumAndError(list_comps, rfr, window=None):
    """ list_comps: list of tuples (obs, bwidth, comp)
    """
    complist = RooArgList()
    widthlist = RooArgList()
    logging.debug(f"{list_comps}")
    for l in list_comps:
        if window:
            l[0].setRange("myrange", window[0], window[1])
            inte = l[2].createIntegral(RooArgSet(l[0]), RF.Range("myrange"))
        else:
            inte = l[2].createIntegral(RooArgSet(l[0]))
        complist.add(inte)
        widthlist.add(RF.RooConst(l[1]))
    roosum = RooAddition("sum", "sum", complist, widthlist)
    val = roosum.getVal()
    if rfr is not None:
        error = ROOT.RU.getPropagatedError(roosum, rfr)
    else:
        error = -1
    return [val, error]


def makePlots(cfg, w, rfr, mass, restrict_to=[], excludes=[], bin_dir=None):
    """ Plot distributions for each subchannel """

    is_prefit = cfg._main_is_prefit
    suffix = cfg._main_suffix
    plotdir = cfg._main_plotdir
    save_hists = cfg._main_save_hists

    os.system("mkdir -vp "+plotdir)
    objs_dict = getAllPlotObjects(cfg, w, rfr, is_prefit, suffix, plotdir, restrict_to, excludes)

    logging.info("Plotting Distributions for each subchannel")

    for ttname, objs in objs_dict.items():
        if ttname.endswith("error"):
            continue

        plot(cfg, objs, ttname, mass, plot_bkgsub = False, bin_dir=bin_dir)
        #if 'mBB' in ttname: # extra mBB hists with bkg subtraction
         #   print ttname
          #  plot(cfg, objs, ttname, mass, plot_bkgsub = True, bin_dir=bin_dir)

    cfg._save_yields()
    # TODO: move this to the cfg.additionalPlots
    #if makeVpT:
    #    makepTbinsPlots(w, rfr, is_prefit, suffix, plotdir, cfg._yields, save_hists)
    logging.info("End plotting distributions!")


# TODO: delete or move
def makepTbinsPlots(w, rfr, is_prefit, suffix, plotdir, yields = None, save_hists = False):
    """ Plot VpT distributions in each tag region """

    logging.info("Plotting VpT Distributions")
    if is_prefit:
        w.loadSnapshot("vars_initial")
    else:
        w.loadSnapshot("vars_final")

    if not yields:
        logging.debug("Yields not provided. Compute them")
        getYields(w, rfr, True)
        yields = Config.yields

    os.system("mkdir -vp "+plotdir)

    ptbins_cut = array('d', [0, 90, 120, 160, 200, 250])
    hmodel_cut = TH1F("hmodel_cut", "hmodel_cut", 5, ptbins_cut)
    errmodel_x_cut = array('d', [0, 90, 90, 120, 120, 160, 160, 200, 200, 250,
                             250, 200, 200, 160, 160, 120, 120, 90, 90, 0])
    errmodel_y_cut = array('d', [0 for i in range(20)])
    errmodel_cut = TGraph(20, errmodel_x_cut, errmodel_y_cut)

    ptbins_mva = array('d', [0, 120, 250])
    hmodel_mva = TH1F("hmodel_mva", "hmodel_mva", 2, ptbins_mva)
    errmodel_x_mva = array('d', [0, 120, 120, 250, 250, 120, 120, 0])
    errmodel_y_mva = array('d', [0 for i in range(8)])
    errmodel_mva = TGraph(8, errmodel_x_mva, errmodel_y_mva)

    ptbins_cut_0lep = array('d', [0, 100, 120, 160, 200, 250])
    hmodel_cut_0lep = TH1F("hmodel_cut_0lep", "hmodel_cut_0lep", 5, ptbins_cut_0lep)
    errmodel_x_cut_0lep = array('d', [0, 100, 100, 120, 120, 160, 160, 200, 200, 250,
                             250, 200, 200, 160, 160, 120, 120, 100, 100, 0])
    errmodel_y_cut_0lep = array('d', [0 for i in range(20)])
    errmodel_cut_0lep = TGraph(20, errmodel_x_cut_0lep, errmodel_y_cut_0lep)

    ptbins_mva_0lep = array('d', [0, 100, 120, 250])
    hmodel_mva_0lep = TH1F("hmodel_mva_0lep", "hmodel_mva_0lep", 3, ptbins_mva_0lep)
    errmodel_x_mva_0lep = array('d', [0, 100, 100, 120, 120, 250, 250, 120, 120, 100, 100, 0])
    errmodel_y_mva_0lep = array('d', [0 for i in range(12)])
    errmodel_mva_0lep = TGraph(12, errmodel_x_mva_0lep, errmodel_y_mva_0lep)

    histos = {}
    mass = None

    for k,y in yields.items():
        parts = k.split('_')
        # k: Region_Y2012_isMVA1_B2_J2_T2_L2_distmva_TType
        # find the bin:
        pos1 = k.find("_B")
        pos2 = k.find("_", pos1+1)
        if pos2 - pos1 != 3:
            logging.error(f"name of the region {k} does not seem to be a standard one")
            logging.error("_B should match the bin name")
            return
        # TODO: horrible. Need to take care of 0 lepton low MET bin properly, especially in MVA case where lowMET is still CUT
        regname = k[:pos1+2]+'9'+k[pos2:]
        bin = int(k[pos1+2])
        pos1 = regname.find("_dist")
        pos2 = regname.find("_", pos1+1)
        regname = regname[:pos1+5]+"VpT"+regname[pos2:]
        pos1 = regname.find("_isMVA")
        isMVA = int(regname[pos1+6])
        pos1 = k.find("_L")
        pos2 = k.find("_", pos1+1)
        nlep = int(k[pos1+2])
        logging.info(f"Accumulating for region {regname}")
        ibin = bin + 1
        if isMVA and nlep != 0 and ibin == 3: # MVA has no B1
            ibin = 2
        if isMVA:
            if nlep == 0:
                hmodel = hmodel_mva_0lep
                errmodel = errmodel_mva_0lep
            else:
                hmodel = hmodel_mva
                errmodel = errmodel_mva
        else:
            if nlep == 0:
                hmodel = hmodel_cut_0lep
                errmodel = errmodel_cut_0lep
            else:
                hmodel = hmodel_cut
                errmodel = errmodel_cut
        if not regname in histos:
            histos[regname] = {}
            for s, v in y.items():
                if s.endswith("_shapes"):
                    sname = getCompName(s)
                    histos[regname][sname] = hmodel.Clone(sname)
                    if mass == None:
                        res = is_signal(sname)
                        if res:
                            mass = res
            histos[regname]["data"] = hmodel.Clone("data")
            histos[regname]["error"] = errmodel.Clone("error")
            histos[regname]["prefit"] = [hmodel.Clone("prefit"), ""]
        # now, fill the histos
        for s, v in y.items():
            if s.endswith("_shapes"):
                sname = getCompName(s)
                try:
                    histos[regname][getCompName(s)].SetBinContent(ibin, v[0])
                except KeyError: # case when a given component is 0 in the first found VpT bin, but !=0 elsewhere
                    sname = getCompName(s)
                    histos[regname][sname] = hmodel.Clone(sname)
                    histos[regname][sname].SetBinContent(ibin, v[0])
        histos[regname]["data"].SetBinContent(ibin, y["data"])
        (mcval, mcerr) = y["MC"]
        if mcerr == -1: # recompute case by case if not already computed somewhere
            mcerr = getMCerror(w, rfr, k)
            y["MC"] = [mcval, mcerr]
        X = ctypes.c_double()
        Y = ctypes.c_double()
        for i in [2*ibin-2, 2*ibin-1]:
            histos[regname]["error"].GetPoint(i, X, Y)
            histos[regname]["error"].SetPoint(i, X, mcval - mcerr)
        npoints = histos[regname]["error"].GetN()
        for i in [npoints+1-2*ibin, npoints-2*ibin]:
            histos[regname]["error"].GetPoint(i, X, Y)
            histos[regname]["error"].SetPoint(i, X, mcval + mcerr)
        # if doing postfit, add the prefit line
        if not is_prefit:
            histo, mulegend = getPrefitCurve(w, regname = k)
            histos[regname]["prefit"][0].SetBinContent(ibin, histo.Integral())
            print( "PREFIT ", mulegend)
            logging.info(f"PREFIT {mulegend}")
            histos[regname]["prefit"][1] = mulegend

    for reg,h in histos.items():
        h["data"] = TGraphAsymmErrors(h["data"]) # TODO use Poisson errors ?
        sm = mkplots.SetupMaker(reg, mass, muhat = Config.muhat)
        for k,v in h.items():
            sm.add(k, v)

        cname = reg +"_"+suffix
        can = sm.setup.make_complete_plot(cname, True, ybounds=(0.85, 1.15))
        plotname = f"{plotdir}/{can.GetName()}"
        can2 = sm.setup.make_complete_plot(cname+"_logy", True, True, ybounds=(0.85, 1.15))
        plotname2 = f"{plotdir}/{can2.GetName()}"
        for f in Config.formats:
            can.Print(plotname+'.'+f)
            can2.Print(plotname2+'.'+f)

        # save histograms if requested
        if save_hists:
            afile = TFile.Open(plotname+".root", "recreate")
            can.Write(can.GetName())
            can2.Write(can2.GetName())
            for k,v in h.items():
                if isinstance(v, TObject):
                    v.Write(v.GetName())
                if k == "prefit":
                    v[0].Write(v[0].GetName())

        can.Close()
        can2.Close()
        # free memory for some objects used in the plotting...
        mkplots.purge()
        # TODO check for things not deleted
    Config.save_yields()


# TODO: Elisabeth's stuff
def plotSumOfCats(cfg, w, rfr, mass, suffix, plotdir, save_hists, list_objs, list_comps, name, weights=None, bin_dir=None, bin_hName=""):
# def plotSumOfCats(rfr, suffix, plotdir, save_hists, list_objs, list_comps, name, weights=None):
    if len(list_objs)>0:
        res = sumPlotObjects(list_objs, weights)
        error_name = name+"_error"
        # print "JWH: error name = {}".format(error_name)
        # print "JWH: objs names = {}".format(cfg._plot_objs.keys())
        if error_name in cfg._plot_objs:
            # print "JWH: found in cfg._plot_objs"
            res["error"] = cfg._plot_objs[error_name]
        else:
            #print "JWH: did not find in cfg._plot_objs"
            mc = w.obj("ModelConfig")
            it_b = mc.GetParametersOfInterest().createIterator()
            n_b = it_b.Next()
            POIs = []
            while n_b:
                POIs.append(n_b.getVal())
                n_b = it_b.Next()
            it_m = mc.GetParametersOfInterest().createIterator()
            if cfg.draw_error_band_on_b_only:
                n_m = it_m.Next()
                while n_m:
                    n_m.setVal(0)
                    n_m = it_m.Next()
            NPs = RooArgList(mc.GetNuisanceParameters())
            if not cfg.draw_error_band_on_b_only:
                NPs.add(mc.GetParametersOfInterest())
            res["error"] = getSumErrorBand(list_comps, rfr, weights, RooArgSet(NPs))
            it_a = mc.GetParametersOfInterest().createIterator()
            n_a = it_a.Next()
            i = 0
            while n_a:
                n_a.setVal(POIs[i])
                i += 1
                n_a = it_a.Next()
            cfg._plot_objs[error_name] = res["error"]
            # print res["error"]
            # for i in range(res["error"].GetN()):
            #     # print "(x,y,err_y) = ({},{},{})".format(res["error"].GetX()[i], res["error"].GetY()[i], res["error"].GetEY()[i])
            #     print "JWH: res[\"error\"](x,y) = ({},{})".format(res["error"].GetX()[i], res["error"].GetY()[i])

        plot(cfg, res, name, mass, False, (0.4, 1.6), bin_dir, bin_hName)
        if 'mBB' in name:
            if not "AZh" in os.getenv("ANALYSISTYPE"):
                plot(cfg, res, name, mass, True)
            else: print( "Skipping 'mBB bkg-subtracted' since running Azh.")
    # if len(list_objs)>0:
    #     res = sumPlotObjects(list_objs, weights)
    #     error_name = name+"_error"
    #     if error_name in Config.plot_objs:
    #         res["error"] = Config.plot_objs[error_name]
    #     else:
    #         res["error"] = getSumErrorBand(list_comps, rfr, weights)
    #         Config.plot_objs[error_name] = res["error"]
    #     plot(res, name, suffix, plotdir, save_hists)


# TODO: Elisabeth's stuff
def makeWeightedSumPlot(cfg, ws, rfr, mass, suffix, plotdir, save_hists, objs_dict, yields, comps, name, restrict_to=[], exclude=[], bin_dir=None, bin_hName=""):
# def makeWeightedSumPlot(rfr, suffix, plotdir, save_hists, objs_dict, yields, comps, name, restrict_to=[], exclude=[]):
    """ restrict_to is to be understand with AND """
    list_tot = []
    comps_tot = []
    weights_tot = []
    weights_dib_tot = []
    sob_rabbit_hole=False
    for k,v in objs_dict.items():
        if "error" in k:
            continue
        if len(restrict_to)>0:
            if False in (r in k for r in restrict_to):
                continue
        if True in (r in k for r in exclude):
            continue
        s_o_b = abs(yields[k]["Signal"][0]) / abs(yields[k]["Bkg"][0])
        diboson = 0
        for r in yields[k]:
            if "WZ" in r or "ZZ" in r or "VZ" in r or "Diboson" in r or "diboson" in r:
                diboson += yields[k][r][0]
        if diboson:
            d_o_b = abs(diboson) / abs(yields[k]["Bkg"][0])
        else:
            d_o_b = 0
        list_tot.append(v)
        comps_tot.append(comps[k])
        weights_tot.append(s_o_b)
        weights_dib_tot.append(d_o_b)
        print( k,' (S/B) weight=',s_o_b)
        ###### Alternative implementation of binning finding
        ### Take histo name from first of the summed histos
        ### Pros: less naming propagation through functions
        ### Cons: less modular (not hand specified) | not sure it does not break mbb fancy plot
        ### if bin_hName=="":
        ###    bin_hName = k # at least I think k can be used for string ...
    for wlist in [ weights_tot, weights_dib_tot]:
        sum_list = math.fsum(wlist)
        if sum_list != 0:
            for w in wlist:
                w /= sum_list


    # print weights_tot
    # print weights_dib_tot

    plotSumOfCats(cfg, ws, rfr, mass, suffix, plotdir, save_hists, list_tot, comps_tot, name, None, bin_dir, bin_hName)
    if not "AZh" in os.getenv("ANALYSISTYPE") and not 'pTV' in name:
        plotSumOfCats(cfg, ws, rfr, mass, suffix, plotdir, save_hists, list_tot, comps_tot, name+"_Higgsweighted", weights_tot)
    else:
        print( "Skipping 'Higgsweighted' since AZh or just PtV plot!")
#    plotSumOfCats(cfg, rfr, mass, plotdir, save_hists, list_tot, comps_tot, name+"_Dibosonweighted", weights_dib_tot) # To-do: figure this out

# TODO: Elisabeth's stuff
def makePlotsSums(cfg, w, rfr, mass, bin_dir=None) : #is_prefit, suffix, plotdir, save_hists = False):
# def makePlotsSums(w, rfr, is_prefit, suffix, plotdir, save_hists = False):

    is_prefit = cfg._main_is_prefit
    suffix = cfg._main_suffix
    plotdir = cfg._main_plotdir
    save_hists = cfg._main_save_hists

    os.system("mkdir -vp "+plotdir)
    objs_dict = getAllPlotObjects(cfg, w, rfr, is_prefit, suffix, plotdir)
    logging.info("got all plot objects for sum plots")
    yields = cfg._yields
    if cfg._comps is None:
        cfg._comps = getComponents(cfg, w)
    comps = cfg._comps

    logging.info("Plotting summed Distributions")

    # resulting name, restrict-to list, exclude-any list
    def plottingFunc(name, rt, ea, bhn="") :
        return makeWeightedSumPlot(cfg, w, rfr, mass,
                                   suffix, plotdir,
                                   save_hists,
                                   objs_dict, yields,
                                   comps, name = name,
                                   restrict_to = rt,
                                   exclude = ea,
                                   bin_dir = bin_dir,
                                   bin_hName = bhn)

    cfg.make_sum_plots(plottingFunc)

    cfg._save_yields()
    logging.info("End plotting summed distributions!")


# TODO: delete or move
def makePlotsSumsCR(w, rfr, is_prefit, suffix, plotdir, save_hists = False):
    """ Plot distributions for each subchannel, summing 7 and 8 TeV """

    os.system("mkdir -vp "+plotdir)
    objs_dict = getAllPlotObjects(w, None, is_prefit, suffix, plotdir, restrict_to=["_T0_", "_T1_", "Spctop"])

    if Config.comps is None:
        getComponents(w)
    comps = Config.comps

    print( "Plotting summed Distributions of backgrounds")

    # FIXME update with new conventions. Low priority since we are not updating 2011
    for flav in ["Zero", "One", "Two"]:
        for reg in ["0T2J", "0T3J", "1T2J", "1T3J", "topcr", "topemucr"]:
            list_cr =[]
            list_comps = []
            for k,v in objs_dict.items():
                if k.endswith("error"):
                    continue
                if reg in k and flav in k:
                    list_cr.append(v)
                    list_comps.append(comps[k])

            if len(list_cr)>0:
                name = f"{flav}Lepton_{reg}_B9_both_mjj"
                res = sumPlotObjects(list_cr)
                error_name = name+"_error"
                if error_name in Config.plot_objs:
                    res["error"] = Config.plot_objs[error_name]
                else:
                    mc = w.obj("ModelConfig")
                    prev_mu = mc.GetParametersOfInterest().first().getVal()
                    if cfg.draw_error_band_on_b_only:
                        mc.GetParametersOfInterest().first().setVal(0)
                    res["error"] = getSumErrorBand(list_comps, rfr)
                    mc.GetParametersOfInterest().first().setVal(prev_mu)
                    Config.plot_objs[error_name] = res["error"]
                plot(res, name, suffix, plotdir, save_hists, plot_bkgsub = False,
                    ybounds = (0.76, 1.24))

    Config.save_yields()
    print( "End plotting distributions !")


def getPlotObjects(cfg, w, obs, pdf, data, components, ttyields, fitres=None, objs={}):
    frm = obs.frame()

    for comp in components:
        compname = comp.GetName()
        if compname in objs:
            continue
        h = comp.createHistogram(compname, obs)
        if h.Integral()!=0:
            h.Scale(1/h.Integral())
            if compname in ttyields:
                h.Scale(ttyields[compname][0])
        objs[compname] = h
        if not "mass" in objs:
            has_mass, res = cfg.is_signal(compname)
            if has_mass:
                objs["mass"] = res

    if not "data" in objs:
        data.plotOn(frm,RF.DataError(RooAbsData.Poisson))
        tgdata = frm.getHist()
        objs["data"] = tgdata
        #pdfSum.plotOn(frm)
        pdf.plotOn(frm, RF.Normalization(1, RooAbsReal.RelativeExpected))
        chi2 = frm.chiSquare()
        objs["chi2"] = chi2

    if fitres is not None and "error" not in objs:
        data.plotOn(frm,RF.DataError(RooAbsData.Poisson))
        mc = w.obj("ModelConfig")
        prev_mu = mc.GetParametersOfInterest().first().getVal()
        if cfg.draw_error_band_on_b_only:
            mc.GetParametersOfInterest().first().setVal(0)
        pdf.plotOn(frm, RF.VisualizeError(fitres,1), RF.Name("FitError_AfterFit"),
                   RF.Normalization(1, RooAbsReal.RelativeExpected))
        mc.GetParametersOfInterest().first().setVal(prev_mu)
        c = frm.getCurve()
        objs["error"] = c

    return objs


# TODO: Elisabeth's stuff
def sumPlotObjects(objs_list, weights=None):
    res = {}
    aux = {}
    if weights is None:
        weights = [1]*len(objs_list)
    if len(weights) != len(objs_list):
        logging.error("Numbers of regions and weights given do not match!")
        return

    for objs,w in zip(objs_list, weights):
        for k,v in objs.items():
            if k == "error" or k == "chi2": # meaningless to sum them
                continue
            short = getCompName(k)
            if not short in aux:
                aux[short] = k
                # pay attention not to modify the objects we are working with. They might be reused elsewhere.
                if isinstance(v, TObject):
                    res[k] = v.Clone()
                    if isinstance(v, TGraphAsymmErrors): # data
                        scaleTGraphAsymmErrors(res[k], w)
                    else:
                        res[k].Scale(w)
                elif k == "prefit":
                    res[k] = [v[0].Clone(), v[1]]
                    res[k][0].Scale(w)
                else:
                    res[k] = v
            else:
                idx = aux[short]
                if short != k: # that's one standard component
                    res[idx].Add(v, w)
                elif k == "prefit":
                    res[idx][0].Add(v[0], w)
                elif k == "data":
                    if w == 1:
                        res[idx] = RooHist(res[idx], v)
                    else:
                        res[idx] = RooHist(res[idx], v, 1, w, RooAbsData.SumW2)
    return res


# TODO: Elisabeth's stuff
def getSumErrorBand(comps_list, rfr, weights=None, rsa=None):
    if rfr is None:
        return None
    if weights is None:
        weights = [1]*len(comps_list)
    if len(weights) != len(comps_list):
        logging.error("Numbers of regions and weights given do not match!")
        return

    #v_pdfs = vector('RooAbsPdf*')()
    #v_obs = vector('RooRealVar*')()
    #v_weights = vector(ctypes.c_double)()
    #v_data = vector('RooAbsData*')()

    #print "Summing:"
    #for c,w in zip(comps_list, weights):
        #print c[4]
        #v_obs.push_back(c[0])
        #v_weights.push_back(w)
        #v_pdfs.push_back(c[4])
        #v_data.push_back(c[2])

    #curve = ROOT.RU.plotOnWithErrorBand(v_pdfs, v_obs, v_weights, rfr, v_data)

    v_pdfs = []
    v_obs = []
    v_bw = []
    #print "Summing:"
    for c in comps_list:
        v_pdfs.append(c[3]["MC"])
        v_obs.append(c[0])
        v_bw.append(c[1])
    curve = getBinByBinErrorBand(v_pdfs, v_obs, v_bw, rfr, weights, rsa)

    return curve


def getBinByBinErrorBand(mc_comps, observables, binWidths, rfr, weights=None, rsa=None):
    if rfr is None:
        return None
    bins = []
    binning = observables[0].getBinning()
    stepsize = binning.averageBinWidth()
    low = binning.lowBound()
    high = binning.highBound()
    real_weights = RooArgList()
    if weights is not None:
        for bw, w in zip(binWidths, weights):
            real_weights.add(RF.RooConst(bw.getVal()*w))
    else:
        for bw in binWidths:
            real_weights.add(RF.RooConst(bw.getVal()))
    m = low
    while m < high - 1e-6:
        rname = "bin"+str(m)
        intes = RooArgList()
        for obs, mc in zip(observables, mc_comps):
            intes.add(mc.createIntegral(RooArgSet(obs), RF.Range(rname)))
        totbin = RooAddition("sumbin", "sumbin", intes, real_weights)
        val = totbin.getVal()
        err = ROOT.RU.getPropagatedError(totbin, rfr, rsa)
        bins.append((val, err))
        logging.debug(f"Found error of {err}")
        m += stepsize
    # NM 19-07-11
    # Need to add lots of useless stuff to mimic what RooFit creates, so it can be rebinned
    # It may look wrong, but please trust me...
    yvals = [0, 0, 0]
    xvals = [low-1, low-1]
    for i,b in enumerate(bins):
        yvals.extend([b[0]+b[1], b[0]+b[1]])
        xvals.extend([binning.binLow(i), binning.binLow(i)])
    xvals.extend([high, high, high, high+1, high+1])
    yvals.extend([0, 0, 0, 0,   0, 0, 0, 0])
    xvals.extend(reversed(xvals))
    for b in reversed(bins):
        yvals.extend([b[0]-b[1], b[0]-b[1]])
    yvals.extend([0, 0, 0])
    # # FIXME JWH
    # for x,y in zip(xvals,yvals):
    #     print("(x,y) = ({0},{1})".format(x,y))
    yvals_a = array('d', yvals)
    xvals_a = array('d', xvals)
    curve = TGraph(len(xvals), xvals_a, yvals_a)
    curve.SetName("Sum_FitError")
    return curve


def getPrefitCurve(cfg, w, obs=None, pdf=None, regname=None):
    w.loadSnapshot("vars_initial")
    mc = w.obj("ModelConfig")
    it_b = mc.GetParametersOfInterest().createIterator()
    n_b = it_b.Next()
    while(n_b):
        n_b.setVal( 0 )
        n_b = it_b.Next()
    mubeforefit = mc.GetParametersOfInterest().first().getVal()
    muValueBeforeFitLegend = "Pre-fit background"
    if regname is not None:
        simPdf = w.pdf("simPdf")
        pdf  = simPdf.getPdf( regname )
        obs  = pdf.getObservables( mc.GetObservables() ).first()
        preFitIntegral = pdf.expectedEvents(RooArgSet(obs))
        h = pdf.createHistogram(pdf.GetName(), obs)
        h.Scale(preFitIntegral/h.Integral())
    else:
        preFitIntegral = pdf.expectedEvents(RooArgSet(obs))
        h = pdf.createHistogram(pdf.GetName(), obs)
        h.Scale(preFitIntegral/h.Integral())
    w.loadSnapshot("vars_final")
    return h, muValueBeforeFitLegend


def getCompName(name):
    if name.endswith("_shapes"):
        return name.split('_')[0]
    return name


def components(pdf, ttname, iscomb):
    modelName1 = ttname + "_model"
    if iscomb:
        modelName1 = '{0}_model_model_{0}_edit'.format(ttname)
    pdfmodel1 = pdf.getComponents().find(modelName1)
    if not pdfmodel1:
        it=pdf.getComponents().createIterator()
        var=it.Next()
        print( f'---------ttname is-------{ttname}',pdfmodel1==0)
        while var:
            nom=var.GetName()
            if '_model' in nom and nom.find(ttname)==0:print( nom)
            var=it.Next()
    for c, f in zip(pdfmodel1.coefList(), pdfmodel1.funcList()):
        rp = ROOT.RooProduct(c.GetName()+"_x_shapes", c.GetTitle()+"_x_shapes", c, f)
        # This is creating some memleaks... let's forget about it for now.
        ROOT.SetOwnership(rp, False)
        yield rp

def getPostfitSuffix(cfg):

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
    #mu = str(mu)
    postfit_suffix = f"{dirname}{condname}{muname}"
    return postfit_suffix


# TODO: delete, move, or refactor
def getMCerror(w, rfr, regname):
    if Config.comps is None:
        getComponents(w)
    comps = Config.comps
    obs  = comps[regname][0]
    binWidth = comps[regname][1]
    MC = comps[regname][3]["MC"]
    val, error = getValueAndError(obs, MC, binWidth, rfr, regname)
    return error


def getAllPlotObjects(cfg, w, rfr, is_prefit, suffix, plotdir, restrict_to=[], excludes=[]):
    """ returns a map of plot objects, indexed by category name """
    if is_prefit:
        logging.info("Loading initial snapshot")
        w.loadSnapshot("vars_initial")
    else:
        logging.info("Loading final snapshot")
        w.loadSnapshot("vars_final")
    getYields(cfg, w)
    yields = cfg._yields
    if cfg._comps is None:
        cfg._comps = getComponents(cfg, w)
    comps = cfg._comps
    if cfg._plot_objs is None:
        cfg._read_plot_objs()
    objs_dict = cfg._plot_objs

    logging.info("Getting Distributions for each subchannel")

    for ttname, comptt in comps.items():
        if len(restrict_to)>0:
            if not True in (r in ttname for r in restrict_to):
                continue
        if len(excludes)>0:
            if True in (r in ttname for r in excludes):
                continue
        objs = objs_dict.get(ttname, {})

        logging.info(f"Gathering plot primitives for region {ttname}")
        pdftmp  = comptt[4]
        datatmp = comptt[2]
        obs  = comptt[0]

        individual_comps = {k:v for k,v in comptt[3].items()
                            if k!="MC" and k!="Signal" and k!="Bkg"
                            and k!="SignalExpected" and k!="S/B"
                            and k!="S/sqrt(S+B)"}
        # objs = getPlotObjects(cfg, obs, pdftmp, datatmp, individual_comps.values(), yields[ttname], rfr, objs)
        # FIXME: JWH test
        objs = getPlotObjects(cfg, w, obs, pdftmp, datatmp, list(individual_comps.values()), yields[ttname], rfr, objs)
        # if doing postfit, add the prefit line
        if not is_prefit and "prefit" not in objs:
            histo, mulegend = getPrefitCurve(cfg, w, obs, pdftmp)
            objs["prefit"] = [histo, mulegend]

        logging.debug(f"plot objects for {ttname} = \n{objs}")
        objs_dict[ttname] = objs

        # # FIXME: JWH test
        # if True:
        #     import json
        #     print json.dumps(objs_dict, sort_keys=True, indent=2)

    cfg._save_plot_objs()

    to_remove = []
    if len(restrict_to)>0:
        for k in objs_dict:
            if not True in (r in k for r in restrict_to):
                to_remove.append(k)
            if True in (r in k for r in excludes):
                to_remove.append(k)
    objs_final = copy.deepcopy(objs_dict)
    for k in to_remove:
        objs_final.pop(k)
    return objs_final


# TODO: Elisabet's stuff
def scaleTGraphAsymmErrors(tg, weight):
    yval = tg.GetY()
    errhi = tg.GetEYhigh()
    errlo = tg.GetEYlow()
    for i in range(tg.GetN()):
        yval[i] *= weight
        errhi[i] *= weight
        errlo[i] *= weight


def plot(cfg, objs, ttname, mass, plot_bkgsub=True, ybounds=(0.4, 1.6), bin_dir=None, bin_hName=""):
    # Now do the plots
    suffix = cfg._main_suffix
    plotdir = cfg._main_plotdir
    save_hists = cfg._main_save_hists
    sm = mkplots.SetupMaker(cfg, ttname, mass, muhat = cfg._muhat, guess_properties = True, bin_dir=bin_dir, bin_hName=bin_hName)
    #for i in range(objs["error"].GetN()):
        #print "JWH: objs[\"error\"](x,y) = ({},{})".format(objs["error"].GetX()[i], objs["error"].GetY()[i])
    if 'mass' in objs:
        sm.add('mass', objs['mass'])
    for k,v in objs.items():
        logging.info(f"... {k}")
        sm.add(getCompName(k), v)

    # first, standard plot
    cname = ttname +"_"+suffix
    if ttname.endswith("weighted"):
        can = sm.setup.make_complete_plot(cname, True, ytitle = "Weighted events",ybounds = ybounds, draw_difference = plot_bkgsub)
        canlog = sm.setup.make_complete_plot(cname+'_logy', True,True, ytitle = "Weighted events",ybounds = ybounds, draw_difference = plot_bkgsub)
    else:
        can = sm.setup.make_complete_plot(cname, True, ybounds = ybounds, draw_difference = plot_bkgsub)
        canlog = sm.setup.make_complete_plot(cname+'_logy', True,True, ybounds = ybounds, draw_difference = plot_bkgsub)
    plotname = f"{plotdir}/{can.GetName()}"

    if plot_bkgsub:
        # then, bkg-subtracted plot
        cname2 = ttname +"_BkgSub_"+suffix
        can2 = sm.setup.make_bkg_substr_plot(cname2)
        plotname2 = f"{plotdir}/{can2.GetName()}"
    for f in cfg.formats:
        print( plotname+'.'+f)
        can.Print(plotname+'.'+f)
        canlog.Print(plotname+'log.'+f)
        if plot_bkgsub:
            can2.Print(plotname2+'.'+f)
    # save histograms if requested
    if save_hists:
        afile = TFile.Open(plotname+".root", "recreate")
        can.Write(can.GetName())
        canlog.Write(canlog.GetName())
        if plot_bkgsub:
            can2.Write(can.GetName())
        for k,v in objs.items():
            if isinstance(v, TObject):
                v.Write(v.GetName())
            if k == "prefit":
                v[0].Write(v[0].GetName())

    if plot_bkgsub:
        can2.Close()
    # free memory for some objects used in the plotting...
    mkplots.purge()
    # TODO check for things not deleted


def getBinningDir(f):
    binHist = f.GetDirectory('binning')
    if not binHist:
        binHist = None
    return binHist


if __name__ == "__main__":

    gROOT.LoadMacro("$WORKDIR/macros/AtlasStyle.C")
    gSystem.Load("libWSMaker.so")
    wdir = os.environ["WORKDIR"]
    gROOT.ProcessLine("#include \""+wdir+"/WSMaker/roofitUtils.hpp\"")
    ROOT.SetAtlasStyle()

    class MyParser(argparse.ArgumentParser):
        def error(self, message=None):
            sys.stderr.write('error: %s\n' % message)
            self.print_help()
            sys.exit(2)

    parser = MyParser(description='Create plots from a given workspace.', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('workspace', help = 'workspace/{name}/{something}/{mass}.root -> pass {name}')
    parser.add_argument('-m', '--mass', type = int, default = 125,
                        help = 'workspace/{name}/{something}/{mass}.root -> pass {mass}', dest = 'mass')
    parser.add_argument('-p', '--plot_modes', default = '0',
                        help = """Comma-separated list of plots to create:
    0: prefit plots
    1: bkg-only postfit plots
    2: s+b postfit plots
    3: s+b conditional postfit plots""", dest = 'mode')
    parser.add_argument('-f', '--fitres', help = "fit results to use (fcc directory)", default = None, dest = 'fitres')
    parser.add_argument('-d', '--dataname', help = "data name in WS (default obsData)", default = 'obsData', dest = 'dataname') # SKC
    parser.add_argument('-s', '--sum', help = "make sum plots",
                        dest = 'sum', action = 'store_true')
    parser.set_defaults(sum = False)
    parser.add_argument('--remove-gamma', help = "prevent gammas from being transfered",
                        default = False, dest = 'remove_gamma', action = 'store_true')
    args, pass_to_user = parser.parse_known_args()

    cfg = analysisPlottingConfig.Config(pass_to_user)

    wsname = args.workspace
    modes = [int(s) for s in args.mode.split(',')]

    mass = args.mass
    doSum = args.sum
    cfg.dataname=args.dataname

    fitres = args.fitres
    if fitres is None:
        fitres = wsname

    if os.path.sep in fitres:
        fcc = fitres
    else:
        fcc = "output/"+fitres+"/fccs"

    cfg._fcc_directory = fcc

    cfg.remove_gamma = args.remove_gamma

    for mode in modes:
        if mode == 0:
            logging.info("Doing prefit plots")
            cfg._main_is_prefit = True
            try:
                main(cfg, wsname, mass, doSum)
            except TypeError as te:
                logging.critical(str(te))
                print( TypeError)
        elif mode == 1:
            logging.info("Doing bkg-only postfit plots")
            cfg._is_conditional = True
            cfg._is_asimov = False
            cfg._mu = 0
            cfg._main_is_prefit = False
            try:
                main(cfg, wsname, mass, doSum)
            except TypeError as te:
                logging.critical(str(te))
                print( TypeError)
        elif mode == 2:
            logging.info("Doing s+b postfit plots")
            cfg._is_asimov = False
            cfg._mu = 1
            cfg._main_is_prefit = False
            try:
                main(cfg, wsname, mass, doSum)
            except TypeError as te:
                logging.critical(str(te))
                print( TypeError)
        elif mode == 3:
            logging.info("Doing postfit plots with mu=1")
            cfg._is_conditional = True
            cfg._is_asimov = False
            cfg._mu = 1
            cfg._main_is_prefit = False
            try:
                main(cfg, wsname, mass, doSum)
            except TypeError as te:
                logging.critical(str(te))
                print( TypeError)
        else:
            print( "Mode", mode, "is not recognized !")
            logging.warning(f"Plotting mode {mode} is not recognized!")
