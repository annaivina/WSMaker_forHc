import ROOT
from array import array
import math as m

from analysisPlottingConfig import Config

class STXSPlotter:
    """
    Class providing plotting functions that are useful e.g. for the visualisation of STXS fit results.

    Author: Philipp Windischhofer
    Date:   November 2019
    Email:  philipp.windischhofer@cern.ch
    """

    @staticmethod
    def plot_2D(mat, labels_x, labels_y, outfile, inner_label = "", label_z = "", label_threshold = 0.01, inner_label_x = 0.54, inner_label_y = 0.87):
        """
        Plot a 2D array, which will usually be a correlation matrix.
        Arguments:
            mat ... array to be plotted, expected as a nested list
            labels_x ... array of labels describing the columns of the matrix
            labels_y ... array of labels describing the rows of the matrix
            outfile ... full path to the generated plot (including filename extension)
            label_z ... label appearing next to the color bar
            label_threshold ... threshold value for a text label to be added for a matrix element
            inner_label ... label showing up in the plot, usually luminosity + COM energy
            inner_label_x / inner_label_y ... normalised coordinates for the placement of the ATLAS label and luminosity / energy
        """

        # get an instance of the analysis plotting configuration
        plotconf = Config(options = [])

        ROOT.gStyle.SetOptStat(0);
        ROOT.gStyle.SetOptTitle(0)

        # prepare the color scheme
        number_colors = 512;
        stops = array('d', [0.00, 0.50, 1.00])
        red   = array('d', [0.20, 1.00, 1.00])
        green = array('d', [0.20, 1.00, 0.20])
        blue  = array('d', [0.20, 1.00, 0.20])
        red   = array('d', [0.10, 1.00, 1.00])
        blue  = array('d', [1.00, 1.00, 0.20])
        ROOT.TColor.CreateGradientColorTable(3, stops, red, green, blue, number_colors);
        ROOT.gStyle.SetNumberContours(number_colors);

        # fill a TH2 with the correlation matrix values
        num_x_bins = len(mat)
        num_y_bins = len(mat[0])
        hist = ROOT.TH2F("hist", "hist", num_x_bins, 0, num_x_bins, num_y_bins, 0, num_y_bins)
        ROOT.SetOwnership(hist, False)

        # if matrix turns out to be symmetric, only fill (and show) half of the entries
        # set contents
        for ind_x in range(num_x_bins):
            for ind_y in range(num_y_bins):
                # convert to ROOT-based indexing, which starts from 1
                bin_x = ind_x + 1
                bin_y = ind_y + 1
                hist.SetBinContent(bin_x, bin_y, mat[ind_x][ind_y])
                
        # set axis labels
        for cur_bin, cur_label in enumerate(labels_x):
            hist.GetXaxis().SetBinLabel(cur_bin + 1, cur_label)

        for cur_bin, cur_label in enumerate(labels_y):
            hist.GetYaxis().SetBinLabel(cur_bin + 1, cur_label)

        hist.GetZaxis().SetTitle(label_z)
        hist.GetZaxis().SetTitleSize(0.03)
        hist.GetZaxis().SetTitleOffset(1.1)

        # prepare the canvas
        canv = ROOT.TCanvas("canv", "canv")
        ROOT.SetOwnership(canv, False)
        canv.cd()
        canv.SetLeftMargin(0.26)
        canv.SetBottomMargin(0.18)
        canv.SetRightMargin(0.17)
        canv.SetTopMargin(0.06)
        
        hist.SetMinimum(-1.0)
        hist.SetMaximum(1.0)
        hist.SetMarkerSize(1.0)
        hist.GetXaxis().SetLabelOffset(0.012)
        hist.GetXaxis().SetLabelSize(0.035)
        hist.GetYaxis().SetLabelSize(0.035)
        hist.GetZaxis().SetLabelOffset(0.015)
        hist.GetZaxis().SetLabelSize(0.04)
        hist.Draw("colz")
        
        # add labels for the individual entries
        t = ROOT.TLatex()
        ROOT.SetOwnership(t, False)
        t.SetTextAlign(22)
        t.SetTextFont(42)
        t.SetTextSize(0.02)
        for ind_x in range(num_x_bins):
            for ind_y in range(num_y_bins):
                bin_x = ind_x + 1
                bin_y = ind_y + 1
                
                cur_cont = hist.GetBinContent(bin_x, bin_y)
                if abs(cur_cont) > label_threshold:
                    t.DrawLatex(ind_x + 0.5, ind_y + 0.5, f"{cur_cont:.2g}")

        # add annotation label
        STXSPlotter._drawATLASLabel(inner_label_x, inner_label_y, plotconf.ATLAS_suffix, fontsize = 0.055)
        t.SetTextAlign(12)
        t.DrawLatexNDC(inner_label_x, inner_label_y - 0.1, inner_label)

        # put ticks on both sides
        ROOT.gPad.SetTickx()
        ROOT.gPad.SetTicky()
        
        canv.SaveAs(outfile)

    @staticmethod
    def plot_STXS_xsec(plotdata_WH, plotdata_ZH, outfile, ymin_abs = 2, ymax_abs = 8000, ymin_rel = -0.49, ymax_rel = 2.49, inner_label = "", legend_header = ""):
        """
        Generate nice plot of STXS cross sections, separately for WH and ZH.

        Arguments:
            plotdata_WH / plotdata_ZH ... dictionaries containing the data to be plotted, in the form
                                          {'labels': [...], 'central_values': [...], 'total_unc_hi': [...],
                                           'total_unc_lo': [...], 'stat_unc_hi': [...], 'stat_unc_lo': [...],
                                           'theory_values': [...], 'theory_unc': [...]}
            outfile ... full path to the output file (including filename extension)
            ymin_abs / ymax_abs ... lower / upper y-axis limit for the upper pane showing the absolute cross sections
            ymin_rel / ymax_rel ... lower / upper y-axis limit for the lower (ratio) pane
            inner_label ... string to be placed in the interior of the plot
            legend_header ... description to be placed immediately above the legend
        """

        plotconf = Config(options = [])

        ROOT.gStyle.SetOptStat(0)

        # have the following fields in the passed 'plotdata's:
        # labels, central_values, total_unc_hi, total_unc_lo, stat_unc_hi, stat_unc_lo, theory_values, theory_unc

        number_WH_bins = len(plotdata_WH["labels"])
        number_ZH_bins = len(plotdata_ZH["labels"])
        number_bins = number_WH_bins + number_ZH_bins

        # create the global Canvas and the pads for absolute and relative values
        canv = ROOT.TCanvas("canv", "canv", 800, 600)
        ROOT.SetOwnership(canv, False)
        canv.cd()

        pad_abs = ROOT.TPad("pad_abs", "pad_abs", 0., 0.37, 1., 1.)
        ROOT.SetOwnership(pad_abs, False)
        pad_rel = ROOT.TPad("pad_rel", "pad_rel", 0., 0.02,  1., 0.369)
        ROOT.SetOwnership(pad_rel, False)

        pad_abs.Draw()
        pad_abs.SetLogy()
        pad_rel.Draw()

        pad_abs.SetTopMargin(0.05)
        pad_abs.SetRightMargin(0.1)
        pad_abs.SetLeftMargin(0.15)
        pad_abs.SetBottomMargin(0.0)

        pad_rel.SetTopMargin(0.0)
        pad_rel.SetRightMargin(0.1)
        pad_rel.SetLeftMargin(0.15)
        pad_rel.SetBottomMargin(0.4)

        # prepare the base histogram for the upper (absolute) pane that holds the axes
        pad_abs.cd()
        base_abs = ROOT.TH1F("base_abs", "base_abs", number_bins, -0.5, number_bins - 0.5)
        ROOT.SetOwnership(base_abs, False)

        base_abs.GetXaxis().SetTickLength(0.0)
        base_abs.GetXaxis().SetBinLabel(1, "")
        base_abs.GetXaxis().SetLabelSize(0.0)
        base_abs.GetYaxis().SetTitle("#sigma_{i} #times #it{B}^{H}_{bb} #times #it{B}^{V}_{lep} [fb]")
        base_abs.GetYaxis().SetLabelSize(0.07)
        base_abs.GetYaxis().SetTitleSize(0.09)
        base_abs.GetYaxis().SetTitleOffset(0.7)
        base_abs.SetMaximum(ymax_abs)
        base_abs.SetMinimum(ymin_abs)
        base_abs.Draw("axis")

        # prepare the base histogram for the lower (relative) pane that holds the axes
        pad_rel.cd()
        base_rel = ROOT.TH1F("base_rel", "base_rel", number_bins, -0.5, number_bins - 0.5)
        ROOT.SetOwnership(base_rel, False)

        base_rel.GetXaxis().SetTickLength(0)
        base_rel.GetXaxis().SetBinLabel(1,"")
        base_rel.GetYaxis().SetTitle("Ratio to SM ")
        base_rel.GetYaxis().SetLabelSize(0.12)
        base_rel.GetYaxis().SetTitleSize(0.12)
        base_rel.GetYaxis().SetTitleOffset(0.5)
        base_rel.GetYaxis().SetNdivisions(405)
        base_rel.SetMarkerSize(0)
        base_rel.SetMaximum(ymax_rel)
        base_rel.SetMinimum(ymin_rel)

        base_rel.GetXaxis().SetLabelOffset(0.04) 
        base_rel.GetXaxis().SetLabelSize(0.16)
        for ind, bin_label in enumerate(plotdata_WH["labels"] + plotdata_ZH["labels"]):
            base_rel.GetXaxis().SetBinLabel(ind + 1, bin_label)
        base_rel.Draw("axis")

        # prepare the values that are to be plotted
        obs_values_abs = plotdata_WH["central_values"] + plotdata_ZH["central_values"]
        total_unc_lo_abs = plotdata_WH["total_unc_lo"] + plotdata_ZH["total_unc_lo"]
        total_unc_hi_abs = plotdata_WH["total_unc_hi"] + plotdata_ZH["total_unc_hi"]
        stat_unc_lo_abs = plotdata_WH["stat_unc_lo"] + plotdata_ZH["stat_unc_lo"]
        stat_unc_hi_abs = plotdata_WH["stat_unc_hi"] + plotdata_ZH["stat_unc_hi"]
        theory_values_abs = plotdata_WH["theory_values"] + plotdata_ZH["theory_values"]
        theory_unc_abs = plotdata_WH["theory_unc"] + plotdata_ZH["theory_unc"]

        # this is done in this roundabout way to avoid picking up a dependency on numpy ...
        obs_values_rel = [cur_obs_value_abs / cur_theory_value_abs for cur_obs_value_abs, cur_theory_value_abs in zip(obs_values_abs, theory_values_abs)]
        total_unc_lo_rel = [cur_total_unc_lo_abs / cur_theory_value_abs for cur_total_unc_lo_abs, cur_theory_value_abs in zip(total_unc_lo_abs, theory_values_abs)]
        total_unc_hi_rel = [cur_total_unc_hi_abs / cur_theory_value_abs for cur_total_unc_hi_abs, cur_theory_value_abs in zip(total_unc_hi_abs, theory_values_abs)]
        stat_unc_lo_rel = [cur_stat_unc_lo_abs / cur_theory_value_abs for cur_stat_unc_lo_abs, cur_theory_value_abs in zip(stat_unc_lo_abs, theory_values_abs)]
        stat_unc_hi_rel = [cur_stat_unc_hi_abs / cur_theory_value_abs for cur_stat_unc_hi_abs, cur_theory_value_abs in zip(stat_unc_hi_abs, theory_values_abs)]
        theory_values_rel = [cur_theory_value_abs / cur_theory_value_abs for cur_theory_value_abs in theory_values_abs]
        theory_unc_rel = [cur_theory_unc_abs / cur_theory_value_abs for cur_theory_unc_abs, cur_theory_value_abs in zip(theory_unc_abs, theory_values_abs)]

        # populate the upper ("absolute") pane
        objs_abs = STXSPlotter._subplot_STXS_xsec(obs_values = obs_values_abs,
                                                            total_unc_lo = total_unc_lo_abs,
                                                            total_unc_hi = total_unc_hi_abs,
                                                            stat_unc_lo = stat_unc_lo_abs,
                                                            stat_unc_hi = stat_unc_hi_abs,
                                                            theory_values = theory_values_abs,
                                                            theory_unc = theory_unc_abs,
                                                            pad = pad_abs,
                                                            name = "abs")

        # populate the lower ("relative") pane
        STXSPlotter._subplot_STXS_xsec(obs_values = obs_values_rel,
                                                 total_unc_lo = total_unc_lo_rel,
                                                 total_unc_hi = total_unc_hi_rel,
                                                 stat_unc_lo = stat_unc_lo_rel,
                                                 stat_unc_hi = stat_unc_hi_rel,
                                                 theory_values = theory_values_rel,
                                                 theory_unc = theory_unc_rel,
                                                 pad = pad_rel,
                                                 name = "rel")

        # draw a vertical line separating WH and ZH
        pad_abs.cd()
        STXSPlotter._drawLine(number_WH_bins - 0.5, ymin_abs, number_WH_bins - 0.5, ymax_abs ** 0.66, width = 2, style = 7, color = ROOT.kBlack)

        pad_rel.cd()
        STXSPlotter._drawLine(number_WH_bins - 0.5, ymin_rel, number_WH_bins - 0.5, ymax_rel, width = 2, style = 7, color = ROOT.kBlack)

        # draw the legend and labels
        pad_abs.cd()
        STXSPlotter._drawATLASLabel(0.18, 0.88, plotconf.ATLAS_suffix)
        STXSPlotter._drawText(0.18, 0.78, inner_label, fontsize = 0.06)

        STXSPlotter._drawText(number_WH_bins / 2.0 - 0.5, ymax_abs ** 0.6, text = "V = W", doNDC = False, alignment = 22, fontsize = 0.07, font = 62)
        STXSPlotter._drawText(number_WH_bins + number_ZH_bins / 2.0 - 0.5, ymax_abs ** 0.6, text = "V = Z", doNDC = False, alignment = 22, fontsize = 0.07, font = 62)
    
        STXSPlotter._drawText(0.45, 0.88, legend_header, doNDC = True, font = 62)

        # prepare some copies of the plots to be able to tune their appearance in the legend
        objs_abs["theory_hist_leg"] = objs_abs["theory_hist"].Clone()
        objs_abs["theory_hist_leg"].SetLineWidth(4)
        objs_abs["data_graph_leg"] = objs_abs["data_graph"].Clone()
        objs_abs["data_graph_leg"].SetLineWidth(4)
        objs_abs["data_statonly_graph_leg"] = objs_abs["data_statonly_graph"].Clone()
        objs_abs["data_statonly_graph_leg"].SetLineWidth(4)

        leg = ROOT.TLegend(0.45, 0.68, 0.87, 0.85)
        ROOT.SetOwnership(leg, False)
        leg.SetTextFont(42)
        leg.SetBorderSize(1)
        leg.SetTextSize(0.05)
        leg.SetLineColor(0)
        leg.SetLineStyle(1)
        leg.SetLineWidth(1)
        leg.SetFillColor(0)
        leg.SetFillStyle(1)
        leg.SetNColumns(3)
        leg.AddEntry(objs_abs["data_graph_leg"], "Observed ", "p")
        leg.AddEntry(objs_abs["data_graph_leg"], "Tot. unc.", "l")
        leg.AddEntry(objs_abs["data_statonly_graph_leg"], "Stat. unc.", "l")
        leg.AddEntry(objs_abs["theory_hist_leg"], "Expected ", "l")
        leg.AddEntry(objs_abs["theory_unc_hist"], "Theo. unc.", "f")
        leg.Draw()

        # switch ticks on on both sides
        pad_abs.cd()
        ROOT.gPad.SetTicky()

        pad_rel.cd()
        ROOT.gPad.SetTicky()

        # # manually draw small ticks to separate different STXS bins
        # pad_abs.cd()
        # for cur_bin in range(number_bins - 1):
        #     STXSPlotter._drawLine(cur_bin + 0.5, ymin_abs, cur_bin + 0.5, ymin_abs ** 1.2, width = 1, color = ROOT.kBlack, style = 1)

        # pad_rel.cd()
        # for cur_bin in range(number_bins - 1):
        #     STXSPlotter._drawLine(cur_bin + 0.5, ymin_rel, cur_bin + 0.5, ymin_rel + 0.2, width = 1, color = ROOT.kBlack, style = 1)
        #     STXSPlotter._drawLine(cur_bin + 0.5, ymax_rel, cur_bin + 0.5, ymax_rel - 0.2, width = 1, color = ROOT.kBlack, style = 1)

        # draw thin lines in the ratio pane at 0 and 2
        pad_rel.cd()
        STXSPlotter._drawLine(xstart = -0.5, ystart = 0.0, xend = number_bins - 0.5, yend = 0.0, color = ROOT.kGray)
        STXSPlotter._drawLine(xstart = -0.5, ystart = 2.0, xend = number_bins - 0.5, yend = 2.0, color = ROOT.kGray)
        
        # redraw the bounding box to make sure it is on top of everything
        pad_abs.cd()
        base_abs.Draw("axis same")
        pad_rel.cd()
        base_rel.Draw("axis same")        
        
        canv.SaveAs(outfile)

    @staticmethod
    def plot_mu(plotdata, outfile, xlabel = "", ylabel = "", inner_label = ""):
        """
        Generate nice plot of the STXS signal strenghts, separately for WH and ZH.

        Arguments:
            plotdata ... dictionary containing the information that is to be plotted, with the following
                         format: {'central_values': [...], 'stat_uncs_hi': [...], 'stat_uncs_lo': [...],
                                  'total_uncs_lo': [...], 'total_uncs_hi': [...], 'theory_central_values': [...],
                                  'theory_uncs': [...], 'labels': [...]}
            xlabel / ylabel ... axies labels
            inner_label ... description showing up in the interior of the plot
            outfile ... full path to the output file (including filename extension)
        """

        plotconf = Config(options = [])

        ROOT.gStyle.SetOptStat(0)

        # have the following fields in 'plotdata':
        # central_values, stat_uncs_hi, stat_uncs_lo, total_uncs_hi, total_uncs_lo, theory_central_values, theory_uncs, labels
        number_mus = len(plotdata['central_values'])

        xmax = 8
        xmin = -0.999

        canv = ROOT.TCanvas("canv", "canv", 1400, 800)
        ROOT.SetOwnership(canv, False)

        ROOT.gPad.SetTopMargin(0.02)
        ROOT.gPad.SetLeftMargin(0.27)
        ROOT.gPad.SetBottomMargin(0.10)
        ROOT.gPad.SetRightMargin(0.05)
        
        # make the base object
        number_bins = int(number_mus * 1.35) # allow for some extra space to fit the header labels etc.
        base = ROOT.TH2D("base", "", 20, xmin, xmax, number_bins, -0.5, number_bins - 0.5)
        ROOT.SetOwnership(base, False)
        base.GetXaxis().SetTitle(xlabel)
        base.GetYaxis().SetTitle(ylabel)
        base.GetXaxis().SetTitleSize(0.04)
        base.GetXaxis().SetLabelSize(0.04)
        base.GetYaxis().SetTitleSize(0.05)
        base.GetYaxis().SetLabelSize(0.05)
        base.GetYaxis().SetTickSize(0)
        base.GetYaxis().SetTickLength(0)

        # set labels
        for ind, cur_label in enumerate(plotdata['labels']):
            base.GetYaxis().SetBinLabel(ind + 1, cur_label)

        ROOT.gPad.SetTickx()
        canv.cd()
        base.Draw()

        # draw the theory data
        unc_x_lo = array('d', plotdata['theory_uncs'])
        unc_x_hi = array('d', plotdata['theory_uncs'])

        no_unc = array('d', [0 for cur in range(number_mus)])

        unc_y_lo = array('d', [0.5 for cur in range(number_mus)])
        unc_y_hi = array('d', [0.5 for cur in range(number_mus)])

        data_y = array('d', list(range(number_mus)))
        data_x = array('d', plotdata['theory_central_values'])

        theory_uncs = ROOT.TGraphAsymmErrors(number_mus, data_x, data_y, unc_x_lo, unc_x_hi, unc_y_lo, unc_y_hi)
        ROOT.SetOwnership(theory_uncs, False)
        theory_uncs.SetLineWidth(0)
        theory_uncs.SetFillColor(ROOT.kGray)
        theory_uncs.Draw("same 2")

        theory = ROOT.TGraphAsymmErrors(number_mus, data_x, data_y, no_unc, no_unc, unc_y_lo, unc_y_hi)
        ROOT.SetOwnership(theory, False)
        theory.SetLineWidth(3)
        theory.SetMarkerColor(1)
        theory.SetMarkerStyle(0)
        theory.SetMarkerSize(0)
        theory.Draw("same Z")

        # draw the data
        unc_x_lo = array('d', plotdata['total_uncs_lo'])
        unc_x_hi = array('d', plotdata['total_uncs_hi'])

        statunc_x_lo = array('d', plotdata['stat_uncs_lo'])
        statunc_x_hi = array('d', plotdata['stat_uncs_hi'])

        data_y = array('d', list(range(number_mus)))
        data_x = array('d', plotdata['central_values'])

        data = ROOT.TGraphAsymmErrors(number_mus, data_x, data_y, unc_x_lo, unc_x_hi, no_unc, no_unc)
        ROOT.SetOwnership(data, False)
        data.SetLineWidth(4)
        data.SetMarkerColor(1)
        data.SetMarkerStyle(20)
        data.SetMarkerSize(1.6)

        data_statonly = ROOT.TGraphAsymmErrors(number_mus, data_x, data_y, statunc_x_lo, statunc_x_hi, no_unc, no_unc)
        ROOT.SetOwnership(data_statonly, False)
        data_statonly.SetLineWidth(3)
        data_statonly.SetMarkerColor(1)
        data_statonly.SetMarkerStyle(20)
        data_statonly.SetMarkerSize(1.6)
        data_statonly.SetLineColor(8)

        ROOT.gStyle.SetEndErrorSize(7.0)
        data.Draw("same p")
        data_statonly.Draw("same p")
        
        # draw labels and legend
        STXSPlotter._drawATLASLabel(0.28, 0.93, plotconf.ATLAS_suffix, doNDC = True, fontsize = 0.042)
        STXSPlotter._drawText(0.93, 0.92, inner_label, fontsize = 0.042, alignment = 32)

        STXSPlotter._drawLine(0.0, -0.5, 0.0, number_mus - 0.5, width = 2, style = 7, color = ROOT.kGray)

        leg = ROOT.TLegend(0.28, 0.84, 0.93, 0.89)
        ROOT.SetOwnership(leg, False)
        leg.SetTextFont(42)
        leg.SetTextSize(0.041)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.SetNColumns(4)
        leg.AddEntry(data, "Obs.", "p")
        leg.AddEntry(data, "Tot. unc.", "l")
        leg.AddEntry(data_statonly, "Stat. unc.", "l")
        #leg.AddEntry(theory, "Expected", "l")
        leg.AddEntry(theory_uncs, "Theo. unc.", "f")
        leg.Draw()

        xlabels_start = xmin + (xmax - xmin) * 0.46
        STXSPlotter._drawText(xlabels_start - 0.1, number_mus - 0.4, "            Tot.", font = 62, fontsize = 0.04, doNDC = False, alignment = 10)
        STXSPlotter._drawText(xlabels_start + 0.5 , number_mus - 0.4, "                        ( Stat.,  Syst. )", font = 42, fontsize = 0.038, doNDC = False, alignment = 10)

        for ind, (cur_central_value, cur_total_unc_hi, cur_total_unc_lo, cur_stat_unc_hi, cur_stat_unc_lo) in enumerate(zip(plotdata['central_values'], plotdata['total_uncs_hi'], plotdata['total_uncs_lo'], plotdata['stat_uncs_hi'], plotdata['stat_uncs_lo'])):
            
            cur_syst_unc_hi = m.sqrt(cur_total_unc_hi ** 2 - cur_stat_unc_hi ** 2)
            cur_syst_unc_lo = m.sqrt(cur_total_unc_lo ** 2 - cur_stat_unc_lo ** 2)

            STXSPlotter._drawText(xlabels_start, ind, f"{cur_central_value:.2f}  {{}}^{{#bf{{#plus}}{cur_total_unc_hi:.2f}}}_{{#bf{{#minus}}{cur_total_unc_lo:.2f}}}", font = 62, fontsize = 0.038, doNDC = False, alignment = 12)
            STXSPlotter._drawText(xlabels_start + (xmax - xmin) * 0.25, ind, f"  {{}}^{{#bf{{#plus}}{cur_stat_unc_hi:.2f}}}_{{#bf{{#minus}}{cur_stat_unc_lo:.2f}}}", font = 42, fontsize = 0.040, doNDC = False, alignment = 12)
            STXSPlotter._drawText(xlabels_start + (xmax - xmin) * 0.25, ind, f"            {{}}^{{#bf{{#plus}}{cur_syst_unc_hi:.2f}}}_{{#bf{{#minus}}{cur_syst_unc_lo:.2f}}}", font = 42, fontsize = 0.040, doNDC = False, alignment = 12)
            STXSPlotter._drawText(xlabels_start + (xmax - xmin) * 0.25, ind, "(            )", font = 42, fontsize = 0.055, doNDC = False, alignment = 12)
            STXSPlotter._drawText(xlabels_start + (xmax - xmin) * 0.25, ind - 0.02, "         ,", font = 42, fontsize = 0.045, doNDC = False, alignment = 13)

        base.Draw("axis same")

        canv.SaveAs(outfile)

    # some private helper functions
    @staticmethod
    def _drawText(x, y, text, color = ROOT.kBlack, fontsize = 0.05, font = 42, doNDC = True, alignment = 12):
        """
        Put a TLatex at a certain position.
        """
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
        """
        Draw a nice ATLAS label.
        """
        STXSPlotter._drawText(x, y, "ATLAS", fontsize = fontsize, font = 72, doNDC = doNDC)
        STXSPlotter._drawText(x + 0.12, y, text, fontsize = fontsize, font = 42, doNDC = doNDC)

    @staticmethod
    def _drawLine(xstart, ystart, xend, yend, width = 2, style = 7, color = ROOT.kBlack):
        """
        Draw a nice line.
        """
        line = ROOT.TLine(xstart, ystart, xend, yend)
        ROOT.SetOwnership(line, False)
        line.SetLineColor(color)
        line.SetLineWidth(width)
        line.SetLineStyle(style)
        line.Draw()

    @staticmethod
    def _subplot_STXS_xsec(obs_values, total_unc_lo, total_unc_hi, stat_unc_lo, stat_unc_hi, theory_values, theory_unc, pad, name = "abs"):
        """
        This function is called by plot_STXS_xsec and takes care of populating a single pane (either the absolute or relative one) of the plot.
        """
        pad.cd()
        number_bins = len(obs_values)
        
        # prepare the histograms for the MC prediction and -uncertainty
        theory_pred = ROOT.TH1F(f"theory_pred_{name}", f"theory_pred_{name}", number_bins, -0.5, number_bins - 0.5)
        ROOT.SetOwnership(theory_pred, False)
        theory_pred.SetMarkerSize(0.0)
        theory_pred.SetLineColor(2)
        theory_pred.SetLineWidth(2)

        theory_pred_unc = ROOT.TH1F(f"theory_pred_unc_{name}", f"theory_pred_unc_{name}", number_bins, -0.5, number_bins - 0.5)
        ROOT.SetOwnership(theory_pred_unc, False)
        theory_pred_unc.SetMarkerSize(0)
        theory_pred_unc.SetFillStyle(1001)
        theory_pred_unc.SetFillColor(ROOT.kRed - 9)
        theory_pred_unc.SetLineColor(2)
        theory_pred_unc.SetLineWidth(1)
        
        for ind, (cur_theory_pred, cur_theory_pred_unc) in enumerate(zip(theory_values, theory_unc)):
            cur_bin = ind + 1
            theory_pred.SetBinContent(cur_bin, cur_theory_pred)
            theory_pred.SetBinError(cur_bin, 1e-6)

            theory_pred_unc.SetBinContent(cur_bin, cur_theory_pred)
            theory_pred_unc.SetBinError(cur_bin, cur_theory_pred_unc)

        theory_pred_unc.Draw("SAMEE2")
        theory_pred.Draw("SAMEE")

        # prepare the graphs for the measurements and their total and statistical uncertainties
        unc_x_lo = array('d', [0 for cur in range(number_bins)])
        unc_x_hi = array('d', [0 for cur in range(number_bins)])        

        unc_y_lo = array('d', total_unc_lo)
        unc_y_hi = array('d', total_unc_hi)

        statunc_y_lo = array('d', stat_unc_lo)
        statunc_y_hi = array('d', stat_unc_hi)

        data_y = array('d', obs_values)
        data_x = array('d', list(range(number_bins)))

        ROOT.gStyle.SetEndErrorSize(10)
        data = ROOT.TGraphAsymmErrors(number_bins, data_x, data_y, unc_x_lo, unc_x_hi, unc_y_lo, unc_y_hi)
        ROOT.SetOwnership(data, False)
        data.SetMarkerColor(1)
        data.SetMarkerStyle(20)
        data.SetMarkerSize(1.2)
        data.SetLineWidth(3)
        data.Draw("P")

        data_statonly = ROOT.TGraphAsymmErrors(number_bins, data_x, data_y, unc_x_lo, unc_x_hi, statunc_y_lo, statunc_y_hi)
        ROOT.SetOwnership(data_statonly, False)
        data_statonly.SetMarkerColor(1)
        data_statonly.SetMarkerStyle(20)
        data_statonly.SetMarkerSize(1.1)
        data_statonly.SetLineWidth(2)
        data_statonly.SetLineColor(8)
        data_statonly.Draw("P")
        
        # return a dict with the created objects in case they are needed
        retdict = {"theory_hist": theory_pred, "theory_unc_hist": theory_pred_unc, "data_graph": data, "data_statonly_graph": data_statonly}
        return retdict