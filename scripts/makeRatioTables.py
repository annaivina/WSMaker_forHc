#!/usr/bin/env python


import copy
import os
import sys
import re
import argparse
from ROOT import gROOT, gSystem

import doPlotFromWS as plots
import makeTables as tables
import runFitCrossCheck
import analysisPlottingConfig

def sumBinsRepl(yields, expr, repl, sample=False):
#    yields = Config.yields
#    return yields
    yieldsNew = {}
    for regname, reg in yields.items():
        regNameNew = regname
        if not sample:
            regNameNew = re.sub(expr, repl, regname)
        if not regNameNew in yieldsNew:
            yieldsNew[regNameNew] = {}
        for k,v in yields[regname].items():
            if k == "S/B" or k == "S/sqrt(S+B)":
            #if k == "data" or k == "S/B" or k == "S/sqrt(S+B)":
                continue
            kNew = re.sub(expr, repl, k)
            if not kNew in yieldsNew[regNameNew]:
                yieldsNew[regNameNew][kNew] = v
            else:
                yieldsNew[regNameNew][kNew][0] += v[0]
                yieldsNew[regNameNew][kNew][1] += v[1]
            if sample:
                yieldsNew[regNameNew][k] = [0, 0]
                yieldsNew[regNameNew][k][0] += v[0]
                yieldsNew[regNameNew][k][1] += v[1]
#            print k
#            print regname + "    " + regNameNew + "    " + k + "    " + str(v[0])

#    for regname, reg in yieldsNew.iteritems():
#       for k,v in yieldsNew[regname].iteritems():
#            print regname + "    " + k + "    " + str(v[0])

#    Config.yields = yieldsNew
    return yieldsNew

def sumBins(cfg, yields):

    for regname,reg in yields.items():
       for k,v in yields[regname].items():
           #print k
           kNew =  re.sub("_Exp", "_HistSys", k)
           if kNew in iter(yields[regname].items()):
               print("WARNING: duplicate key: " + k + ", " + kNew)

    #WSMaker1
    #yields = sumBinsRepl(yields, "_(mva|mjj)", "_dist")
    #yields = sumBinsRepl(yields, "_B[0-4]_", "_B9_")
    #yields = sumBinsRepl(yields, "_[12][MLT]?T", "_xT")
    #yields = sumBinsRepl(yields, "[23]J_", "xJ_")
    #yields = sumBinsRepl(yields, "_[0-9a-z]*top[a-z]*cr_", "_xTxJ_")
    #yields = sumBinsRepl(yields, "[ZOT][a-z]*Lepton", "AnyLepton")
    #yields = sumBinsRepl(yields, "_W(bb|bl|bc|cc)_", "_Whf_", True)
    #yields = sumBinsRepl(yields, "_Z(bb|bl|bc|cc)_", "_Zhf_", True)

    #WSMaker2
    # Region_Y2012_isMVA0_B2_J2_T1_L0_distmjj_TType

    for key in cfg.category_condenser:
        expr = key
        repl = cfg.category_condenser[key][0]
        is_sample = cfg.category_condenser[key][1]
        yields = sumBinsRepl(yields, expr, repl, is_sample)

    # yields = sumBinsRepl(yields, "_HistSyst", "_Exp")
    # yields = sumBinsRepl(yields, "_dist(mva|mjj)", "_dist")
    # yields = sumBinsRepl(yields, "_distMV1cBTag", "_dist")
    # yields = sumBinsRepl(yields, "_isMVA[01]", "_isMVA")
    # yields = sumBinsRepl(yields, "_B[0-5]_", "_B9_")
    # yields = sumBinsRepl(yields, "_TType(ll|mm|tt|xx)", "_TType")
    # yields = sumBinsRepl(yields, "_T[012]", "_Tx")
    # yields = sumBinsRepl(yields, "_J[23]", "_Jx")
    # yields = sumBinsRepl(yields, "_Spc[0-9a-z]*top[a-z]*cr", "_TType")
    # yields = sumBinsRepl(yields, "(multijet)(.*_L)([0123])(.*)",r'MJ\3lep\2\3\4')
    # yields = sumBinsRepl(yields, "_L[0123]", "_Lx")
    # yields = sumBinsRepl(yields, "_W(bb|bl|bc|cc)_", "_Whf_", True)
    # yields = sumBinsRepl(yields, "_Z(bb|bl|bc|cc)_", "_Zhf_", True)

    return yields


