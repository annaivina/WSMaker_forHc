#!/usr/bin/env python

import sys
import os
import argparse
import logging

import ROOT
from ROOT import gDirectory, gROOT, gStyle

import runFitCrossCheck
import analysisPlottingConfig

import numpy as np
from matplotlib import pyplot as plt
import matplotlib as mpl
import matplotlib.gridspec as gridspec
from matplotlib import ticker
from cycler import cycler
from matplotlib.font_manager import FontProperties, findfont, get_font
from matplotlib.transforms import Transform
from matplotlib.backends.backend_agg import get_hinting_flag

WORKDIR = os.environ["WORKDIR"]
_y_gap = 1
_header_footer_size = 7

def main():
    # First: parse command-line arguments
    parser = argparse.ArgumentParser(description='Plot nuisance parameters from a fit, or \
compare NP from different workspaces/fits',
            formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('what', choices=['plot', 'compare_fits', 'compare_ws'],
            help = 'what to do: plot, compare_fits, compare_ws')
    parser.add_argument('workspace', nargs='+',
            help = 'workspaces: output/{WSname}/fccs/FitCrossChecks.root -> pass {WSname}')
    parser.add_argument('-a', '--alg_type', nargs='+', type=int,
            help = """Fit number (or list of fits), from the following list of FCC options:
     2: unconditional ( start with mu=1 )
     4: conditional mu = 0
     5: conditional mu = 1
     6: run Asimov mu = 1 toys: randomize Poisson term
     7: unconditional fit to asimov where asimov is built with mu=1
     8: unconditional fit to asimov where asimov is built with mu=0
     9: conditional fit to asimov where asimov is built with mu=1
     10: conditional fit to asimov where asimov is built with mu=0""", 
                        required = True)
    parser.add_argument('-v', '--versions', nargs = '*',
            help = "List of different workspace versions to compare (base workspace name with version wildcarded)", default = [], dest = 'versions')
    parser.add_argument('-s', '--special', nargs = '*',
            help = "List of patterns to create a special plot with only the NPs matching the patterns in the list", default = [], dest = 'special')
    parser.add_argument('-l','--legend', nargs = '*', help = "Legend of the workspace versions")
    parser.add_argument('-p','--plotdir', help = "Output plot directory")
    parser.add_argument('--slides', help = "Optimize the output to show in slides",
            action='store_true')
    parser.add_argument('--paper', help = "Optimize the output to put in INT note",
            action='store_true')
    parser.add_argument('--nostd', help = "Do not print the standard plots",
            action='store_false', dest='stdplots')
    parser.add_argument('pass_to_user', nargs = argparse.REMAINDER, default = [])
    args = parser.parse_args()

    ws_list = _get_workspaces(args.workspace, args.versions)
    if args.legend and len(args.legend) != len(ws_list):
        print("ERROR: The number of legends provided and of workspaces do not match:",
                len(args.legend), "vs", len(ws_list))
        return

    cfg = analysisPlottingConfig.Config(args.pass_to_user)

    if args.what == 'plot':
        if args.plotdir:
            print("WARNING: specifying a plotdir when plotting NPs is possible but not \
the recommended behaviour")
        for i, ws in enumerate(ws_list):
            for a_type in args.alg_type:
                fitres = _get_fitres(ws, a_type)
                mu, is_conditional, is_asimov = _decode_alg(a_type)
                asi = "Asimov" if is_asimov else "Data"
                cond = "" if is_conditional else "un"
                fitname = f"{asi}Fit_{cond}conditional_mu{mu}"
                if args.plotdir:
                    plots_fname_stub = f"{_ws_name(ws)}_{fitname}_NP_"
                    cov_fname_stub = f"{_ws_name(ws)}_{fitname}_Cov_"
                    pdir = args.plotdir
                else:
                    plots_fname_stub = "NP_"
                    cov_fname_stub = "Cov_"
                    pdir = f"{WORKDIR}/../output/{_ws_name(ws)}/plots/fcc/{fitname}"
                os.makedirs(pdir, exist_ok=True)

                # Now plot the NPs
                NPs = _get_NPs(fitres, blind=(cfg.blind and not is_asimov),
                        blind_list=cfg.NP_blind)
                leg = fitname
                if args.legend:
                    leg = f"{args.legend[i]} {leg}"
                make_all_pull_plots(cfg, [NPs], [leg], plotdir=pdir,
                        plots_fname_stub=plots_fname_stub, stdplots=args.stdplots,
                        slides=args.slides, paper=args.paper, special=args.special)
                make_all_cov_plots(cfg, fitres, leg, plotdir=pdir,
                        plots_fname_stub=cov_fname_stub)

    elif args.what == 'compare_fits':
        if len(args.alg_type)<2:
            print("ERROR: cannot compare fits when only one alg has been provided")
            return
        for i, ws in enumerate(ws_list):
            fitres_list = []
            fitres_names = []
            for a_type in args.alg_type:
                fitres = _get_fitres(ws, a_type)
                mu, is_conditional, is_asimov = _decode_alg(a_type)
                asi = "Asimov" if is_asimov else "Data"
                cond = "" if is_conditional else "un"
                fitres_names.append(f"{asi}Fit_{cond}conditional_mu{mu}")
                NPs = _get_NPs(fitres, blind=(cfg.blind and not is_asimov),
                        blind_list=cfg.NP_blind)
                fitres_list.append(NPs)
            plots_fname_stub = "NP_"
            if args.plotdir:
                pdir = args.plotdir
                if len(ws_list)>1:
                    if args.legend:
                        plots_fname_stub = f"{args.legend[i]}_NP_"
                    else:
                        plots_fname_stub = f"{_ws_name(ws)}_NP_"
            else:
                pdir = f"{WORKDIR}/../output/{_ws_name(ws)}/plots/fcc/Compare_"
                pdir += '_'.join(fitres_names)
            os.makedirs(pdir, exist_ok=True)
            suptitle = None
            if args.legend:
                suptitle = args.legend[i]
            make_all_pull_plots(cfg, fitres_list, fitres_names, plotdir=pdir,
                    plots_fname_stub=plots_fname_stub, stdplots=args.stdplots,
                    slides=args.slides, paper=args.paper, suptitle=suptitle,
                    special=args.special)

    elif args.what == 'compare_ws':
        if not args.plotdir:
            print("ERROR: Please provide a --plotdir argument when comparing ws")
            return
        if len(ws_list)<2:
            print("ERROR: cannot compare workspaces when only 1 has been provided")
            return
        for a_type in args.alg_type:
            fitres_list = []
            fitres_names = []
            mu, is_conditional, is_asimov = _decode_alg(a_type)
            asi = "Asimov" if is_asimov else "Data"
            cond = "" if is_conditional else "un"
            suptitle = f"{asi}Fit_{cond}conditional_mu{mu}"
            for i, ws in enumerate(ws_list):
                fitres = _get_fitres(ws, a_type)
                if args.legend:
                    fitres_names.append(args.legend[i])
                else:
                    fitres_names.append(_ws_name(ws))
                NPs = _get_NPs(fitres, blind=(cfg.blind and not is_asimov),
                        blind_list=cfg.NP_blind)
                fitres_list.append(NPs)
            plots_fname_stub = "NP_"
            if len(args.alg_type)>1:
                plots_fname_stub = f"{suptitle}_NP_"
            os.makedirs(args.plotdir, exist_ok=True)
            make_all_pull_plots(cfg, fitres_list, fitres_names, plotdir=args.plotdir,
                    plots_fname_stub=plots_fname_stub, stdplots=args.stdplots,
                    slides=args.slides, paper=args.paper, suptitle=suptitle,
                    special=args.special)

    else:
        print("ERROR: Unknown command", args.what)




def _get_NPs(fitres, blind, blind_list):
    def do_blind(name):
        if not blind: return False
        return any([excl in name for excl in blind_list])
    return [Nuisance(f, i, do_blind(f.GetName())) for f, i in 
            zip(fitres.floatParsFinal(), fitres.floatParsInit())]

def _get_workspaces(ws_list, v_list):
    if len(v_list) == 0:
        basedir_fcc = "{0}/../output/{1}/fccs/FitCrossChecks.root"
        return [ROOT.TFile.Open(basedir_fcc.format(WORKDIR, w)) for w in ws_list]
    res = []
    for w in ws_list:
        basedir_fcc = f"../output/{w}/fccs/FitCrossChecks.root"
        basedir_fcc = os.path.join(WORKDIR, basedir_fcc)
        res.extend([ROOT.TFile.Open(basedir_fcc.format(v)) for v in v_list])
    return res

def _ws_name(ws):
    return ws.GetName().split("/")[-3]

def _decode_alg(alg_type):
    alg = runFitCrossCheck.available_algs[alg_type]
    mu = int(alg[1])
    is_conditional = False
    if alg[3] == "true":
        is_conditional = True
    is_asimov = False
    if "Asimov" in alg[0]:
        is_asimov = True
    return mu, is_conditional, is_asimov

def _get_fitres(ws, alg_type):
    mu, is_conditional, is_asimov = _decode_alg(alg_type)
    print("In workspace", ws.GetName())
    print("Getting fit result: POI", mu, "Asimov", is_asimov, "Conditional", is_conditional)

    dir_1 = "PlotsAfterFitToAsimov" if is_asimov else "PlotsAfterGlobalFit"
    dir_2 = f"conditionnal_MuIsEqualTo_{mu}" if is_conditional else "unconditionnal"
    fitres = ws.Get(f"{dir_1}/{dir_2}/fitResult")
    if fitres is None:
        print("WARNING: RooFitResult not found !!")
    return fitres

def _get_NP_key(cfg, name):
    # give special meaning to certain components of the name ...
    name = cfg.get_NP_name_for_ordering(name)
    special_key = ""
    for key, value in cfg.NP_ordering:
        if key in name:
            special_key = f"{value:03}"  #automatic 0-padding to 3 digits
            break
    # ... but otherwise sort alphabetically
    return special_key + name.lower()


def make_all_pull_plots(cfg, fitres_list = [], fitres_names = [], plotdir='',
        plots_fname_stub='', stdplots=True, slides=False, paper=False, suptitle=None,
        special=None):
    if len(fitres_list) != len(fitres_names):
        print("ERROR: lengths of lists of fitResults and fit names it do not match !")
        print(fitres_list)
        print(fitres_names)
        return

    def _get_NP_key_priv(name):
        return _get_NP_key(cfg, name)

    # get the names of all NPs (which can be different in the various fitRes)
    all_NPs = list(set([nuisp.GetName() for fitres in fitres_list for nuisp in fitres]))
    # and sort them according to user's wishes
    all_NPs.sort(key = _get_NP_key_priv)

    classified_NPlists = []
    all_NPlists = []
    # all Thetas
    all_thetas = sorted(list(set([nuisp.GetName() for fitres in fitres_list for nuisp in fitres if
        nuisp.getType() == 'theta'])), key = _get_NP_key_priv)
    if len(all_thetas):
        all_NPlists.append({'NPlist': all_thetas, 'name': "AllTheta"})

    # all Gammas
    all_gammas = sorted(list(set([nuisp.GetName() for fitres in fitres_list for nuisp in fitres if
        nuisp.getType() == 'gamma'])), key = _get_NP_key_priv)
    if len(all_gammas):
        all_NPlists.append({'NPlist': all_gammas, 'name': "AllGamma"})

    # all NFs
    all_NFs = sorted(list(set([nuisp.GetName() for fitres in fitres_list for nuisp in fitres if
        nuisp.getType() == 'NF'])), key = _get_NP_key_priv)
    if len(all_NFs):
        all_NPlists.append({'NPlist': all_NFs, 'name': "AllNF"})

    # then custom plots
    classified_NPlists = []
    for k, v in cfg.NP_classification.items():
        inc_args = v[0]
        excl_args = v[1]
        def add_np(nuisp):
            # should it be included ?
            incl = (len(inc_args) == 0) or any(ia in nuisp for ia in inc_args)
            # should it be excluded ?
            return incl and not any(ea in nuisp for ea in excl_args)
        NPs = [nuisp for nuisp in all_NPs if add_np(nuisp)]
        if len(NPs)>0:
            classified_NPlists.append({'NPlist': NPs, 'name': k})
            #make_pull_plot(cfg, k, NPs, fitres_list, fitres_names)

    if special:
        NPs = [nuisp for nuisp in all_NPs if any(ia in nuisp for ia in special)]
        if len(NPs)>0:
            classified_NPlists.append({'NPlist': NPs, 'name': 'Special'})

    # TODO do we want to flag suspicious NPs and create a plot only with them ?

    if stdplots:
        for NPlist in all_NPlists + classified_NPlists:
            make_simple_pull_plot(cfg, NPlist['name'], NPlist['NPlist'], fitres_list,
                    fitres_names, f"{plotdir}/{plots_fname_stub}", suptitle)

    if slides or paper:
        NPs_breakdown = []
        NPs_breakdown_names = []
        NPs_to_break = set(all_NPs)
        NFs = set(all_NFs) & NPs_to_break
        NPs_to_break -= NFs
        NPs_breakdown.append(sorted(list(NFs), key = _get_NP_key_priv))
        NPs_breakdown_names.append("NFs")
        for NPs in classified_NPlists:
            NPset = set(NPs['NPlist']) & NPs_to_break
            if len(NPset):
                NPs_to_break -= NPset
                NPs_breakdown.append(sorted(list(NPset), key = _get_NP_key_priv))
                NPs_breakdown_names.append(NPs['name'])
        if len(NPs_to_break):
            NPs_breakdown.append(sorted(list(NPs_to_break), key = _get_NP_key_priv))
            NPs_breakdown_names.append("Other")

    if slides:
        plots_fname_root = f"{plotdir}/Slides_{plots_fname_stub}"
        for NPlist in classified_NPlists:
            make_slides_pull_plot(cfg, [NPlist['name']], [NPlist['NPlist']], fitres_list,
                    fitres_names, f"{plots_fname_root}{NPlist['name']}", suptitle)
        make_slides_pull_plot(cfg, NPs_breakdown_names, NPs_breakdown, fitres_list, fitres_names,
                f"{plots_fname_root}All", suptitle)

    if paper:
        plots_fname_root = f"{plotdir}/Paper_{plots_fname_stub}"
        for NPlist in classified_NPlists:
            make_paper_pull_plot(cfg, [NPlist['name']], [NPlist['NPlist']], fitres_list,
                    fitres_names, f"{plots_fname_root}{NPlist['name']}", suptitle)
        make_paper_pull_plot(cfg, NPs_breakdown_names, NPs_breakdown, fitres_list, fitres_names,
                f"{plots_fname_root}All", suptitle)


def make_simple_pull_plot(cfg, name, NPs_to_plot, fitres_list, fitres_names, plots_fname_root,
        suptitle):
    """NPs_to_plot: list"""
    make_pull_figure_multiblocks(cfg, [[name]], [[NPs_to_plot]], fitres_list, fitres_names,
            f"{plots_fname_root}{name}", suptitle)

def _get_padded_name(name, j, n):
    if n == 1:
        return name
    if n < 10:
        return f"{name}_{j+1}"
    if n < 100:
        return f"{name}_{j+1:02}"
    return f"{name}_{j+1:03}"

def make_slides_pull_plot(cfg, names, NPs_to_plot, fitres_list = [], fitres_names = [], plots_fname_root='', suptitle=None):
    ncols = 2
    max_things_per_col = 71
    nb_cols_per_block = [1 + (len(block)*(len(fitres_list)+_y_gap) + _header_footer_size)//max_things_per_col for block in NPs_to_plot]
    nslides = (sum(nb_cols_per_block)-1)//ncols + 1

    cols = []
    colnames = []
    i_slides = 0

    for i, block in enumerate(NPs_to_plot):
        nb_cols_block = nb_cols_per_block[i]
        n_NP_per_block = 1 + (len(block)-1)//nb_cols_block
        for j in range(nb_cols_block):
            cols.append([block[j*n_NP_per_block:(j+1)*n_NP_per_block]])
            colnames.append([_get_padded_name(names[i], j, nb_cols_block)])
            if len(cols) == ncols:
                fname = _get_padded_name(plots_fname_root, i_slides, nslides)
                make_pull_figure_multiblocks(cfg, colnames, cols, fitres_list, fitres_names,
                        fname, suptitle)
                cols = []
                colnames = []
                i_slides += 1
    if len(cols):
        fname = _get_padded_name(plots_fname_root, i_slides, nslides)
        make_pull_figure_multiblocks(cfg, colnames, cols, fitres_list, fitres_names,
                fname, suptitle)
        i_slides += 1


def make_paper_pull_plot(cfg, names, NPs_to_plot, fitres_list = [], fitres_names = [], plots_fname_root='', suptitle=None):
    """ Bear with me"""
    max_things_per_page = 160
    ncols = 2
    i_page = 0
    blocks = []
    blocknames = []
    blocks_cols = []
    blocknames_cols = []
    remaining_size = max_things_per_page
    remaining_cols = ncols
    for name, NP_block in zip(names, NPs_to_plot):
        j = 0
        remaining_NP = [NP for NP in NP_block]
        while len(remaining_NP):
            needed_size = _header_footer_size + len(remaining_NP)*(len(fitres_names)+_y_gap)
            if remaining_size > needed_size:
                blocks.append(remaining_NP)
                blocknames.append(_get_padded_name(name, j, 99))
                remaining_size -= needed_size
                remaining_NP = []
                j += 1
                continue
            n_available_NPs = (remaining_size - _header_footer_size)//(len(fitres_names)+_y_gap)
            if n_available_NPs < 5: # don't start a block if it's too small: print the page and move on
                blocks_cols.append(blocks)
                blocknames_cols.append(blocknames)
                remaining_cols -= 1
                blocks = []
                blocknames = []
                remaining_size = max_things_per_page
                if remaining_cols == 0:
                  fname = _get_padded_name(plots_fname_root, i_page, 99)
                  make_pull_figure_multiblocks(cfg, blocknames_cols, blocks_cols, fitres_list, fitres_names,
                          fname, suptitle)
                  _print_latex_paper(fname.split('/')[-1], len(blocks_cols))
                  remaining_cols = ncols
                  blocknames_cols = []
                  blocks_cols = []
                  i_page += 1
                continue
            blocks.append(remaining_NP[0:n_available_NPs])
            blocknames.append(_get_padded_name(name, j, 99))
            remaining_NP = remaining_NP[n_available_NPs:]
            remaining_size = 0
            j+=1
    if len(blocks):
        blocks_cols.append(blocks)
        blocknames_cols.append(blocknames)
        fname = _get_padded_name(plots_fname_root, i_page, 99)
        make_pull_figure_multiblocks(cfg, blocknames_cols, blocks_cols, fitres_list, fitres_names,
                fname, suptitle)
        _print_latex_paper(fname.split('/')[-1], len(blocks_cols))

def _print_latex_paper(plotname, ncols):
    print(r"""
  \clearpage
  \begin{{figure}}[htpb]""")
    if ncols == 2:
        print(r"""    \hspace{{-1.8cm}}\includegraphics[width=1.3\linewidth]{{{0}.pdf}}""".format(plotname))
    elif ncols == 2:
        print(r"""    \includegraphics[width=0.7\linewidth]{{{0}.pdf}}""".format(plotname))
    print(r"""    \caption{{{0}}}
    \label{{fig:{0}}}
  \end{{figure}}
""".format(plotname))


def make_pull_figure_multiblocks(cfg, names, NPs_to_plot, fitres_list, fitres_names,
        plot_fname, suptitle):
    """NPs_to_plot: list (columns) of lists (blocks in a column) of lists (Nuisances)"""
    # Use seaborn-muted color palette
    plt.rcParams['axes.prop_cycle'] = cycler('color', ['#4878CF', '#6ACC65', '#D65F5F',
        '#B47CC7', '#C4AD66', '#77BEDB'])
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]

    print("Making plot", plot_fname, "using", names)
    ncols = len(NPs_to_plot)
    nb_fits = len(fitres_list)
    nb_things_to_plot = max([sum([len(NPlist) for NPlist in NPblock])*(nb_fits+_y_gap)+_header_footer_size*len(NPblock) for NPblock in NPs_to_plot])
    #max_NPs = max([len(NPlist) for NPlist in NPs_to_plot])

    # Compute reasonable figure size based on the amount of data to draw
    header = 2
    stuff_size = 0.10
    height = header + stuff_size*nb_things_to_plot
    width = ncols * 8
    fig = plt.figure(figsize=(width, height))
    gspec = gridspec.GridSpec(ncols=ncols, nrows=2, figure=fig, height_ratios = [1,
        stuff_size*nb_things_to_plot])
    gspec.update(left=0.01,right=1-0.01,top=1-0.3/height,bottom=0.5/height,wspace=0.,
            hspace=0.3/height)

    # Fill the columns
    for i in range(ncols):
        NP_blocks = NPs_to_plot[i]
        if len(NP_blocks) == 1:
            _plot_pull_block(cfg, gspec[1,i], names[i][0], NP_blocks[0], fitres_list)
        else:
            hratios = [(nb_fits+_y_gap)*len(NPlist) for NPlist in NP_blocks]
            gsi = gspec[1,i].subgridspec(nrows=len(NP_blocks), ncols=1, height_ratios = hratios,
                    wspace=0.0, hspace=0.8*len(NP_blocks)/height) # hspace is expressed as a fraction of the average axis height !@#
            for j, NPs in enumerate(NP_blocks):
                _plot_pull_block(cfg, gsi[j], names[i][j], NPs, fitres_list)

    # Now draw the header
    ax_header = plt.subplot(
        gspec[0, 0], frameon=False, xlim=[0, 1], xticks=[], ylim=[0, 1], yticks=[]
    )
    ax_header.errorbar([.2], [.75], xerr=[.03], marker='.', markersize=6, color='black',
            ecolor='black', ls='')
    ax_header.plot([.2], [.5], marker='X', markersize=6, color='black', ls='')
    ax_header.text(.26, .75, 'Parameter', ha='left', va='center')
    ax_header.text(.26, .5, 'Blinded NP', ha='left', va='center')
    if suptitle:
        ax_header.text(.45, 1, suptitle, ha='left', va='center')
    for j, fitres in enumerate(fitres_names):
        ax_header.plot([.47], [.8-.2*j], marker='o', color=f'C{j}', ls='')
        ax_header.text(.5, .8-.2*j, fitres, ha='left', va='center')
    ax_header.text(0.17, 1, "ATLAS", fontfamily='DejaVu Sans', fontsize='x-large',
            fontstyle='italic', fontweight='bold', va='baseline', clip_on=False)
    ax_header.text(0.27, 1, "Internal", fontfamily='DejaVu Sans', fontsize='x-large',
            va='baseline', clip_on=False)

    for ext in cfg.formats:
        plt.savefig(f"{plot_fname}.{ext}")
    plt.close()


def _plot_pull_block(cfg, gspec, name, NPs, fitres_list):
    # Nice colors from Open colors
    green = '#2F9E44' # green 8
    orange = '#F08C00' # yellow 8
    red = '#E03131' # red 8
    violet = '#9C36B5' # grape 8
    gray = '#ADB5BD' # gray 5
    lightgray = '#DEE2E6' # gray 3

    nNPs = len(NPs)
    # Each columns is made of 3 parts
    gsi = gspec.subgridspec(nrows=1, ncols=4, width_ratios = [0.9, 1, 0.12, 0.3],
            wspace=0.05, hspace=0)
    ax_labels = plt.subplot(
            gsi[0], frameon=False, xlim=[0,1], xticks=[], ylim = [-.5, nNPs-0.5],
            yticks=[])
    ax_labels.set_title(name, loc= 'right', fontdict={'fontsize':'x-large',
        'fontweight':'bold'})

    # change stuff depending on type of NP plotted
    plot_type = "generic"
    NPtypes = set([n.getType() for f in fitres_list for n in f if n.GetName() in NPs])
    if NPtypes == set(["NF"]):
        plot_type = "NF"
    elif NPtypes == set(["gamma"]):
        plot_type = "gamma"

    ax_qual = plt.subplot(
            gsi[2], frameon=False, xlim=[0,1], xticks=[], sharey=ax_labels, yticks=[],
            title="Signif")

    ax_pulls = plt.subplot(gsi[1], frameon=True, sharey=ax_labels, yticks=[])
    ax_pulls.spines['left'].set_visible(False)
    ax_pulls.spines['right'].set_visible(False)
    ax_pulls.tick_params(axis='x', which='major', top=True, bottom=True,
            labeltop=True, labelbottom=True, direction='in', color=gray,
            grid_color=gray, grid_linewidth=1.5, grid_linestyle='--')
    ax_pulls.grid(axis='x', which='major', visible=True)

    # determine xlims of pull plot
    bounds = np.array([(x.getVal()-x.getError(), x.getVal()+x.getError()) for fitres
        in fitres_list for x in fitres if x.GetName() in NPs])
    xmin_a = np.min(bounds)
    xmax_a = np.max(bounds)

    if plot_type == "generic":
        ax_pulls.set_xlabel('$\\theta$')
        ax_pulls.axvline(0, ls='-', color=gray, lw=2)
        ax_pulls.xaxis.set_major_locator(ticker.MultipleLocator(1))
        lim = np.ceil(max(abs(xmax_a), abs(xmin_a)))*1.1
        if lim<1.e-6: lim=1.1
        ax_pulls.set_xlim(-lim, lim)
        ax_pulls.axvspan(-1, 1, color='#EBFBEE')
    elif plot_type == "gamma":
        ax_pulls.set_xlabel('$\\gamma$')
        ax_pulls.axvline(1, ls='-', color=gray, lw=2)
        ax_pulls.xaxis.set_major_locator(ticker.MultipleLocator(.1))
        ax_pulls.set_xlim(0.78, 1.22)
    elif plot_type == "NF":
        ax_pulls.set_xlabel('NF')
        ax_pulls.axvline(1, ls='-', color=gray, lw=2)
        ax_pulls.xaxis.set_major_locator(ticker.MultipleLocator(.25))
        lim = np.ceil(max(abs(xmax_a-1), abs(xmin_a-1))*4)/4*1.1
        ax_pulls.set_xlim(1-lim, 1+lim)

    ax_vals = plt.subplot(
            gsi[3], frameon=False, xlim=[0,1], xticks=[], sharey=ax_labels, yticks=[],
            title="Values")

    # There is black magic I don't understand with sharey and ticks
    if len(fitres_list) > 1:
        ax_pulls.yaxis.set_major_locator(ticker.FixedLocator(np.arange(.5, nNPs-.5)))
        ax_pulls.tick_params(axis='y', which='major', left=False, right=False,
                labelleft=False, labelright=False)
        ax_pulls.grid(axis='y', which='major', visible=True, ls='-', lw=1.0, color=lightgray)
        ax_labels.tick_params(axis='y', which='major', left=False, right=False,
                labelleft=False, labelright=False)
        ax_qual.tick_params(axis='y', which='major', left=False, right=False,
                labelleft=False, labelright=False)
        ax_vals.tick_params(axis='y', which='major', left=False, right=False,
                labelleft=False, labelright=False)

    # write NP names
    # tricky part is to reduce the font size if needed to fit in the box
    all_names = [cfg.get_nice_NP_name(nuisp) for nuisp in NPs]
    props = FontProperties()
    font = get_font(findfont(props))
    font.set_size(props.get_size_in_points(), ax_labels.get_figure().dpi)
    all_w = []
    for n in all_names:
        font.set_text(n, 0, flags=get_hinting_flag())
        w, _ = font.get_width_height()
        all_w.append(w)
    max_w = max(all_w)
    fontsize = props.get_size_in_points()
    ax_w = ax_labels.bbox.x1 - ax_labels.bbox.x0
    if max_w/64 > ax_w:
        fontsize = int(fontsize * ax_w / (max_w/64))

    for j, nuisp in enumerate(NPs):
        ax_labels.text(1, nNPs-1-j, cfg.get_nice_NP_name(nuisp), ha="right", va="center",
                fontsize=fontsize)

    # draw and write values
    y_spacing = 1/(_y_gap+len(fitres_list))
    n_fitres = len(fitres_list)
    for j, fitres in enumerate(fitres_list):
        x = []
        y = []
        xerr = []
        sig = []
        NPtypes = []
        blind = []
        for nuisp in fitres:
            if nuisp.GetName() in NPs:
                x.append(nuisp.getVal())
                xerr.append(nuisp.getError())
                y.append(1.0*(nNPs - 1 - NPs.index(nuisp.GetName())))
                sig.append(nuisp.getSigma())
                NPtypes.append(nuisp.getType())
                blind.append(nuisp.blind)
        if len(x):
            x = np.array(x)
            xerr = np.array(xerr)
            blind = np.array(blind)
            y = np.array(y)
            y += ((n_fitres-1)/2 - j) * y_spacing
            # regular NP
            ax_pulls.errorbar(x[~blind], y[~blind], xerr=xerr[~blind], marker='.',
                    markersize=10, ecolor=f'C{j}', color=f'C{j}', ls='', lw=2)
            # blinded NP
            ax_pulls.plot(x[blind], y[blind], marker='X', markersize=6, color=f'C{j}', ls='')

        # write significance and value
        for k in range(len(x)):
            col = 'black'
            t = NPtypes[k]
            if t == 'NF' and (x[k]>1.3 or x[k]<0.7):
                col = orange
            elif t == 'theta' and abs(x[k])>0.5:
                col = orange
            elif t == 'theta' and abs(x[k])>2:
                col = red
            ax_vals.text(0.43, y[k], f"{x[k]:.2f}", ha="right",
            va="center", color=col, fontsize='small')
            ax_vals.text(0.5, y[k], "$\\pm$", ha="center",
            va="center", fontsize='small')
            col = 'black'
            if t == 'theta':
                if xerr[k] < 1e-3: # blinding case
                    col = 'black'
                elif xerr[k] < 0.3:
                    col = red
                elif xerr[k] < 0.7 or xerr[k] > 1.0:
                    col = orange
            ax_vals.text(0.57, y[k], f"{xerr[k]:.2f}", ha="left",
            va="center", color=col, fontsize='small')
            s = sig[k]
            if s == "UNK":
                col = violet
            elif s == "UND":
                col = orange
            elif s == "N/A":
                col = gray
            else:
                s = float(s)
                if abs(s)>3:
                    col = red
                elif abs(s)>2:
                    col = orange
                else:
                    col = green
                s = f"{s:.1f}$\\sigma$"
            ax_qual.text(1, y[k], s, color=col, ha='right', va='center', fontsize='small')

def _get_submatrix(mat, idx_list):
    return mat[:,idx_list][idx_list,:]

def make_all_cov_plots(cfg, fitres, legend, plotdir='', plots_fname_stub=''):
    hcov = fitres.correlationHist()
    nNPs = fitres.floatParsFinal().size()
    cov = np.array([[hcov.GetBinContent(j+1, nNPs-i) for j in range(nNPs)] for i in range(nNPs)])

    # Get all NPs and sort them
    all_NP_names = [nuisp.GetName() for nuisp in fitres.floatParsFinal()]
    all_NPs = [(nuisp, i) for i, nuisp in enumerate(all_NP_names)]
    def _get_NP_key_pair(pair):
        return _get_NP_key(cfg, pair[0])
    all_NPs.sort(key = _get_NP_key_pair)
    sorted_cov = _get_submatrix(cov, [p[1] for p in all_NPs])
    sorted_names = np.array([p[0] for p in all_NPs])
    # full correlation plot is useless, i.e always unreadable
    #make_simple_cov_plot(cfg, sorted_cov, sorted_names, legend,
                         #f"{plotdir}/{plots_fname_stub}All")

    # then custom plots
    classified_NPlists = []
    for k, v in (cfg.cov_classification.items()):
        inc_args = v[0]
        excl_args = v[1]
        def add_np(nuisp):
            # should it be included ?
            incl = (len(inc_args) == 0) or any(ia in nuisp for ia in inc_args)
            # should it be excluded ?
            return incl and not any(ea in nuisp for ea in excl_args)
        idx = np.array([add_np(nuisp) for nuisp in sorted_names])
        NPs = sorted_names[idx]
        if len(NPs)>0:
            subcov = _get_submatrix(sorted_cov, idx)
            make_simple_cov_plot(cfg, subcov, NPs, legend,
                                 f"{plotdir}/{plots_fname_stub}{k}")

    idx_sigX = np.array(["SigX" in n for n in sorted_names])

    # then matrix of high correlations
    thresh = 0.25
    idx = np.abs((sorted_cov-np.identity(nNPs))).max(axis=0) > thresh
    idx |= idx_sigX
    NPs = sorted_names[idx]
    if len(NPs)>0:
        subcov = _get_submatrix(sorted_cov, idx)
        make_simple_cov_plot(cfg, subcov, NPs, legend,
                             f"{plotdir}/{plots_fname_stub}HighCorr")
    # and remove MC stat since this was a feature of the previous code
    idx_MCStat = np.array(['bin' in n for n in sorted_names])
    idx_highthresh_noMCStat = idx & ~idx_MCStat
    NPs = sorted_names[idx_highthresh_noMCStat]
    if len(NPs)>0:
        subcov = _get_submatrix(sorted_cov, idx_highthresh_noMCStat)
        make_simple_cov_plot(cfg, subcov, NPs, legend,
                             f"{plotdir}/{plots_fname_stub}HighCorrNoMCStat")

    # now do the 'HighSyst' corr plot, i.e systs that are quite correlated to signal
    high_thresh = 0.15
    systs = ["SigX"] + cfg.NP_for_highSysts_cov
    idx_systs = np.array([any([s in n for s in systs]) for n in sorted_names])
    sig_corrs = np.abs(sorted_cov)[:,idx_systs]
    if sig_corrs.shape[1]>0:
        idx_high = sig_corrs.max(axis=1) > high_thresh
        NPs = sorted_names[idx_high]
        if len(NPs)>0:
            subcov = _get_submatrix(sorted_cov, idx_high)
            make_simple_cov_plot(cfg, subcov, NPs, legend,
                                 f"{plotdir}/{plots_fname_stub}HighSysts")



def make_simple_cov_plot(cfg, cov, names, legend, plot_fname=''):
    print("Making plot", plot_fname)
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]

    nb_things_to_plot = len(names)
    stuff_size = 0.5
    needed_size = stuff_size*nb_things_to_plot
    max_size = 20
    if needed_size > max_size:
        fontsize_red = needed_size / max_size
        needed_size = max_size
    label_margin = 2
    cmap_margin = 1
    w = needed_size + label_margin + cmap_margin
    h = needed_size + label_margin
    fig, ax = plt.subplots(1, figsize=(w, h))
    plt.subplots_adjust(top=1-label_margin/h, left=label_margin/w,
            right=1-cmap_margin/w, bottom=.1/h)

    nice_names = [cfg.get_nice_NP_name(nuisp) for nuisp in names]

    # We can nicely plot a correlation matrix. Since this is bound by -1 and 1,
    # we use those as vmin and vmax. We may also remove leading zeros and hide
    # the diagonal elements (which are all 1) by using a
    # `matplotlib.ticker.FuncFormatter`.

    im, _ = _heatmap(cov, nice_names, nice_names, ax=ax,
            cmap="RdBu_r", vmin=-1, vmax=1,
            cbarlabel="correlation coeff.",
            cbar_kw={'fraction':.3/w, 'pad':.2/w})

    def func(x, pos):
        return "{:.2f}".format(x).replace("0.", "").replace("1.00", "")

    _annotate_heatmap(im, valfmt=ticker.FuncFormatter(func), size=10,
            threshold=0.45, annotate_outliers=[-.15, .15])

    # fix fontsizes of y axis tick labels so they fit in the figure
    props = FontProperties()
    font = get_font(findfont(props))
    font.set_size(props.get_size_in_points(), fig.dpi)
    fontsize = props.get_size_in_points()
    label_space = label_margin*fig.dpi*0.95
    for t in ax.yaxis.get_ticklabels():
        font.set_text(t.get_text(), 0, flags=get_hinting_flag())
        w, _ = font.get_width_height()
        if w/64 > label_space:
            t.set_size(int(fontsize * label_space / (w/64)))

    #plt.tight_layout()
    for ext in cfg.formats:
        plt.savefig(f"{plot_fname}.{ext}")
    plt.close()



