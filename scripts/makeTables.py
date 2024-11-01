#!/usr/bin/env/python


import sys
import os
import os.path
import argparse
import doPlotFromWS as plots
from ROOT import *
from ROOT import RooFit as RF
import analysisPlottingConfig
from AtlasRounding import atlasRound


def main(cfg, version, mass):
    RooMsgService.instance().setGlobalKillBelow(RF.ERROR)
    gROOT.SetBatch(True)
    gSystem.Load("libWSMaker.so")

    cfg.tables = True

    ws,g = plots.getWorkspace(version, mass)
    if not cfg._main_is_prefit: # if directory is present, then assumes we want postfit
        rfr, suffix = plots.getFitResult(cfg)
        plots.transferResults(cfg, ws, rfr)
        plotdir = f"output/{version}/plots/postfit"
        tsuffix = "Postfit"
    else : # else, compute prefit yields
        plotdir = f"output/{version}/plots/prefit"
        rfr = plots.getInitialFitRes(cfg, ws)
        ws.loadSnapshot("vars_initial")
        suffix = "Prefit"
        tsuffix = "Prefit"

    # cfg.make_slides = False

    os.system("mkdir -vp "+plotdir)

    if cfg.window:
        cfg._yieldsfile = os.path.join(plotdir, "Yields_{}_{}_{}.yik".format(suffix, cfg.window[0],
                                                                                    cfg.window[1]))
    else:
        cfg._yieldsfile = os.path.join(plotdir, f"Yields_{suffix}.yik")
    plots.getYields(cfg, ws, rfr, window=cfg.window)
    raw_yields = cfg._yields

    pretty_yields = make_pretty_yields_map(cfg, raw_yields)
    if cfg.verbose:
        print(pretty_yields)
    tables = make_tables(cfg, pretty_yields)
    #final_text = r"\newcolumntype{d}{D{+}{\hspace{-3pt}\;\pm\;}{-1}}"+'\n'
    final_text = r"% \newcolumntype{d}{D{+}{\hspace{-3pt}\;\pm\;}{-1}}"+'\n'
    if(hasattr(cfg, 'do_tables_standalone') and cfg.do_tables_standalone==False):
        final_text +=r"% You need to include this file from a bigger tex-document"+'\n'
    else:
        final_text += r"\documentclass{article}"+'\n'
        final_text += r"\usepackage{graphicx}"+'\n'
        final_text += r"\newcommand{\GeV}{\mathrm{GeV}}"+'\n'
        final_text += r"\newcommand{\ptv}{p_T^V}"+'\n'
        final_text += r"\begin{document}"+'\n'

    if cfg.make_slides: # suitable for beamer
        for t in sorted(tables.keys()):
            #[year, chan, reg] = t.split('_')
            #final_text += r"\begin{frame}{"+chan+', '+reg+', '+year+"}\n"
            final_text += r"\begin{frame}{"+t+"}\n"
            final_text += "\\tiny\n"
            final_text += tables[t]
            final_text += r"\end{frame}"+"\n\n\n"
    else:   # suitable for CONF note or whatever
        for ind, t in enumerate(sorted(tables.keys())):
            #[year, chan, reg] = t.split('_')
            final_text += r"\begin{table}"+"\n"
            final_text += r"\centering"+"\n"
            final_text += "\\small"+"\n"
            final_text += tables[t]
            #final_text += r"\caption{The "+tsuffix+" yield on the "+chan+", "+reg+" category from "+year+"\label{"+tsuffix+chan+reg+year+"}}"+"\n"
            final_text += r"\end{table}"+"\n\n\n"

            if ind % 5 == 4:
                final_text += r"\clearpage"+"\n\n\n"
        pass
    if(hasattr(cfg, 'do_tables_standalone') and cfg.do_tables_standalone==False):
        final_text += '\n'
    else:
        final_text += r"\end{document}"+'\n'
    if cfg.verbose:
        print(final_text)

    tablesdir = plotdir.replace("plots", "tables")
    os.system("mkdir -p "+tablesdir)
    if cfg.window:
        latexfile = os.path.join(tablesdir, f"Yields_{suffix}_{cfg.window[0]}_{cfg.window[1]}.tex")
    else:
        latexfile = os.path.join(tablesdir, f"Yields_{suffix}.tex")
    os.system("rm -f "+latexfile)
    f = open(latexfile, 'w')
    f.write(final_text)
    f.close()
    g.Close()
    cfg._reset()