# def main(ws1, ws2, is_Prefit=False, is_conditional=False, is_asimov=False, mu=None, window=[90,150]):
def main(cfg, ws1, ws2):
    printUnc = False
    if ws1 == ws2:
        suffix1 = plots.getPostfitSuffix(cfg)
        suffix2 = "Prefit"
        plotdir1 = f"output/{ws1}/plots/postfit"
        plotdir2 = f"output/{ws1}/plots/prefit"
        printUnc = True
        print("INFO: Create post/pre-fit table.")
    elif not cfg._main_is_prefit:
        suffix1 = plots.getPostfitSuffix(cfg)
        suffix2 = plots.getPostfitSuffix(cfg)
        plotdir1 = f"output/{ws1}/plots/postfit"
        plotdir2 = f"output/{ws2}/plots/postfit"
        print("INFO: Create post-fit table.")
    else:
        plotdir1 = f"output/{ws1}/plots/prefit"
        plotdir2 = f"output/{ws2}/plots/prefit"
        suffix1 = "Prefit"
        suffix2 = "Prefit"
        print("INFO: Create prefit-fit table.")

    if cfg.window:
        cfg._yieldsfile = os.path.join(plotdir1, "Yields_{}_{}_{}.yik".format(suffix1, cfg.window[0],
                                                                                        cfg.window[1]))
    else:
        cfg._yieldsfile = os.path.join(plotdir1, f"Yields_{suffix1}.yik")
    print(cfg._yieldsfile)
    cfg._read_yields()
    #plots.sumPTbins()
    yields1 = copy.deepcopy(cfg._yields)
    yields1 = sumBins(cfg, yields1)
    cfg._reset()
    if cfg.window:
        cfg._yieldsfile = os.path.join(plotdir2, "Yields_{}_{}_{}.yik".format(suffix2, cfg.window[0],
                                                                                        cfg.window[1]))
    else:
        cfg._yieldsfile = os.path.join(plotdir2, f"Yields_{suffix2}.yik")
    print(cfg._yieldsfile)
    cfg._read_yields()
    #plots.sumPTbins()
    yields2 = copy.deepcopy(cfg._yields)
    yields2 = sumBins(cfg, yields2)


    #print yields2

    yields_ratio = {}
    for regname, reg in yields1.items():
        if not regname in yields2:
            continue
        yields_ratio[regname] = copy.deepcopy(reg)
        to_remove = ['data']
        for k,v in yields_ratio[regname].items():
            if not k in yields2[regname]:
                continue
            if isinstance(yields_ratio[regname][k], float):
                if yields2[regname][k] == 0 and yields_ratio[regname][k] == 0:
                    to_remove.append(k)
                    continue
            elif isinstance(yields_ratio[regname][k], list):
                if yields2[regname][k][0] == 0 and yields_ratio[regname][k][0] == 0:
                    to_remove.append(k)
                    continue
            if k != "S/B" and k != "S/sqrt(S+B)" and k!= "data":
                if yields2[regname][k][0] != 0:
                    v[0] /= yields2[regname][k][0]
                    v[1] /= yields2[regname][k][0]
                else:
                    v[0] = 9999
            else:
                if yields2[regname][k] != 0:
                    v /= yields2[regname][k]
                else:
                    v = 9999
        for i in to_remove:
            del yields_ratio[regname][i]
    pretty_yields = tables.make_pretty_yields_map(cfg, yields_ratio)
    if cfg.verbose:
        print(pretty_yields)
    final_tables = tables.make_tables(cfg, pretty_yields, printUnc)
    final_text = r"% \newcolumntype{d}{D{+}{\hspace{-3pt}\;\pm\;}{-1}}"+'\n'
    final_text += r"\documentclass{article}"+'\n'
    final_text += r"\usepackage{graphicx}"+'\n'
    final_text += r"\begin{document}"+'\n'

    if cfg.make_slides:
        for t in sorted(final_tables.keys()):
            #[year, chan, reg] = t.split('_')
            #final_text += r"\begin{frame}{"+chan+', '+reg+', '+year+"}\n"
            final_text += r"\begin{frame}{"+t+"}\n"
            final_text += "\\tiny\n"
            final_text += final_tables[t]
            final_text += r"\end{frame}"+"\n\n\n"
    else: # TODO should make a file that is input-able in a CONF note otherwise
        for t in sorted(final_tables.keys()):
            #[year, chan, reg] = t.split('_')
            final_text += r"\begin{table}"+"\n"
            final_text += r"\centering"+"\n"
            final_text += "\\small"+"\n"
            final_text += final_tables[t]
            #final_text += r"\caption{The "+tsuffix+" yield on the "+chan+", "+reg+" category from "+year+"\label{"+tsuffix+chan+reg+year+"}}"+"\n"
            final_text += r"\end{table}"+"\n\n\n"
    final_text += r"\end{document}"+'\n'
    os.system("mkdir -p tables/ratios")
    latexfile = f"tables/ratios/{ws1}_{suffix1}_over_{ws2}_{suffix2}.tex"
    os.system("rm -f "+latexfile)
    f = open(latexfile, 'w')
    f.write(final_text)
    f.close()
    cfg._reset()



if __name__ == "__main__":

    gSystem.Load("libWSMaker.so")
    wdir = os.environ["WORKDIR"]
    gROOT.ProcessLine("#include \""+wdir+"/WSMaker/roofitUtils.hpp\"")

    class MyParser(argparse.ArgumentParser):
        def error(self, message):
            sys.stderr.write('error: %s\n' % message)
            self.print_help()
            sys.exit(2)

    parser = MyParser(description='Create tables of yield ratios from two given workspaces.', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('workspace1', help = 'output/{name}/workspaces/combined/{mass}.root -> pass {name}')
    parser.add_argument('workspace2', help = 'output/{name}/workspaces/combined/{mass}.root -> pass {name}')
    parser.add_argument('-t', '--table_modes', default = '4',
                        help = """Comma-separated list of FCC options (with additional prefit option):
    p: prefit
    2: unconditional ( start with mu=1 )
    4: conditional mu = 0
    5: conditional mu = 1
    6: run Asimov mu = 1 toys: randomize Poisson term
    7: unconditional fit to asimov where asimov is built with mu=1
    8: unconditional fit to asimov where asimov is built with mu=0
    9: conditional fit to asimov where asimov is built with mu=1
    10: conditional fit to asimov where asimov is built with mu=0""", dest = 'mode')
    args, pass_to_user = parser.parse_known_args()

    cfg = analysisPlottingConfig.Config(pass_to_user)

    wspace1 = args.workspace1
    wspace2 = args.workspace2
    modes = [s for s in args.mode.split(',')]

    for algnum in modes:
        if algnum == 'p':
            cfg._main_is_prefit = True
        else:
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
            cfg._main_is_prefit = False

        # main(ws1, ws2, False, False, False, 1, window=None)
        main(cfg, wspace1, wspace2)
