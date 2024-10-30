"""
Generate summary plot of 1D confidence intervals.

Author: Philipp Windischhofer
Date:   March 2020
Email:  philipp.windischhofer@cern.ch
"""


import ROOT, os
import numpy as np

from array import array
from argparse import ArgumentParser
from plotLikelihoodLandscape import GetConfidenceInterval, Tree2Dict, operator_namer, _drawATLASLabel, _drawText
from analysisPlottingConfig import Config

def plot_CIs(labels, CIs_68_linear, CIs_95_linear, bestfits_linear, CIs_68_quadratic, CIs_95_quadratic, bestfits_quadratic, outfile, xmin = None, xmax = None, xlabel = "c_{i}", year = "6051", SFs = None, longplot = False, add_table = True, is_exp = False, inner_label = None):

    if SFs is None:
        SFs = [1.0 for cur in labels]

    color_linear = ROOT.kAzure - 5
    color_quadratic = ROOT.kOrange - 3
    linear_quadratic_spacing = 0.2

    ROOT.gStyle.SetOptStat(0)

    number_lines = len(labels)

    if longplot:
        canv = ROOT.TCanvas("canv", "canv", 800, 1000)
    else:
        canv = ROOT.TCanvas("canv", "canv", 800, 600)
    ROOT.SetOwnership(canv, False)

    if longplot:
        ROOT.gPad.SetLeftMargin(0.20)
    else:
        ROOT.gPad.SetLeftMargin(0.17)

    ROOT.gPad.SetTopMargin(0.02)

    if longplot:
        ROOT.gPad.SetBottomMargin(0.11)
    else:
        ROOT.gPad.SetBottomMargin(0.13)

    ROOT.gPad.SetRightMargin(0.05)

    mg = ROOT.TMultiGraph()
    ROOT.SetOwnership(mg, False)

    # make the base object
    if longplot:
        number_bins = int(len(labels) * 1.4)
    else:
        number_bins = int(len(labels) * 1.8)

    if not xmin:
        xmin = min(map(np.min, CIs_95))

    if not xmax:
        xmax = max(map(np.max, CIs_95))

    # settings for the extent of the table region on the right
    if longplot:
        table_width = 8.5
    else:
        table_width = 6.5

    if not add_table:
        table_width = 0.0

    base = ROOT.TH2D("base", "", 20, xmin, xmax + table_width, number_bins, -0.5, number_bins - 0.5)
    ROOT.SetOwnership(base, False)
    base.SetFillStyle(0)
    base.GetXaxis().SetTitle(xlabel)
    base.GetXaxis().SetTitleSize(0.05)
    base.GetXaxis().SetLabelSize(0.05)
    base.GetYaxis().SetTitleSize(0.06)
    if longplot:
        base.GetYaxis().SetLabelSize(0.052)
    else:
        base.GetYaxis().SetLabelSize(0.063)
    base.GetYaxis().SetTickSize(0)
    base.GetYaxis().SetTickLength(0)

    for ind, (cur_label, cur_SF) in enumerate(zip(labels, SFs)):
        if cur_SF != 1.0:
            cur_label = f"{cur_label}  [#times {cur_SF}]"

        base.GetYaxis().SetBinLabel(ind + 1, cur_label)

    base.Draw()

    l = ROOT.TLine()
    ROOT.SetOwnership(l, False)
    l.SetLineColor(ROOT.kGray)
    l.SetLineWidth(2)
    l.SetLineStyle(2)
    l.DrawLine(0.0, -0.5, 0.0, len(bestfits_linear) - 0.5)

    # Draw the CIs
    def draw_CIs(CIs, color, ls, lw = 3, y_offset = 0.0, SFs = None):
        if SFs is None:
            SFs = [1.0 for cur in CIs]

        graph_objs = []

        ROOT.SetOwnership(l, False)
        for cur_y, (cur_CI, cur_SF) in enumerate(zip(CIs, SFs)):
            cur_y += y_offset
            for cur_beginning, cur_end in cur_CI:
                if cur_beginning is None or cur_end is None:
                    continue

                cur_beginning *= cur_SF
                cur_end *= cur_SF

                print("---")
                print(f"[{cur_beginning}, {cur_end}]")

                center = cur_end if abs(cur_end) < abs(cur_beginning) else cur_beginning
                unc_down = abs(cur_end - center)
                unc_up = abs(cur_beginning - center)

                print(f"center = {center}, unc_up = {unc_up}, unc_down = {unc_down}")
                print("---")

                cur_graph = ROOT.TGraphAsymmErrors(1, array('d', [center]), array('d', [cur_y]), array('d', [unc_up]), array('d', [unc_down]), array('d', [0.0]), array('d', [0.0]))
                ROOT.SetOwnership(cur_graph, False)
                cur_graph.SetLineWidth(lw)
                cur_graph.SetLineStyle(ls)
                cur_graph.SetLineColor(color)
                graph_objs.append(cur_graph)
                cur_graph.Draw("same lz")
        return graph_objs

    draw_CIs(CIs_68_linear, color_linear, SFs = SFs, ls = 0, lw = 4, y_offset = linear_quadratic_spacing / 2)
    draw_CIs(CIs_95_linear, color_linear, SFs = SFs, ls = 2, lw = 2, y_offset = linear_quadratic_spacing / 2)

    draw_CIs(CIs_68_quadratic, color_quadratic, SFs = SFs, ls = 0, lw = 4, y_offset = -linear_quadratic_spacing / 2)
    draw_CIs(CIs_95_quadratic, color_quadratic, SFs = SFs, ls = 2, lw = 2, y_offset = -linear_quadratic_spacing / 2)

    if add_table:
        # draw white rectangle as background for the section of numerical values
        label_background = ROOT.TBox(xmax, base.GetYaxis().GetXmin(), base.GetXaxis().GetXmax() - 0.1, base.GetYaxis().GetXmax() - 0.1)
        label_background.SetFillColor(ROOT.kWhite)
        label_background.Draw()
        canv.RedrawAxis()

        l = ROOT.TLine()
        ROOT.SetOwnership(l, False)
        l.SetLineColor(ROOT.kGray)
        l.SetLineWidth(2)
        l.SetLineStyle(2)
        l.DrawLine(xmax, -0.5, xmax, len(bestfits_linear) + 0.3)

    def draw_bestfits(bestfits, y_offset, SFs):
        y_vals = [y_offset + ind for ind in range(len(bestfits))]
        x_vals = [cur_bestfit * cur_SF for cur_bestfit, cur_SF in zip(bestfits, SFs)]
        bestfit_graph = ROOT.TGraph(len(bestfits), array('d', x_vals), array('d', y_vals))
        ROOT.SetOwnership(bestfit_graph, False)
        bestfit_graph.SetMarkerColor(1)
        bestfit_graph.SetMarkerStyle(20)
        bestfit_graph.SetMarkerSize(1.2)
        bestfit_graph.Draw("same p")

        return bestfit_graph

    # finally the best-fit values ...
    draw_bestfits(bestfits_linear, SFs = SFs, y_offset = linear_quadratic_spacing / 2)
    draw_bestfits(bestfits_quadratic, SFs = SFs, y_offset = -linear_quadratic_spacing / 2)

    # ... and some labels and legends
    plotconf = Config(options = [])
    plotconf._year = year

    if inner_label is None:
        runinfo = plotconf.get_run_info()
        lumi, energy = list(runinfo.values())[0]
        signaldesc = plotconf.signal[0]
        lambdaval = plotconf.EFT_lambda
        inner_label = f"#splitline{{#sqrt{{s}} = {energy} TeV, {lumi} fb^{{-1}}}}{{{signaldesc}, #Lambda = {lambdaval} TeV}}"

    if longplot:
        inner_label_y = 0.94
        inner_label_x = 0.21
        _drawATLASLabel(inner_label_x, inner_label_y, "  " + plotconf.ATLAS_suffix, fontsize = 0.04)
        _drawText(inner_label_x + 0.38, inner_label_y - 0.035, inner_label, fontsize = 0.035)
    else:
        inner_label_y = 0.94
        inner_label_x = 0.2
        _drawATLASLabel(inner_label_x, inner_label_y, plotconf.ATLAS_suffix, fontsize = 0.045)
        _drawText(inner_label_x + 0.42, inner_label_y - 0.05, inner_label, fontsize = 0.04)

    inner_label_y = 0.92

    # prepare the legends
    CI_68_dummy = ROOT.TGraph()
    ROOT.SetOwnership(CI_68_dummy, False)
    CI_68_dummy.SetLineStyle(0)
    CI_68_dummy.SetLineWidth(4)

    CI_95_dummy = ROOT.TGraph()
    ROOT.SetOwnership(CI_95_dummy, False)
    CI_95_dummy.SetLineStyle(2)
    CI_95_dummy.SetLineWidth(2)

    if longplot:
        CI_legend = ROOT.TLegend(inner_label_x, inner_label_y - 0.07, inner_label_x + 0.35, inner_label_y - 0.02)
    else:
        CI_legend = ROOT.TLegend(inner_label_x, inner_label_y - 0.09, inner_label_x + 0.3, inner_label_y - 0.04)

    ROOT.SetOwnership(CI_legend, False)
    CI_legend.SetBorderSize(0)
    CI_legend.SetFillStyle(0)
    if longplot:
        CI_legend.SetTextSize(0.035)
    else:
        CI_legend.SetTextSize(0.041)
    CI_legend.SetNColumns(2)
    CI_legend.AddEntry(CI_68_dummy, "68% CL", "l")
    CI_legend.AddEntry(CI_95_dummy, "95% CL", "l")
    CI_legend.Draw("same")

    linear_dummy = ROOT.TGraph()
    ROOT.SetOwnership(linear_dummy, False)
    linear_dummy.SetMarkerStyle(21)
    linear_dummy.SetMarkerSize(2)
    linear_dummy.SetMarkerColor(color_linear)

    quadratic_dummy = ROOT.TGraph()
    ROOT.SetOwnership(linear_dummy, False)
    quadratic_dummy.SetMarkerStyle(21)
    quadratic_dummy.SetMarkerSize(2)
    quadratic_dummy.SetMarkerColor(color_quadratic)

    if longplot:
        style_legend = ROOT.TLegend(inner_label_x - 0.019, inner_label_y - 0.07, inner_label_x + 0.68, inner_label_y - 0.11)
    else:
        style_legend = ROOT.TLegend(inner_label_x - 0.018, inner_label_y - 0.11, inner_label_x + 0.57, inner_label_y - 0.15)

    obsexp_suffix = " (exp.)" if is_exp else " (obs.)"

    ROOT.SetOwnership(style_legend, False)
    style_legend.SetBorderSize(0)
    style_legend.SetFillStyle(0)
    if longplot:
        style_legend.SetTextSize(0.035)
    else:
        style_legend.SetTextSize(0.041)
    style_legend.SetNColumns(2)
    style_legend.AddEntry(linear_dummy, "Linear" + obsexp_suffix, "p")
    style_legend.AddEntry(quadratic_dummy, "Linear + quadratic" + obsexp_suffix, "p")
    style_legend.Draw("same")

    # legend for best fit
    bestfit_dummy = ROOT.TGraph()
    ROOT.SetOwnership(bestfit_dummy, False)
    bestfit_dummy.SetLineWidth(0)
    bestfit_dummy.SetLineColor(0)
    bestfit_dummy.SetFillColor(0)
    bestfit_dummy.SetFillStyle(0)
    bestfit_dummy.SetMarkerColor(1)
    bestfit_dummy.SetMarkerStyle(20)
    bestfit_dummy.SetMarkerSize(1.2)

    if longplot:
        bestfit_legend = ROOT.TLegend(inner_label_x - 0.019, inner_label_y - 0.15, inner_label_x + 0.33, inner_label_y - 0.11)
    else:
        bestfit_legend = ROOT.TLegend(inner_label_x - 0.019, inner_label_y - 0.25, inner_label_x + 0.28, inner_label_y - 0.15)

    ROOT.SetOwnership(bestfit_legend, False)
    bestfit_legend.SetBorderSize(0)
    bestfit_legend.SetFillStyle(0)
    if longplot:
        bestfit_legend.SetTextSize(0.035)
    else:
        bestfit_legend.SetTextSize(0.041)
    bestfit_legend.AddEntry(bestfit_dummy, "Best-fit" + obsexp_suffix)
    bestfit_legend.Draw("same")

    if add_table:
        # build up the table section with the numerical values of the limits
        def format_CI(CI):
            elems = []
            for cur_beginning, cur_end in CI:
                if cur_beginning is None or cur_end is None:
                    continue

                elems.append("[{}, {}]".format(("%#.2g" % cur_beginning).rstrip('.'), ("%#.2g" % cur_end).rstrip('.')))

            return " #cup ".join(elems)

        def write_CI_column(x_column, CIs, y_offset, fontsize):
            for cur_y, cur_CI in enumerate(CIs):
                cur_y += y_offset

                cur_string = format_CI(cur_CI)
                _drawText(x_column, cur_y, cur_string, fontsize = fontsize, doNDC = False, alignment = 22)
                print(cur_string)

        # write table
        if longplot:
            table_fontsize = 0.03
            linear_offset = 1.9
            quadratic_offset = 6.1
        else:
            table_fontsize = 0.035
            linear_offset = 1.5
            quadratic_offset = 4.7

        write_CI_column(xmax + linear_offset, CIs_68_linear, y_offset = linear_quadratic_spacing / 2, fontsize = table_fontsize)
        write_CI_column(xmax + quadratic_offset, CIs_68_quadratic, y_offset = linear_quadratic_spacing / 2, fontsize = table_fontsize)

        # write table header
        _drawText(text = "#bf{Linear}", x = xmax + linear_offset, y = len(CIs_68_linear) + 0.1, fontsize = table_fontsize, alignment = 21, doNDC = False)
        _drawText(text = "68% CL", x = xmax + linear_offset, y = len(CIs_68_linear) - 0.3, fontsize = table_fontsize, alignment = 21, doNDC = False)

        _drawText(text = "#bf{Linear + quadratic}", x = xmax + quadratic_offset, y = len(CIs_68_linear) + 0.1, fontsize = table_fontsize, alignment = 21, doNDC = False)
        _drawText(text = "68% CL", x = xmax + quadratic_offset, y = len(CIs_68_linear) - 0.3, fontsize = table_fontsize, alignment = 21, doNDC = False)

    canv.SaveAs(outfile)
    outfile_png_path = os.path.splitext(outfile)[0] + ".png"
    canv.SaveAs(outfile_png_path) # always also save as png for webpage

    outfile_path = os.path.splitext(outfile)[0] + ".C"
    canv.SaveAs(outfile_path)