def make_pretty_yields_map(cfg, yields):
    """ Ugly logic to get things right """

    regions = sorted(yields.keys())
    samples = []
    for r in regions:
        samples.extend([plots.getCompName(y) for y in yields[r].keys()])
    samples = list(set(samples))
    print(samples)
    samples.sort(key = lambda x: cfg.priorities[x])
    pretty_yields = [[s] for s in samples]
    for r in regions:
        compname_dict = {}
        for s in yields[r].keys():
            compname_dict[plots.getCompName(s)] = s
        for i,s in enumerate(samples):
            if s in compname_dict:
                pretty_yields[i].append( yields[r][compname_dict[s]] )
            else:
                pretty_yields[i].append( [0.0, 0.0] )
    regions.insert(0, "")
    pretty_yields.insert(0, regions)
    return pretty_yields


def make_tables(cfg, pretty_yields, print_errors=True):
    regions = {}
    for i,reg in enumerate(pretty_yields[0]):
        if reg == '':
            continue
        #blocks = reg.split('_')
        #region = blocks[-2] + '_' + blocks[0] + '_' + blocks[1]
        region=reg
        # In case a more fancy splitting of the tables is wanted,
        # implement a splitTable() function in the analysiscfg
        if(hasattr(cfg, 'splitTable')):
            region=cfg.splitTable(reg)
        if not region in regions:
            regions[region] = [i]
        else:
            regions[region].append(i)

    tables = {}
    for reg in sorted(regions.keys()):
        print("Making table for region", reg, "with columns", regions[reg])
        tables[reg] = make_subtable(cfg, pretty_yields, regions[reg], print_errors)
    return tables

def make_subtable(cfg, yields, cols, print_errors=True):
    # vptbin_dict = {0: r"p_{T}^{V}<90\,\mathrm{GeV}", 1: r"90<p_{T}^{V}<120\,\mathrm{GeV}",
    #                2: r"120<p_{T}^{V}<160\,\mathrm{GeV}", 3: r"160<p_{T}^{V}<200\,\mathrm{GeV}",
    #                4: r"p_{T}^{V}>200\,\mathrm{GeV}", 9: r"p_{T}^{V}>0"}

    #table = r"\begin{tabular}{l"+"|d"*len(cols)+"|}\n"
    table = r"\begin{tabular}{l"+"|c"*len(cols)+"|}\n"
    table += r"\cline{2-"+str(int(len(cols)+1))+"}\n"
    #decomp = yields[0][cols[0]].split('_')
    #region = decomp[0]+", "+decomp[1]
    region = yields[0][cols[0]]
    if(hasattr(cfg, 'getTableTitle')):
        table += r" & \multicolumn{"+str(len(cols))+"}{c|}{"+cfg.getTableTitle(region,1)+r"}\\"+'\n'
    else:
        table += r" & \multicolumn{"+str(len(cols))+"}{c|}{"+region.replace('_', r'\_')+r"}\\"+'\n'
    table += r"\cline{2-"+str(int(len(cols)+1))+"}\n"
    table += yields[0][0]
    for i in cols:
        #bin = int(yields[0][i].split('_')[2][1])
        #table += r" & \multicolumn{1}{c|}{$"+vptbin_dict[bin]+"$}"
        bin = yields[0][i]
        if(hasattr(cfg, 'getTableTitle')):
            table += r" & \multicolumn{1}{c|}{"+cfg.getTableTitle(bin,2)+"}"
        else:
            table += r" & \multicolumn{1}{c|}{"+bin.replace('_', r'\_')+"}"
    table += r"\\ \hline"+"\n"
    for line in yields:

        if cfg.blind and not cfg._main_is_prefit and ("AZh" in line[0] or "VH" in line[0] or "Signal" in line[0] or line[0] == "S/B" or line[0] == "S/sqrt(S+B)"):
            continue
        if line[0] == "MC" or line[0] == '':
            continue
        if cfg.blind and "hhbbtautau" in line[0] or "hhttbb" in line[0]:
            continue

        if cfg.blind and "SRVBS" in region and "data" in line[0] :
            continue

        if line[0] == "data":
            table += r"\hline"+"\n"
            table += line[0]
            for i in cols:
                ##table += r" & \multicolumn{1}{c|}{"+str(int(line[i]))+"}"
                table += r" & "+str(int(line[i]))
            table += r"\\ \hline"+"\n"
            continue
        if line[0] == "S/B":
            table += r"\hline"+"\n"
            table += line[0]
            for i in cols:
                table += fr" & {line[i]:.2e}"
            table += r"\\"+"\n"
            continue

        if line[0] == "S/sqrt(S+B)":
            table += line[0]
            for i in cols:
                table += fr" & {line[i]:.2e}"
            table += r"\\"+"\n"
            continue
        if line[0] == "Bkg" or line[0] == "Signal":
            table += r"\hline"+"\n"
        table = add_line(cfg, line, table, cols, print_errors)
        if line[0] == "Bkg":
            table += r"\hline"+"\n"
    table += r"\end{tabular}"+"\n"
    return table


