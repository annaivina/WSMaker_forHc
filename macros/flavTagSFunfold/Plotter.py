import ROOT
from array import array
import numpy as np

ROOT.gStyle.SetOptStat(0)

class Plotter:
    """
    Utility class providing some plotting functions to visualise the prefit / postfit correspondence of the SFs.

    Author: Philipp Windischhofer
    Date:   November 2019
    Email:  philipp.windischhofer@cern.ch
    """

    @staticmethod
    def plot_curves(curves_x, curves_y, uncs, line_colors, unc_colors, labels, outfile, ratio_reference = None, xlabel = "p_{T} [GeV]", ylabel = "SF", inner_label = ""):
        """
        Simple function to plot curves specified by (x, y) points.
        """
        if len(uncs) != len(curves_x):
            uncs = [[] for cur in curves_x]

        canv = ROOT.TCanvas("canv", "canv", 800, 600)
        ROOT.SetOwnership(canv, False)

        yrange_abs = (0.7 * np.min(np.array(curves_y) - np.array(uncs)), 1.5 * np.max(np.array(curves_y) + np.array(uncs)))

        if ratio_reference is not None:
            # compute the curves that will be shown in the ratio pane
            ratio_curves_y, ratio_uncs = Plotter._get_ratio_curve_uncs(curves_y, uncs, ratio_reference)
            yrange_ratio = (0.9 - np.max(ratio_uncs), 1.1 + np.max(ratio_uncs))

            # make sure to also show the ratios, if requested
            number_pads = 2
            curves_x_to_plot = [curves_x, curves_x]
            curves_y_to_plot = [curves_y, ratio_curves_y]
            uncs_to_plot = [uncs, ratio_uncs]
            line_colors_to_plot = [line_colors, line_colors]
            unc_colors_to_plot = [unc_colors, unc_colors]
            ylabels_to_plot = [ylabel, "rel. uncertainty"]
            pad_dividers = [1.0, 0.4, 0.0]
            yrange_to_plot = [yrange_abs, yrange_ratio]
        else:
            # only have one pane with the absolute SF values
            number_pads = 1
            curves_x_to_plot = [curves_x]
            curves_y_to_plot = [curves_y]
            uncs_to_plot = [uncs]
            line_colors_to_plot = [line_colors]
            unc_colors_to_plot = [unc_colors]
            pad_dividers = [1.0, 0.0]
            yrange_to_plot = [yrange_abs]

        pad_objs = []
        pads = []
        pad_height = 1.0 / number_pads

        for ind, (cur_curves_x, cur_curves_y, cur_uncs, cur_line_colors, cur_unc_colors, cur_ylabel, pad_y_start, pad_y_end, cur_yrange) in enumerate(zip(curves_x_to_plot, curves_y_to_plot, uncs_to_plot, line_colors_to_plot, unc_colors_to_plot, ylabels_to_plot, pad_dividers[:-1], pad_dividers[1:], yrange_to_plot)):
            canv.cd()
            cur_name = f"Pad_{ind}"
            cur_pad = ROOT.TPad(cur_name, cur_name, 0.0, pad_y_start, 1.0, pad_y_end)
            ROOT.SetOwnership(cur_pad, False)
            cur_pad.Draw()

            cur_pad.cd()

            # use ticks on all sides
            ROOT.gPad.SetTickx()
            ROOT.gPad.SetTicky()
                        
            cur_pad.SetTopMargin(0.02)
            cur_pad.SetLeftMargin(0.08)
            cur_pad.SetRightMargin(0.02)

            # create the subplot
            cur_pad_objs = Plotter._subplot_curves(cur_pad, cur_curves_x, cur_curves_y, cur_uncs, cur_line_colors, cur_unc_colors, xlabel, cur_ylabel, cur_yrange)
            pad_objs.append(cur_pad_objs)
            pads.append(cur_pad)
            
        leg = ROOT.TLegend(0.6, 0.75, 0.9, 0.9)
        ROOT.SetOwnership(leg, False)
        leg.SetNColumns(len(curves_x))
        leg.SetFillStyle(0)
        leg.SetBorderSize(0)
        leg.SetTextFont(42)
        leg.SetTextSize(0.035)

        for obj, label in zip(pad_objs[0], labels):
            leg.AddEntry(obj, label, "l")

        # draw legend and labels in the first pad
        pads[0].cd()
        leg.Draw()
        Plotter._drawATLASLabel(0.12, 0.88, "Internal", fontsize = 0.05)
        Plotter._drawText(0.12, 0.79, inner_label, fontsize = 0.04)

        canv.SaveAs(outfile)

    @staticmethod
    def plot_categories(cat_labels, cat_values, cat_uncs, labels, inner_label, line_colors, unc_colors, outfile, ylabel = "SF", xlabel = "tagweight bin", ratio_reference = None):
        """
        Simple function to generate a categorical plot.
        """
        canv = ROOT.TCanvas("canv", "canv", 800, 600)
        ROOT.SetOwnership(canv, False)

        yrange_abs = (0.7 * np.min(np.array(cat_values) - np.array(cat_uncs)), 1.5 * np.max(np.array(cat_values) + np.array(cat_uncs)))

        if ratio_reference is not None:
            # compute the curves that will be shown in the ratio pane
            ratio_cat_values, cat_ratio_uncs = Plotter._get_ratio_curve_uncs(cat_values, cat_uncs, ratio_reference)
            yrange_ratio = (0.9 - np.max(cat_ratio_uncs), 1.1 + np.max(cat_ratio_uncs))

            # make sure to also show the ratios, if requested
            number_pads = 2
            cat_values_to_plot = [cat_values, ratio_cat_values]
            cat_uncs_to_plot = [cat_uncs, cat_ratio_uncs]
            line_colors_to_plot = [line_colors, line_colors]
            unc_colors_to_plot = [unc_colors, unc_colors]
            ylabels_to_plot = [ylabel, "rel. uncertainty"]
            pad_dividers = [1.0, 0.4, 0.0]
            yrange_to_plot = [yrange_abs, yrange_ratio]
        else:
            # only have one pane with the absolute SF values
            number_pads = 1
            cat_values_to_plot = [cat_values]
            cat_uncs_to_plot = [cat_uncs]
            line_colors_to_plot = [line_colors]
            unc_colors_to_plot = [unc_colors]
            pad_dividers = [1.0, 0.0]
            ylabels_to_plot = [ylabel]
            yrange_to_plot = [yrange_abs]

        pad_objs = []
        pads = []
        pad_height = 1.0 / number_pads

        for ind, (cur_cat_values, cur_cat_uncs, cur_line_colors, cur_unc_colors, cur_ylabel, pad_y_start, pad_y_end, cur_yrange) in enumerate(zip(cat_values_to_plot, cat_uncs_to_plot, line_colors_to_plot, unc_colors_to_plot, ylabels_to_plot, pad_dividers[:-1], pad_dividers[1:], yrange_to_plot)):
            canv.cd()
            cur_name = f"Pad_{ind}"
            cur_pad = ROOT.TPad(cur_name, cur_name, 0.0, pad_y_start, 1.0, pad_y_end)
            ROOT.SetOwnership(cur_pad, False)
            cur_pad.Draw()

            cur_pad.cd()

            # use ticks on all sides
            ROOT.gPad.SetTickx()
            ROOT.gPad.SetTicky()
                        
            cur_pad.SetTopMargin(0.02)
            cur_pad.SetLeftMargin(0.08)
            cur_pad.SetRightMargin(0.02)

            # create the subplot
            cur_pad_objs = Plotter._subplot_categories(cur_pad, cat_labels, cur_cat_values, cur_cat_uncs, cur_line_colors, cur_unc_colors, labels, xlabel, cur_ylabel, cur_yrange)
            pad_objs.append(cur_pad_objs)
            pads.append(cur_pad)
            
        leg = ROOT.TLegend(0.6, 0.75, 0.9, 0.9)
        ROOT.SetOwnership(leg, False)
        leg.SetNColumns(len(labels))
        leg.SetFillStyle(0)
        leg.SetBorderSize(0)
        leg.SetTextFont(42)
        leg.SetTextSize(0.035)

        for obj, label in zip(pad_objs[0], labels):
            leg.AddEntry(obj, label, "l")

        # draw legend and labels in the first pad
        pads[0].cd()
        leg.Draw()
        Plotter._drawATLASLabel(0.12, 0.88, "Internal", fontsize = 0.05)
        Plotter._drawText(0.12, 0.79, inner_label, fontsize = 0.04)

        canv.SaveAs(outfile)

    # internal helper methods
    @staticmethod
    def _subplot_categories(pad, cat_labels, cat_values, cat_uncs, line_colors, unc_colors, series_labels, xlabel, ylabel, yrange):
        pad.cd()

        objs = []

        for series_label, line_color, cur_unc_color, cur_cat_values, cur_cat_uncs in zip(series_labels, line_colors, unc_colors, cat_values, cat_uncs):
            number_cats = len(cat_labels)
            cur_hist = ROOT.TH1F(series_label, "", number_cats, 0.0, number_cats)
            ROOT.SetOwnership(cur_hist, False)
            cur_hist.SetLineColor(line_color)
            cur_hist.SetLineWidth(2)
            cur_hist.SetMarkerColor(line_color)
            cur_hist.SetFillStyle(0)
            cur_hist.SetFillColor(0)

            cur_unc_hist = ROOT.TH1F(series_label + "_uncs", "", number_cats, 0.0, number_cats)
            ROOT.SetOwnership(cur_unc_hist, False)
            cur_unc_hist.SetFillStyle(1001)
            cur_unc_hist.SetFillColorAlpha(cur_unc_color, 0.5)
            cur_unc_hist.SetMarkerSize(0.0)

            # fill the histogram for the current data series
            for ind, (cat_label, cat_data, cat_uncertainty) in enumerate(zip(cat_labels, cur_cat_values, cur_cat_uncs)):
                cur_hist.GetXaxis().SetBinLabel(ind + 1, cat_label)
                cur_unc_hist.GetXaxis().SetBinLabel(ind + 1, cat_label)
                
                cur_hist.SetBinContent(ind + 1, cat_data)
                cur_hist.SetBinError(ind + 1, 1e-6)

                cur_unc_hist.SetBinContent(ind + 1, cat_data)
                cur_unc_hist.SetBinError(ind + 1, cat_uncertainty + 1e-6)

            objs.append(cur_hist)
            cur_unc_hist.Draw("axis same e2")
            cur_hist.Draw("axis same e")

            cur_hist.GetYaxis().SetTitle(ylabel)
            cur_hist.GetXaxis().SetTitleFont(43)
            cur_hist.GetXaxis().SetTitleSize(13)
            cur_hist.GetYaxis().SetTitleFont(43)
            cur_hist.GetYaxis().SetTitleSize(13)
            cur_hist.GetXaxis().SetLabelFont(43)
            cur_hist.GetXaxis().SetLabelSize(13)
            cur_hist.GetYaxis().SetLabelFont(43)
            cur_hist.GetYaxis().SetLabelSize(13)
            cur_hist.GetYaxis().SetTitleOffset(1.4)
            cur_hist.GetXaxis().SetTitleOffset(1.1)

            cur_unc_hist.GetYaxis().SetTitle(ylabel)
            cur_unc_hist.GetXaxis().SetTitleFont(43)
            cur_unc_hist.GetXaxis().SetTitleSize(13)
            cur_unc_hist.GetYaxis().SetTitleFont(43)
            cur_unc_hist.GetYaxis().SetTitleSize(13)
            cur_unc_hist.GetXaxis().SetLabelFont(43)
            cur_unc_hist.GetXaxis().SetLabelSize(13)
            cur_unc_hist.GetYaxis().SetLabelFont(43)
            cur_unc_hist.GetYaxis().SetLabelSize(13)
            cur_unc_hist.GetYaxis().SetTitleOffset(1.4)
            cur_unc_hist.GetXaxis().SetTitleOffset(1.1)

            cur_unc_hist.Draw("same e2")
            cur_hist.Draw("same e")

        return objs

    @staticmethod
    def _drawText(x, y, text, color = ROOT.kBlack, fontsize = 0.05, font = 42, doNDC = True, alignment = 12):
        tex = ROOT.TLatex()
        if doNDC:
            tex.SetNDC()
        ROOT.SetOwnership(tex, False)
        tex.SetTextAlign(alignment)
        tex.SetTextSize(fontsize)
        tex.SetTextFont(font)
        tex.SetTextColor(color)
        tex.DrawLatex(x, y, text)        

    @staticmethod
    def _drawATLASLabel(x, y, text, doNDC = True, fontsize = 0.07):
        sep = 0.15 * ROOT.gPad.GetWh() / ROOT.gPad.GetWw()

        Plotter._drawText(x, y, "ATLAS", fontsize = fontsize, font = 72, doNDC = doNDC)
        Plotter._drawText(x + sep, y, text, fontsize = fontsize, font = 42, doNDC = doNDC)

    @staticmethod
    def _subplot_curves(pad, curves_x, curves_y, uncs, line_colors, unc_colors, xlabel = "", ylabel = "", yrange = (0.0, 1.5)):
        pad.cd()
        pad_objs = []

        mg = ROOT.TMultiGraph()
        ROOT.SetOwnership(mg, False)

        for curve_x, curve_y, unc_y, line_color, fill_color in zip(curves_x, curves_y, uncs, line_colors, unc_colors):
            if len(unc_y) != len(curve_x):
                unc_y = [0.0 for cur in curve_x]
            unc_x = [0.0 for cur in curve_x]

            cur_graph = ROOT.TGraphErrors(len(curve_x), array('d', curve_x), array('d', curve_y), array('d', unc_x), array('d', unc_y))
            ROOT.SetOwnership(cur_graph, False)
            cur_graph.SetLineWidth(4)
            cur_graph.SetLineColor(line_color)
            cur_graph.SetFillColorAlpha(fill_color, 0.5)
            cur_graph.SetFillStyle(1001)

            pad_objs.append(cur_graph)

            mg.Add(cur_graph, "l3")

        mg.GetXaxis().SetTitle(xlabel)
        mg.GetYaxis().SetTitle(ylabel)
        mg.GetYaxis().SetRangeUser(yrange[0], yrange[1])

        mg.Draw("alp")

        mg.GetXaxis().SetTitleFont(43)
        mg.GetXaxis().SetTitleSize(13)
        mg.GetXaxis().SetLabelFont(43)
        mg.GetXaxis().SetLabelSize(13)
        mg.GetYaxis().SetTitleFont(43)
        mg.GetYaxis().SetTitleSize(13)
        mg.GetYaxis().SetLabelFont(43)
        mg.GetYaxis().SetLabelSize(13)
        mg.GetYaxis().SetTitleOffset(1.4)
        mg.GetXaxis().SetTitleOffset(1.1)

        return pad_objs

    @staticmethod
    def _get_ratio_curve_uncs(curves_y, uncs, ratio_reference_y):
        ratio_uncs = [cur_unc / cur_curve_y for cur_unc, cur_curve_y in zip(uncs, curves_y)] # show the relative uncertainties ...
        ratio_curves = [np.ones_like(cur_curve_y) for cur_curve_y in curves_y] # ... around 1.0
        return ratio_curves, ratio_uncs