def get_1d_best_fit(path):
    try:
        return Tree2Dict(path, "bestFit")
    except OSError:
        print(f"Problem when reading from '{path}'.")
        return None

def get_1d_best_fit_manual(path):
    try:
        cur_data = Tree2Dict(path, "NLLscan")
    except OSError as e:
        print(f"Problem when reading from '{path}'.")
        return None

    domain_columns = [col for col in cur_data.keys() if "NLL" not in col]
    if len(domain_columns) != 1:
        raise NotImplementedError("This function only works with 1d NLL scans -- please check your settings!")

    x_column = domain_columns[0]

    xvals = np.array(cur_data[x_column])
    yvals = np.array(cur_data["NLL"])

    return xvals[np.argmin(yvals)]

def get_1d_CI(path, CL):

    # load the data
    try:
        cur_data = Tree2Dict(path, "NLLscan")
    except OSError as e:
        print(f"Problem when reading from '{path}'.")
        return (None, None)

    domain_columns = [col for col in cur_data.keys() if "NLL" not in col]
    if len(domain_columns) != 1:
        raise NotImplementedError("This function only works with 1d NLL scans -- please check your settings!")

    x_column = domain_columns[0]

    # make sure that everything is centered at zero
    minval = min(cur_data["NLL"])
    cur_data["NLL"] = np.array(cur_data["NLL"])
    cur_data["NLL"] -= minval

    # proceed to get the CI
    CI = GetConfidenceInterval(cur_data[x_column], cur_data["NLL"], CL)
    return x_column, CI

