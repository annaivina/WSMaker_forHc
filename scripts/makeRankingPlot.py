#!/usr/bin/env python

import sys
import os
import argparse
import logging
import shutil

import ROOT

import analysisPlottingConfig
from colors import Open_mpl as Open

import numpy as np
from matplotlib import pyplot as plt
#import matplotlib as mpl
from matplotlib import ticker
from matplotlib.patches import Patch
#from matplotlib.font_manager import FontProperties, findfont, get_font
#from matplotlib.transforms import Transform
#from matplotlib.backends.backend_agg import get_hinting_flag

def main():
    # First: parse command-line arguments
    parser = argparse.ArgumentParser(description='Create a ranking plot',
            formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--prefit', help = "Add the prefit impact",
            action='store_true')
    parser.add_argument('--nNP', help = "Set how many NP to display", type=int)
    parser.add_argument('--relative', help = "Plot DeltaMu/Mu instead of DeltaMu",
            action='store_true')
    parser.add_argument('--mergeJobs', help = "Merging output of ranking jobs",
            action='store_true')
    parser.add_argument('workspace',
            help = 'workspace: output/{WSname} -> pass {WSname}')

    parser.add_argument('pass_to_user', nargs = argparse.REMAINDER, default = [])
    args = parser.parse_args()
    cfg = analysisPlottingConfig.Config(args.pass_to_user)

    if args.mergeJobs:
        _merge_jobs(cfg, args.workspace)

    nNPs = cfg.ranking_max_NP
    if args.nNP: nNPs = args.nNP

    rootdir = f"{os.environ['WORKDIR']}/output/{args.workspace}/root-files/pulls"
    plotdir = f"{os.environ['WORKDIR']}/output/{args.workspace}/plots/ranking"
    os.makedirs(plotdir, exist_ok=True)
    pull_plots_contents = {}
    with os.scandir(rootdir) as it:
        for f in it:
            if f.name.endswith('.root'):
                NPname = f.name.rsplit('.')[0]
                tf = ROOT.TFile.Open(f"{rootdir}/{f.name}")
                h = tf.Get(NPname)
                nPOI = (h.GetNbinsX()-3)//5
                for i in range(nPOI):
                    POI_name = h.GetXaxis().GetBinLabel(4+i*5)
                    if POI_name == NPname:
                        continue
                    if not POI_name in pull_plots_contents:
                        pull_plots_contents[POI_name] = []
                    # impact: [NP_name, NP_val, NP_err_up, NP_err_do, POI_val, POI_up, POI_do,
                    #          POI_prefit_up, POI_prefit_do]
                    impact = [NPname] + [h.GetBinContent(i) for i in
                            list(range(1,4))+list(range(4+i*5, 9+i*5))]
                    pull_plots_contents[POI_name].append(impact)
                tf.Close()

    def _impact_postfit(impact_v):
        return (abs(impact_v[5]-impact_v[4]) + abs(impact_v[6]-impact_v[4]))/2

    def _impact_prefit(impact_v):
        return (abs(impact_v[7]-impact_v[4]) + abs(impact_v[8]-impact_v[4]))/2

    for poi, impacts in pull_plots_contents.items():
        impacts.sort(key = _impact_postfit, reverse = True)
        restr_impacts = impacts[:nNPs]
        plot_ranking(cfg, poi, restr_impacts, f"{plotdir}/Ranking_postfit_{poi}",
                args.prefit, args.relative)
        impacts.sort(key = _impact_prefit, reverse = True)
        restr_impacts = impacts[:nNPs]
        plot_ranking(cfg, poi, restr_impacts, f"{plotdir}/Ranking_prefit_{poi}",
                args.prefit, args.relative)

def _merge_jobs(cfg, ws):
    """WARNING: not tested !"""
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
        outdir = f"{os.environ['WORKDIR']}/../output/{ws}/root-files/"
        os.makedirs(outdir+"breakdown_add", exist_ok=True)
        os.makedirs(outdir+"pulls", exist_ok=True)
        jobStr = "job%iof%i" % (nJobs, nJobs)
        for iJob in range(0, nJobs):
            jobStr2 = "job%iof%i" % (iJob, nJobs)
            ws2 = ws.replace(jobStr, jobStr2)
            outdir2 = f"{os.environ['WORKDIR']}/../output/{ws2}/root-files/"
            print("Copying root-files for job", iJob)
            status = os.system( f"cp {outdir2}breakdown_add/*.root {outdir}breakdown_add/" )
            os.system( f"cp {outdir2}pulls/*.root {outdir}pulls/" )
            if status != 0:
                miss += 1