# The following two functions are copy-pasted from matplotlib examples library
# as they match exactly our needs

def _heatmap(data, row_labels, col_labels, ax=None,
            cbar_kw=None, cbarlabel="", **kwargs):
    """
    Create a heatmap from a numpy array and two lists of labels.

    Parameters
    ----------
    data
        A 2D numpy array of shape (M, N).
    row_labels
        A list or array of length M with the labels for the rows.
    col_labels
        A list or array of length N with the labels for the columns.
    ax
        A `matplotlib.axes.Axes` instance to which the heatmap is plotted.  If
        not provided, use current axes or create a new one.  Optional.
    cbar_kw
        A dictionary with arguments to `matplotlib.Figure.colorbar`.  Optional.
    cbarlabel
        The label for the colorbar.  Optional.
    **kwargs
        All other arguments are forwarded to `imshow`.
    """

    if ax is None:
        ax = plt.gca()

    if cbar_kw is None:
        cbar_kw = {}

    # Plot the heatmap
    im = ax.imshow(data, **kwargs)

    # Create colorbar
    cbar = ax.figure.colorbar(im, ax=ax, **cbar_kw)
    cbar.ax.set_ylabel(cbarlabel, rotation=-90, va="bottom")

    # Show all ticks and label them with the respective list entries.
    ax.set_xticks(np.arange(data.shape[1]))
    ax.set_xticklabels(col_labels)
    ax.set_yticks(np.arange(data.shape[0]))
    ax.set_yticklabels(row_labels)

    # Let the horizontal axes labeling appear on top.
    ax.tick_params(top=True, bottom=False,
                   labeltop=True, labelbottom=False)

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=-30, ha="right",
             rotation_mode="anchor")

    # Turn spines off and create white grid.
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_xticks(np.arange(data.shape[1]+1)-.5, minor=True)
    ax.set_yticks(np.arange(data.shape[0]+1)-.5, minor=True)
    ax.grid(which="minor", color="w", linestyle='-', linewidth=2)
    ax.tick_params(which="minor", bottom=False, left=False)

    return im, cbar