def make1DLimitsSummaryPlot(run_dirs_linear, run_dirs_quadratic, outfile, year, range_xaxis, exp = False, operator_order = [], add_table = True, **kwargs):

    SF_library = {
        "cHq3": 10.0,
        "cHq1": 2.0,
        "cHW": 2.0,
        "cHu": 5.0,
        "cdHAbs": 0.05,
        "cHWB": 0.5,
        "cHB": 0.1,
        "cHl3": 0.1,
        "cll1": 0.1,
        "cHbox": 0.1,
        "cHl1": 0.05,
        "cHDD": 0.05,
        "cHe": 0.03
    }

    plotconf = Config(options = [])
    plotconf._year = year

    def read_CIs(run_dirs, CL):

        CIs = {}
        for run_dir in run_dirs:

            # need to load both expected and observed NLL scan results
            if exp:
                scan_result = os.path.join(run_dir, "LikelihoodLandscape", "Asimov", "LikelihoodLandscape_out.root")
            else:
                scan_result = os.path.join(run_dir, "LikelihoodLandscape", "Data", "LikelihoodLandscape_out.root")

            # get the 1D confidence intervals to show on the plots
            operator, CI = get_1d_CI(scan_result, CL)
            CIs[operator] = CI

        return CIs

    def read_bestfits(run_dirs):
        bestfits = {}
        for run_dir in run_dirs:

            # need to load both expected and observed NLL scan results
            if exp:
                scan_result = os.path.join(run_dir, "LikelihoodLandscape", "Asimov", "LikelihoodLandscape_out.root")
            else:
                scan_result = os.path.join(run_dir, "LikelihoodLandscape", "Data", "LikelihoodLandscape_out.root")

            operator, _ = get_1d_CI(scan_result, 1.0)

            if operator == "cHe":
                bestfit_to_use = get_1d_best_fit_manual(scan_result)
            else:
                bestfit_to_use = get_1d_best_fit(scan_result)[operator][0]

            bestfits[operator] = bestfit_to_use

        return bestfits

    # read the CIs from the individual fit results
    print("read linear")
    bestfits_linear = read_bestfits(run_dirs_linear)
    CIs_68_linear = read_CIs(run_dirs_linear, 0.494475)
    CIs_95_linear = read_CIs(run_dirs_linear, 1.92072)

    print("read quadratic")
    bestfits_quadratic = read_bestfits(run_dirs_quadratic)
    CIs_68_quadratic = read_CIs(run_dirs_quadratic, 0.494475)
    CIs_95_quadratic = read_CIs(run_dirs_quadratic, 1.92072)

    # compose everything in the form needed for plotting
    if not operator_order:
        operator_order = list(set(list(bestfits_linear.keys()) + list(bestfits_quadratic.keys())))

    labels = []
    SFs = []

    CIs_68_linear_to_plot = []
    CIs_95_linear_to_plot = []
    bestfits_linear_to_plot = []

    CIs_68_quadratic_to_plot = []
    CIs_95_quadratic_to_plot = []
    bestfits_quadratic_to_plot = []

    for cur_operator in operator_order:
        if cur_operator in SF_library:
            SFs.append(SF_library[cur_operator])
        else:
            SFs.append(1.0)

        labels.append(operator_namer(cur_operator, plotconf))

        if cur_operator in CIs_68_linear:
            CIs_68_linear_to_plot.append(CIs_68_linear[cur_operator])
            CIs_95_linear_to_plot.append(CIs_95_linear[cur_operator])
            bestfits_linear_to_plot.append(bestfits_linear[cur_operator])
        else:
            CIs_68_linear_to_plot.append([(1e4, 2e4)])
            CIs_95_linear_to_plot.append([(1e4, 2e4)])
            bestfits_linear_to_plot.append(1e4)

        if cur_operator in CIs_68_quadratic:
            CIs_68_quadratic_to_plot.append(CIs_68_quadratic[cur_operator])
            CIs_95_quadratic_to_plot.append(CIs_95_quadratic[cur_operator])
            bestfits_quadratic_to_plot.append(bestfits_quadratic[cur_operator])
        else:
            CIs_68_quadratic_to_plot.append([(None, None)])
            CIs_95_quadratic_to_plot.append([(None, None)])
            bestfits_quadratic_to_plot.append(1e4)

    assert len(CIs_68_linear_to_plot) == len(CIs_68_quadratic_to_plot)
    assert len(CIs_95_linear_to_plot) == len(CIs_95_quadratic_to_plot)

    plot_CIs(labels, CIs_68_linear_to_plot, CIs_95_linear_to_plot, bestfits_linear_to_plot, CIs_68_quadratic_to_plot, CIs_95_quadratic_to_plot, bestfits_quadratic_to_plot, outfile,
             SFs = SFs, xmin = -3.6, xmax = 3.0, xlabel = "Parameter value", add_table = add_table, is_exp = exp, **kwargs)

if __name__ == "__main__":
    parser = ArgumentParser(description = "make summary plots")
    parser.add_argument("--run_dirs_linear", nargs = '+', dest = "run_dirs_linear", help = "path to the individual fit directories")
    parser.add_argument("--run_dirs_quadratic", nargs = '+', dest = "run_dirs_quadratic", help = "path to the individual fit directories")
    parser.add_argument("--outfile", action = "store", dest = "outfile", help = "path to the generated plot")
    parser.add_argument("--year", action = "store", dest = "year", default = "6051", help = "data-taking periods used to make this plot, following WSMaker convention. Default: 6051, i.e. full Run 2")
    parser.add_argument("--exp", action = "store_const", const = "True", default = False)
    parser.add_argument("--xrange", action = "store", dest = "range_xaxis", help = "x-axis range", type = float)
    parser.add_argument("--operator_order", action = "store", dest = "operator_order", nargs = '+', default = [])
    parser.add_argument("--longplot", action = "store_const", const = True, default = False)
    parser.add_argument("--add_table", action = "store_const", const = True, default = False)
    args = vars(parser.parse_args())

    make1DLimitsSummaryPlot(**args)