def plot_ranking(cfg, POI_name, impacts, plot_fname, plot_prefit_impact, relative=False):
    # impact: [NP_name, NP_val, NP_err_up, NP_err_do, POI_val, POI_up, POI_do,
    #          POI_prefit_up, POI_prefit_do]
    plt.rcParams["font.sans-serif"] = ["Tex Gyre Heros"]
    print("Making plot", plot_fname, "using", [i[0] for i in impacts])

    NF_color = Open['pink'][7]
    pull_color = Open['gray'][9]
    block_colors = [Open['cyan'], Open['green'], Open['yellow'], Open['grape'],
            Open['indigo']]
    shade_pos = 5
    shade_neg = 3

    nNPs = len(impacts)
    stuff_size = 0.3
    header_size = 1.3
    bottom_size = .5
    w = 6

    padding_impact_bars = 1.1
    padding_pulls = 1.1


    h = header_size + nNPs*stuff_size + bottom_size
    fig, ax_impact = plt.subplots(1, figsize=(w, h))
    plt.subplots_adjust(top=1-header_size/h, left=0.4, right=0.95, bottom=bottom_size/h)

    impacts.reverse() # highest impact on top

    y = np.arange(nNPs)

    impact_hi = np.array([i[5]-i[4] for i in impacts])
    impact_lo = np.array([i[6]-i[4] for i in impacts])
    impact_hi_prefit = np.array([i[7]-i[4] for i in impacts])
    impact_lo_prefit = np.array([i[8]-i[4] for i in impacts])
    if relative:
        impact_hi /= impacts[0][4]
        impact_lo /= impacts[0][4]
        impact_hi_prefit /= impacts[0][4]
        impact_lo_prefit /= impacts[0][4]

    idx_categorized_NP = np.array([False]*nNPs)

    idx_categories = []
    for cat_name, args in cfg.ranking_classification.items():
        idx = np.array([any([a in i[0] for a in args]) for i in impacts])
        idx_categories.append((cat_name, idx))
        idx_categorized_NP |= idx
    # Create Other category with uncategorized NP
    if not all(idx_categorized_NP):
        idx_categories.append(("Other", ~idx_categorized_NP))

    for i, cat in enumerate(idx_categories):
        idx = cat[1]
        if not any(idx):
            continue
        if plot_prefit_impact:
            ax_impact.barh(y[idx], impact_hi_prefit[idx], align='center',
                    fill=False, edgecolor=block_colors[i][shade_pos], linewidth=1,
                    linestyle='--')
            ax_impact.barh(y[idx], impact_lo_prefit[idx], align='center',
                    fill=False, edgecolor=block_colors[i][shade_neg], linewidth=1,
                    linestyle='--')
        ax_impact.barh(y[idx], impact_hi[idx], align='center',
                color=block_colors[i][shade_pos])
        ax_impact.barh(y[idx], impact_lo[idx], align='center',
                color=block_colors[i][shade_neg], label=cat[0])

    max_impact = max( np.abs(impact_hi).max(), np.abs(impact_lo).max(),
            np.abs(impact_hi_prefit).max(), np.abs(impact_lo_prefit).max() )
    ax_impact.set_xlim(-max_impact*padding_impact_bars, max_impact*padding_impact_bars)

    ax_pulls = ax_impact.twiny()

    x_pull = np.array([i[1] for i in impacts])
    x_pull_err_lo = np.array([i[3] for i in impacts])
    x_pull_err_hi = np.array([i[2] for i in impacts])
    idx_NF = np.array(['ATLAS_norm' in i[0] for i in impacts])
    idx_theta = ~idx_NF

    ax_pulls.errorbar(x_pull[idx_theta], y[idx_theta],
            xerr=(x_pull_err_lo[idx_theta], x_pull_err_hi[idx_theta]), marker='o',
            markersize=6, ecolor=pull_color, color=pull_color, ls='',
            label=r"Constrained param.")
            #label=r"Constrained param. $\hat{\theta}$")
    ax_pulls.errorbar(x_pull[idx_NF], y[idx_NF],
            xerr=(x_pull_err_lo[idx_NF], x_pull_err_hi[idx_NF]), marker='o',
            markersize=6, ecolor=NF_color, color=NF_color, ls='',
            label="Normalization param.")

    ylabels = [cfg.get_ranking_NP_name(i[0]) for i in impacts]
    ax_pulls.set_yticks(ticks=y, labels=ylabels)

    max_pulls = max(np.abs(x_pull+x_pull_err_hi).max(), np.abs(x_pull - x_pull_err_lo).max())
    ax_pulls.set_xlim(-max_pulls*padding_pulls, max_pulls*padding_pulls)

    ymax = y[-1]+.5*.8
    _, ymax_ndc = ax_pulls.transAxes.inverted().transform(ax_pulls.transData.transform((0,ymax)))

    ax_pulls.axvline(0, ymax=ymax_ndc, color=pull_color, ls='--', lw=1)
    ax_pulls.axvline(1, ymax=ymax_ndc, color=NF_color, ls='--', lw=1)
    ax_pulls.axvline(-1, ymax=ymax_ndc, color=pull_color, ls='--', lw=1)

    ax_pulls.xaxis.set_minor_locator(ticker.MultipleLocator(.25))

    ax_pulls.tick_params(which='both', top=False, bottom=True, left=False,
                   labeltop=False, labelbottom=True,
                   direction = 'in')
    ax_impact.tick_params(top=True, bottom=False, left=False,
                   labeltop=True, labelbottom=False,
                   direction='in')
    ax_impact.tick_params(axis='x', color=Open['gray'][shade_pos+1],
                   labelcolor=Open['gray'][shade_pos+1])
    ax_impact.tick_params(axis='y', labelsize='small')

    ax_pulls.tick_params(which='major', length=7)
    ax_pulls.tick_params(which='minor', length=4)

    ax_impact.tick_params(which='major', length=7)
    #ax_impact.tick_params(which='minor', top=True, length=3)

    ax_impact.xaxis.set_label_position('top')
    ax_pulls.xaxis.set_label_position('bottom')
    ax_pulls.set_xlabel('Parameter value', loc='right', size='large')
    xlabel = r'$\Delta\mu/\mu$' if relative else r'$\Delta\mu$'
    ax_impact.set_xlabel(xlabel, loc='right', color=Open['gray'][shade_pos+1],
            size='large')

    #ax_impact.spines['top'].set(color=Open['gray'][shade_pos])
    ax_pulls.spines['top'].set(color=Open['gray'][shade_pos+1])

    # Now plot all the header and legend
    fig.text(0.71, 1-.2/h, "ATLAS", fontfamily='Tex Gyre Heros', fontsize='x-large',
            fontstyle='italic', fontweight='bold', va='baseline')
    fig.text(0.84, 1-.2/h, "Internal", fontfamily='Tex Gyre Heros', fontsize='x-large',
            va='baseline')
    fig.text(0.71, 1-.45/h, r"$\sqrt{s}=13\,$TeV, $139\,$fb$^{-1}$", va='baseline')

    title = r"$\mu$: " + cfg.ranking_POI_titles.get(POI_name, "signal strength")
    ax_impact.set_title(title, va='baseline', fontweight='bold',
            fontsize='large', color=Open['gray'][shade_pos+1], y=1, pad=25)

    handles_pulls, labels_pulls = ax_pulls.get_legend_handles_labels()
    pos_patch = Patch(color=Open['gray'][shade_pos])
    neg_patch = Patch(color=Open['gray'][shade_neg])
    handles_impact, labels_impact = ax_impact.get_legend_handles_labels()

    handles_left = handles_pulls + [pos_patch, neg_patch]
    labels_left = labels_pulls + [r"$+1\sigma$ Postfit Impact on $\mu$",
                    r"$-1\sigma$ Postfit Impact on $\mu$"]
    if plot_prefit_impact:
        handles_left.append(Patch(edgecolor=Open['gray'][shade_pos], ls='--', fill=False))
        labels_left.append("$1\sigma$ Prefit Impact on $\mu$")

    fig.legend(handles=handles_left, labels=labels_left, loc='upper left',
            bbox_to_anchor=(.05, 1), frameon=False,
            prop={'weight':'bold', 'size':'small'})
    fig.legend(handles=handles_impact, labels=labels_impact, loc='upper left',
            bbox_to_anchor=(.39, 1), frameon=False,
            prop={'weight':'bold', 'size':'small'})

    # Alternate gray bands
    for i in range(nNPs//2):
        ax_impact.axhspan(ymin=.5+2*i, ymax=1.5+2*i, color=Open['gray'][1], zorder=-1)

    for ext in cfg.formats:
        plt.savefig(f"{plot_fname}.{ext}", dpi=200)
    plt.close()



if __name__ == "__main__":
# Why do I get so much debug ?
    plt.set_loglevel("info")
    pil_logger = logging.getLogger('PIL')
    pil_logger.setLevel(logging.INFO)
    main()