def _annotate_heatmap(im, data=None, valfmt="{x:.2f}",
                     textcolors=("black", "white"),
                     threshold=None, annotate_outliers=[], **textkw):
    """
    A function to annotate a heatmap.

    Parameters
    ----------
    im
        The AxesImage to be labeled.
    data
        Data used to annotate.  If None, the image's data is used.  Optional.
    valfmt
        The format of the annotations inside the heatmap.  This should either
        use the string format method, e.g. "$ {x:.2f}", or be a
        `matplotlib.ticker.Formatter`.  Optional.
    textcolors
        A pair of colors.  The first is used for values below a threshold,
        the second for those above.  Optional.
    threshold
        Value in data units according to which the colors from textcolors are
        applied.  If None (the default) uses the middle of the colormap as
        separation.  Optional.
    annotate_outliers
        Annotate only the cells with a value outside of the provided range
    **kwargs
        All other arguments are forwarded to each call to `text` used to create
        the text labels.
    """

    if not isinstance(data, (list, np.ndarray)):
        data = im.get_array()

    # Normalize the threshold to the images color range.
    if threshold is not None:
        threshold = im.norm(threshold)
    else:
        threshold = im.norm(data.max())/2.

    # Set default alignment to center, but allow it to be
    # overwritten by textkw.
    kw = dict(horizontalalignment="center",
              verticalalignment="center")
    kw.update(textkw)

    # Get the formatter in case a string is supplied
    if isinstance(valfmt, str):
        valfmt = matplotlib.ticker.StrMethodFormatter(valfmt)

    # Loop over the data and create a `Text` for each "pixel".
    # Change the text's color depending on the data.
    texts = []
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            if len(annotate_outliers):
                if data[i,j]>annotate_outliers[0] and data[i,j]<annotate_outliers[1]:
                    continue
            kw.update(color=textcolors[int(im.norm(data[i, j]) > threshold)])
            text = im.axes.text(j, i, valfmt(data[i, j], None), **kw)
            texts.append(text)

    return texts