def add_line(cfg, line, mytable, cols, print_errors=True):

    table = line[0] #cfg.bkg_tuple.get(line[0], [line[0]])[0]
    #avoid printing empty lines
    allzero = True
    for i in cols:
        if line[i][0] != 0:
            ## table += " & {0:.2f}\\hspace{{3pt}}+{1:.2f}".format(line[i][0], line[i][1])
            allzero = False

            if print_errors:
                if hasattr(cfg, "atlas_rounding") and cfg.atlas_rounding:
                    table += r" & {} $\pm$ {}".format(*atlasRound(float(line[i][0]), float(line[i][1]), nsig = 2))
                else:
                    table += fr" & {line[i][0]:.2f} $\pm$ {line[i][1]:.2f}"
            else:
                if hasattr(cfg, "atlas_rounding") and cfg.atlas_rounding:
                    table += f" & {atlasRound(float(line[i][0]), float(line[i][1]), nsig = 2)[0]}"
                else:
                    table += f" & {line[i][0]:.2f}"
        else:
            ##table += r" & \multicolumn{1}{c|}{--}"
            table += r" & --"

    table += r"\\"+"\n"

    if (not allzero):
        mytable += table
    return mytable


if __name__ == "__main__":

    gSystem.Load("libWSMaker.so")
    wdir = os.environ["WORKDIR"]
    gROOT.ProcessLine("#include \""+wdir+"/WSMaker/roofitUtils.hpp\"")

    class MyParser(argparse.ArgumentParser):
        def error(self, message):
            sys.stderr.write('error: %s\n' % message)
            self.print_help()
            sys.exit(2)

    parser = MyParser(description='Create yield tables from a given workspace.', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('workspace', help = 'workspace/{name}/{something}/{mass}.root -> pass {name}')
    parser.add_argument('-m', '--mass', type = int, default = 125,
                        help = 'workspace/{name}/{something}/{mass}.root -> pass {mass}', dest = 'mass')
    parser.add_argument('-t', '--table_modes', default = '0',
                        help = """Comma-separated list of tables to create:
    0: prefit table
    1: bkg-only postfit table
    2: s+b postfit table
    3: s+b postfit table with mu=1""", dest = 'mode')
    parser.add_argument('-f', '--fitres', help = "", default = None, dest = 'fitres')
    args, pass_to_user = parser.parse_known_args()

    cfg = analysisPlottingConfig.Config(pass_to_user)

    wsname = args.workspace
    modes = [int(s) for s in args.mode.split(',')]

    mass = args.mass

    fitres = args.fitres
    if fitres is None:
        fitres = wsname

    if os.path.sep in fitres:
        fcc = fitres
    else:
        fcc = "output/" + fitres + "/fccs"

    cfg._fcc_directory = fcc

    for mode in modes:
        if mode == 0:
            print("Doing prefit tables")
            cfg._main_is_prefit = True
            main(cfg, wsname, mass)
        elif mode == 1:
            print("Doing bkg-only postfit tables")
            cfg._is_conditional = True
            cfg._is_asimov = False
            cfg._mu = 0
            cfg._main_is_prefit = False
            main(cfg, wsname, mass)
        elif mode == 2:
            print("Doing s+b postfit tables")
            cfg._is_asimov = False
            cfg._mu = 1
            cfg._main_is_prefit = False
            main(cfg, wsname, mass)
        elif mode == 3:
            print("Doing mu=1 postfit tables")
            cfg._main_is_prefit = False
            cfg._is_conditional = True
            cfg._is_asimov = False
            cfg._mu = 1
            main(cfg, wsname, mass)
        else:
            print("Mode", mode, "is not recognized !")