class Nuisance:
    def __init__(self, rrv_f, rrv_i, blind=False):
        self.name = rrv_f.GetName()
        self.val = rrv_f.getVal()
        self.err = rrv_f.getError()
        self.val_i = rrv_i.getVal()
        self.err_i = rrv_i.getError()
        if 'alpha' in self.name and self.val_i == 0:
            self.NPtype = "theta"
        elif 'gamma' in self.name and self.val_i == 1:
            self.NPtype = "gamma"
            # hack to make DD TTbar stat NP work: initial sigma not stored in rrv, but upper limit is 5 sigma
            if self.err_i < 1e-6:
                self.err_i = (rrv_i.getRange()[1] - self.val_i) / 5
        elif 'SigXsecOverSM' in self.name:
            self.NPtype = "NF"
        elif self.err_i == 0.0:
            self.NPtype = "NF"
        else:
            rrv_f.Print()
            rrv_i.Print()
            print("WARNING: unable to assign a type to np", self.name)
        self.blind = blind
        if blind:
            self.val = self.val_i
            self.err = 0

    def __str__(self):
        l1 = f"{self.name} ({self.NPtype})"
        l2 = f"{self.val:.2f} ± {self.err:.2f} ({self.val_i:.2f} ± {self.err_i:.2f})"
        l3 = f"{self.getSigma()}"
        return f"{l1} :: {l2} => {l3}"

    def GetName(self):
        return self.name

    def getVal(self):
        return self.val

    def getError(self):
        return self.err

    def getType(self):
        return self.NPtype

    def getSigma(self):
        if self.NPtype == "NF" or self.blind:
            return "N/A"
        elif self.NPtype == "gamma":
            if self.err > self.err_i:
                return "UND"
            return (self.val-self.val_i) / np.sqrt(self.err_i*self.err_i - self.err*self.err)
        elif self.NPtype == "theta":
            if self.err > 1:
                return "UND"
            return self.val / np.sqrt(1 - self.err*self.err)
        else:
            return "UNK"

if __name__ == "__main__":
# Why do I get so much debug ?
    plt.set_loglevel("info")
    pil_logger = logging.getLogger('PIL')
    pil_logger.setLevel(logging.INFO)
    main()

