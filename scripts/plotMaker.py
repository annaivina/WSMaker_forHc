#!/usr/bin/env python

# TODO Treat automatically 2011/2012. Partially done
# TODO: put ifs to handle h as both TGraph and TH1 gracefully

# README
# configuration of samples, colors, etc... at the bottom of this file, in Config
# there is possibility to merge samples in one color/block in the plots: see stop(Wt/st) case
# signal can be stacked or overprinted as a line
# customisation of title of X axis: see get_xTitle()


import os
import array
import math
import bisect
import logging
import re
import random

import ROOT

class Setup:
    """ A class that contains data, signal MC, background MC..., and that knows how to plot them """
    def __init__(self, cfg, title="", guess_properties=True):
        self.cfg = cfg
        self.data = 0
        self.fiterr = 0
        self.prefit = 0
        self.bkgs = []
        self.sig = 0
        self.sig_to_use = None
        self.add_sig = 0
        self.determine_weighted(title)
        self.title = title
        for wtag in cfg.weight_tags:
            if wtag in title.rsplit('_', 1)[-1]:
                self.title = title.rsplit('_', 1)[0]
                break
        self.isBkgSub = False
        self.chi2 = -1
        self.initialized = False
        ROOT.TGaxis.SetMaxDigits(4)
        if guess_properties:
            self.properties = getPropertiesFromTag(cfg, self.title)
        else:
            self.properties = None

    def determine_weighted(self, title):
        cfg = self.cfg
        cfg._weighted = ""
        for wtag in cfg.weight_tags:
            if wtag in title:
                if "weighted" in wtag:
                    cfg._weighted = wtag.replace('weighted', '')
                else:
                    cfg._weighted = wtag

    def append_bkg(self, bkg):
        is_merged = False
        for name in bkg.mergelist:
            for b in self.bkgs:
                if b.name == name:
                    b.append(bkg)
                    is_merged = True
                    break
        if not is_merged:
            self.bkgs.append(bkg)

    def init_finished(func):
        """ to be used as a decorator:

        Ensures that backgrounds are sorted
        Ensures that sum of backgrounds is available
        Ensures that stack of backgrounds is available
        Blind data and creates a data TH1 from the data TGraphAsymmErrors
        Scales the signal by the desired amount
        """
        def f(self, *args, **kwargs):
            if not self.initialized:
                self.finish_initialize()
            return func(self, *args, **kwargs)
        return f

    def finish_initialize(self):
        cfg = self.cfg
        if not self.initialized:
            if not cfg.isSoBplot:
                self.bkgs.sort()
            else:
                self.bkgs.sort(reverse=True)
                index_ttbar=0
                index_stop=0
                for i in range(0,len(self.bkgs)):
                    if "ttbar" in self.bkgs[i].h.GetName():
                        index_ttbar = i
                    elif "stop" in self.bkgs[i].h.GetName():
                        index_stop = i
                if index_ttbar and index_stop:
                    self.bkgs[index_ttbar], self.bkgs[index_stop] = self.bkgs[index_stop], self.bkgs[index_ttbar]

            if len(self.bkgs) != 0:
                self.hsum = clone(self.bkgs[0].h)
                self.hsum.Reset()
                self.stack= ROOT.THStack("stack","stack")
                for bkg in self.bkgs:
                    self.hsum.Add(bkg.h)
                    self.stack.Add(bkg.h)
            if cfg.use_exp_sig and not (self.sig == 0): self.sig_to_use = self.sig.make_expected_signal()
            elif not (self.sig == 0): self.sig_to_use = self.sig
            logging.debug(f"is signal present = {not (self.sig == 0)}")
            logging.debug(f"is signal-to-use present = {self.sig_to_use is not None}")

            logging.debug(f"plot_with_additional_signal = {self.plot_with_additional_signal()}")
            if self.plot_with_additional_signal():
                if "VHbbRun2" in os.getenv("ANALYSISTYPE") or "VHccRun2" in os.getenv("ANALYSISTYPE") or "VHqqRun2" in os.getenv("ANALYSISTYPE") or "SemileptonicVBS" in os.getenv("ANALYSISTYPE"):
                    self.add_sig = self.sig.make_additional_signal(self.hsum.Integral(), self.properties["dist"], self.properties)
                else:
                    self.add_sig = self.sig.make_additional_signal(self.hsum.Integral(), self.properties["dist"], self.properties["L"])
            if cfg.generate_pseudodata:
                self.randomize_data()

            self.data.clean()
            if cfg.blind:
                self.blind_data()
            self.data.make_data_hist(self.hsum)
            if self.sig_to_use is not None:
                self.sig_to_use.scale()
                if "#mu" not in self.sig_to_use.title and not "AZh" in os.getenv("ANALYSISTYPE"):
                    if "boostedVHbbRun2" in os.getenv("ANALYSISTYPE"):
                        self.sig_to_use.title += f" (#mu_{{VH}}={self.sig_to_use.muhat:.2f})"
                    else:
                        self.sig_to_use.title += f" (#mu={self.sig_to_use.muhat:.2f})"
            self.initialized = True

    def blind_data(self):
        """ Blind data according to the configuration """
        self.cfg.blind_data(self)


    def randomize_data(self):
        """ Randomize data to make fancy PR plots """

        tmpsumSB = clone(self.hsum)
        tmpsumSB.Add(self.sig_to_use.h)
        self.data.randomize(tmpsumSB)


    def find_bkg(self, name):
        """ Returns a background of the given name """
        for b in self.bkgs:
            if b.name == name:
                return b
        return None

    @init_finished
    def find_maximum(self, log_scale):
        """ Find maximum of data(+error bar) and MC """
        # JWH stuff
        h1 = self.data.hist
        tobjarray = self.stack.GetStack()
        max_histo_range = None

        max_data_range = h1.GetBinContent(h1.GetMaximumBin()) + h1.GetBinError(h1.GetMaximumBin())
        for h in tobjarray:
            if not isinstance(h, ROOT.TH1): continue
            if max_histo_range is None:
                # max_histo_range = h.GetBinContent(h.GetMaximumBin()) + h.GetBinError(h.GetMaximumBin())
                max_histo_range = h.GetBinContent(h.GetMaximumBin())
            else:
                # max_histo_range = max(max_histo_range, h.GetBinContent(h.GetMaximumBin()) + h.GetBinError(h.GetMaximumBin()))
                max_histo_range = max(max_histo_range, h.GetBinContent(h.GetMaximumBin()))
        max_histo_range = max(max_histo_range, max_data_range)

        if log_scale and max_histo_range <= 0:
            max_histo_range = 1e-2

        logging.debug(f"found content maximum of {max_histo_range}")
        return max_histo_range

        # h1 = self.data.hist
        # tobjarray = self.stack.GetStack()
        # h2 = tobjarray.Last()
        # maximum = max(h1.GetBinContent(h1.GetMaximumBin())+h1.GetBinError(h1.GetMaximumBin()), h2.GetBinContent(h2.GetMaximumBin()))
        # print "found maximum of", maximum
        # return maximum

    @init_finished
    def find_minimum(self, log_scale,use_data_only_for_bounds=False):
        """ Find minimum of data(-error bar) and MC
        Function is a bit complicated so that empty bins are not taken into account
        and log plots are not spoiled
        """
        # JWH stuff
        h1 = self.data.hist
        tobjarray = self.stack.GetStack()
        min_histo_range = None
        min_histo_range_total = 1.0

        if not log_scale:
            min_data_range = h1.GetBinContent(h1.GetMinimumBin()) - h1.GetBinError(h1.GetMinimumBin())
            for h in tobjarray:
                if not isinstance(h, ROOT.TH1): continue
                if min_histo_range is None:
                    # min_histo_range = h.GetBinContent(h.GetMinimumBin())
                    min_histo_range = h.GetBinContent(h.GetMinimumBin()) - h.GetBinError(h.GetMinimumBin())
                else:
                    # min_histo_range = min(min_histo_range, h.GetBinContent(h.GetMinimumBin()))
                    min_histo_range = min(min_histo_range, h.GetBinContent(h.GetMinimumBin()) - h.GetBinError(h.GetMinimumBin()))
            min_histo_range = min(min_histo_range, min_data_range)
        else:
            min_data_range = h1.GetBinContent(h1.GetMinimumBin()) - h1.GetBinError(h1.GetMinimumBin())
            if min_data_range <= 0:
                min_data_range = h1.GetBinContent(h1.GetMinimumBin())
                if min_data_range <= 0:
                    min_data_range = 0
            for h in tobjarray:
                if not isinstance(h, ROOT.TH1): continue
                temp = h.GetBinContent(h.GetMinimumBin())
                # temp = h.GetBinContent(h.GetMinimumBin()) - h.GetBinError(h.GetMinimumBin())
                if temp <= 0:
                    temp = h.GetBinContent(h.GetMinimumBin())
                    if temp <= 0:
                        temp = 0
                if min_histo_range is None:
                    min_histo_range = temp
                elif not temp == 0 and not min_histo_range == 0:
                    min_histo_range = min(min_histo_range, temp)
                elif not temp == 0 and min_histo_range == 0:
                    min_histo_range = temp
            if min_histo_range == 0:
                min_histo_range = min_data_range
                if min_histo_range == 0:
                    min_histo_range = 1e-1
            if not min_histo_range == 0 and not min_data_range == 0:
                min_histo_range = min(min_histo_range, min_data_range)

            # use minimum of the total bkg rather than the minumum of each process
            min_histo_range_total = self.stack.GetMinimum()
            if min_histo_range_total <=0:
                min_histo_range_total = 0
            if min_histo_range_total == 0:
                min_histo_range_total = min_data_range
                if min_histo_range_total == 0:
                    min_histo_range_total = 1e-1
            if not min_histo_range_total == 0 and not min_data_range == 0:
                min_histo_range_total = min(min_histo_range_total, min_data_range)

        logging.debug(f"found content minimum of {min_histo_range}")
        logging.debug(f"found total content minimum of {min_histo_range_total}")
        if use_data_only_for_bounds:
            return min_data_range,min_histo_range_total
        return min_histo_range,min_histo_range_total

        # h1 = self.data.hist
        # tobjarray = self.stack.GetStack()
        # h2 = tobjarray.Last()
        # min_data = h1.GetBinContent(h1.GetMinimumBin())
        # if min_data != 0:
        #     min_data -= h1.GetBinError(h1.GetMinimumBin())
        # min_MC = h2.GetBinContent(h2.GetMinimumBin())
        # mini = min(min_data, min_MC)
        # if mini == 0:
        #     print "found minimum of 0"
        #     newmin = min(h1.GetMinimum(1.e-5), h2.GetMinimum(1.e-5))
        #     print "next to minimum is found at", newmin
        #     return newmin
        # else:
        #     print "found minimum of ", mini
        # return mini

    def make_complete_plot(self, can_name = "", do_ratio = False, logy = False, ytitle = "Events", ybounds=(0.5, 1.5), draw_difference = False):
        """ Main function to create plots.

        Divide canvas if needed, call functions to fill the pads, and call functions
        to print all the stuff (legend, titles, labels...)
        """
        if can_name:
            cname = can_name
        else:
            cname = "can"
        print( cname)
        logging.info(f'plotting {cname}')
        tc = ROOT.TCanvas(cname, cname, 600, 600)
        if draw_difference : tc = ROOT.TCanvas(cname, cname, 600, 800)
        if do_ratio:
            up, do = divide_canvas(tc, 0.25)
            if draw_difference : up, do = divide_canvas(tc, 0.40)
            up.cd()
            self.smallFontSize = 0.04
            self.legFontSize = 0.03
            self.normalFontSize = 0.05
        else:
            ROOT.gPad.SetLeftMargin(0.13)
            ROOT.gPad.SetRightMargin(0.075)
            self.smallFontSize = 0.03
            self.legFontSize = 0.025
            self.normalFontSize = 0.0375
        xbounds = self.cfg.get_xbound_from_properties(self.properties)
        # TODO: JWH
        # leg_pos = self.cfg.get_legend_pos_from_properties(self.properties)
        # if leg_pos is None: # default
        #     leg_pos = [0.62, 0.42, 0.865, 0.925]
        # leg = self.build_legend(leg_pos)
        # self.draw_everything(do_ratio, leg.GetNRows(), logy, ytitle, xbounds=xbounds)
        do_dat_only_limits = ('MET' in can_name or 'pTV' in can_name) and logy
        hist = self.draw_everything(do_ratio, logy, ytitle, xbounds=xbounds,use_data_only_for_bounds=do_dat_only_limits)
        logx = False
        if logy:
            ROOT.gPad.SetLogy()
            if "AZh" in os.getenv("ANALYSISTYPE") and self.properties["dist"]=="mVH":
                ROOT.gPad.SetLogx()
                logx = True
        if do_ratio:
            do.cd()
            if draw_difference :
                self.draw_dataMC_difference(cname)
                ROOT.gPad.SetBottomMargin(0.25)
            else : self.draw_dataMC_ratio(True, ybounds, xbounds=xbounds, xtitle="", logx=logx)
            up.cd()
        leg_pos = self.cfg.get_legend_pos_from_properties(self.properties)
        if leg_pos is None: # default
            leg_pos = [0.62, 0.42, 0.865, 0.925]
        leg = self.build_legend(leg_pos, logy)
        draw(leg)
        if do_ratio:
            ref_up = 0.87
        else:
            ref_up = 0.90
        xref = 0.17
        self.draw_ATLAS_label((xref, ref_up))
        self.draw_lumi((xref, ref_up - self.normalFontSize - 0.01))
        height = self.cfg.get_title_height()
        self.draw_title((xref, ref_up - height*self.normalFontSize - 0.01))
        logging.debug("RETURNING from make_complete_plot")
        return tc

    @init_finished
    def make_bkg_substr_plot(self, can_name = ""):
        """ Function to create background-subtracted plots.

        Subtract backgrounds from everything, and pass the resulting objects
        to make_complete_plot()
        """
        bkgsum = clone(self.hsum)
        binwidth = self.hsum.GetBinWidth(3)
        binCheck = self.hsum.GetBinWidth(1)
        for iB in range(2,self.hsum.GetNbinsX()+1):
            if binCheck != self.hsum.GetBinWidth(iB):
                logging.debug(f"Found 2 different bin-width: (bin 1, width {binCheck:.2f}) and (bin {iB:.0f} width {self.hsum.GetBinWidth(iB):.2f})")
                binwidth = -1
                break

        model = clone(self.hsum)
        model.Reset()
        #diboson = Bkg(model, "Diboson")
        diboson = Bkg(self.cfg, model, self.cfg.bkg_substr_name, self.properties)
        # for sample in ["diboson", "Diboson", "WZ", "ZZ", "VZ"]:
        for sample in self.cfg.bkg_substr_list:
            res = self.find_bkg(sample)
            if res:
                bkgsum.Add(res.h, -1)
                diboson.h.Add(res.h)

        setup_tmp = Setup(self.cfg,self.title,True)
        setup_tmp.determine_weighted(can_name)
        setup_tmp.isBkgSub = True
        setup_tmp.data = self.data.subtract(bkgsum)
        setup_tmp.append_bkg(diboson)
        setup_tmp.sig = self.sig
        # setup_tmp.exp_sig = self.exp_sig
        setup_tmp.sig_to_use = self.sig_to_use
        if self.fiterr:
            setup_tmp.fiterr = self.fiterr.center_at_0()
        setup_tmp.chi2 = self.chi2
        if self.cfg._weighted:
            if binwidth>0: return setup_tmp.make_complete_plot(can_name, ytitle=f"Events / {binwidth:.0f} GeV (Weighted, B-subtracted)")
            else: return setup_tmp.make_complete_plot(can_name, ytitle="Events / GeV (Weighted, B-subtracted)")
#            return setup_tmp.make_complete_plot(can_name, ytitle="Weighted events after subtraction")
        else:
            return setup_tmp.make_complete_plot(can_name, ytitle="Events after B-subtraction")

    # not sure all the draw functions should be there

    @init_finished
    def draw_everything(self, plot_ratio = False, logy = False, ytitle = "Events", xtitle="", xbounds = None,use_data_only_for_bounds=False):
        """ Function in charge of plotting histos on the upper pad

            Take care of the nightmarish Y axis ranges
        """
        cfg = self.cfg
        the_min,the_min_total = self.find_minimum(logy,use_data_only_for_bounds)
        the_max = self.find_maximum(logy)
        # avoid to have stack and legend overlapping
        # no_trafo = not cfg.is_transformed(self.properties, self.data.hist)
        if self.properties:
            the_max *= cfg.get_yscale_factor_from_properties(self.properties, logy)

        # this legend is only used to get the y range correct
        if "AZh" in os.getenv("ANALYSISTYPE"):
            leg_pos = [0.62, 0.48, 0.84, 0.88] # init
        else:
            leg_pos = [0.58, 0.48, 0.80, 0.88]
        leg = self.build_legend(leg_pos, logy)
        if self.sig_to_use is not None and self.sig_to_use.mode == self.cfg._OVERPRINT:
            logging.debug("DRAWING UNSTACKED")
            hist = self.draw_bkg(True)
            cfg.set_y_range(hist, leg.GetNRows(), the_min, the_min_total, the_max, logy, self.properties)
            self.draw_sig(False)
            # if not self.exp_sig:
            #     self.draw_sig(False)
            # else:
            #     self.draw_sig(False, is_expected=True)
        elif self.sig_to_use is not None:
            logging.debug("DRAWING STACKED")
            additional_possible = self.plot_with_additional_signal()
            hist = self.draw_bkg_plus_sig(True,is_expected=False, is_additional=False)
            #hist = self.draw_bkg_plus_sig(True)
            if (self.properties["dist"]=="NAdditionalCaloJets"):
                hist.GetXaxis().SetNdivisions(107)
            elif (self.properties["dist"]=="Naddbtrackjets"):
                hist.GetXaxis().SetNdivisions(103)
            cfg.set_y_range(hist, leg.GetNRows(), the_min, the_min_total, the_max, logy, self.properties)
            # if not self.exp_sig:
            #     hist = self.draw_bkg_plus_sig(True)
            # else:
            #     hist = self.draw_bkg_plus_sig(True, is_expected=True)
                #if self.sig.muhat < 1:  # Change order of plotting whether muhat <> 1
                    #hist = self.draw_bkg_plus_sig(True, is_expected=True)
                    #self.draw_bkg_plus_sig(False, is_expected=False)
                #else:
                    #hist = self.draw_bkg_plus_sig(True, is_expected=False)
                    #self.draw_bkg_plus_sig(False, is_expected=True)
        else:
            logging.debug("DRAWING BKG ONLY - NO SIGNAL PRESENT")
            hist = self.draw_bkg(True, draw_ylabels=True)
            cfg.set_y_range(hist, leg.GetNRows(), the_min, the_min_total, the_max, logy, self.properties)

        hist.SetMinimum(hist.GetHistogram().GetYaxis().GetXmin())
        hist.SetMaximum(hist.GetHistogram().GetYaxis().GetXmax())

        if plot_ratio: # tricks to draw pretty ratio plots
            hist.GetYaxis().SetLabelSize(0.05)
            hist.GetYaxis().SetTitleSize(0.05)
            hist.GetYaxis().SetTitleOffset(1.3)
            hist.GetXaxis().SetLabelOffset(0.15) # nudge axis labels behind ratio plots
            if hist.GetMaximum() > 0 and hist.GetMinimum() / hist.GetMaximum() < 0.25 and not logy:
                hist.SetMinimum(hist.GetMaximum() / 1000000)
            hist.Draw("hist")
            if self.sig_to_use is not None and self.sig_to_use.mode != self.cfg._OVERPRINT:
                if additional_possible:
                    self.draw_sig(False)

        else:
            hist.GetYaxis().SetTitleOffset(1.3)


        if self.fiterr:
            self.draw_FitErr(False)
        #else:
            #self.draw_MCstat(False)

        if self.prefit and cfg.plot_prefit_curve:
            self.draw_PreFit(False)
        self.draw_data(False)

        if xtitle:
            hist.GetXaxis().SetTitle(xtitle)
        else:
            hist.GetXaxis().SetTitle(cfg.get_xTitle(self.properties, self.data.hist))

        if "bin" in ytitle or "GeV" in ytitle: extra_str = ""
        else: extra_str = cfg.get_yTitle_tag(self.properties, self.data.hist)

        if (not (self.properties["dist"]=="Naddbtrackjets" or self.properties["dist"]=="NAdditionalCaloJets")):
            ytitle += extra_str
        if "AZh" in os.getenv("ANALYSISTYPE"):
            if self.cfg.do_rebinning(self.properties) and self.properties["dist"]=="mVH": ytitle = extra_str
        hist.GetYaxis().SetTitle(ytitle)
        logging.debug(f"y-axis label = {ytitle}")

        if xbounds:
            hist.GetXaxis().SetRangeUser(xbounds[0], xbounds[1])

        if self.properties is not None:
            hist = cfg.postprocess_main_content_histogram(self.properties, hist)

        # hist.GetHistogram().GetYaxis().SetRangeUser(hist.GetHistogram().GetYaxis().GetXmin(), hist.GetHistogram().GetYaxis().GetXmax())
        # NOTE: ~worked
        # hist.SetMinimum(hist.GetHistogram().GetYaxis().GetXmin())
        # hist.SetMaximum(hist.GetHistogram().GetYaxis().GetXmax())
        return hist

    @init_finished
    def make_SoB_plot(self, can_name = "",do_ratio = True, Ratioybounds=(0.4, 1.6), ratioType = 0):
        """ Main function to create S/B plot
        """
        if can_name:
            cname = can_name
        else:
            cname = "can"
        logging.info(f"plotting {cname}")

        tc = ROOT.TCanvas(cname, cname, 600, 600)
        if do_ratio:
            up, do = divide_canvas(tc, 0.25)
            up.cd()
            self.smallFontSize = 0.045
            self.legFontSize = 0.035
            self.normalFontSize = 0.05
        else:
            ROOT.gPad.SetLeftMargin(0.13)
            ROOT.gPad.SetRightMargin(0.075)
            self.smallFontSize = 0.03
            self.legFontSize = 0.025
            self.normalFontSize = 0.0375

        # TODO: JWH
        # leg_pos = self.cfg.get_legend_pos_from_properties(self.properties)
        # if leg_pos is None: # default
        #     leg_pos = [0.62, 0.48, 0.84, 0.88]
        # leg = self.build_legend(leg_pos)
        # first_h = self.draw_everything(True, leg.GetNRows(), True, xtitle = "log_{10}(S/B)")
        # first_h = self.draw_everything(True, True, "Events / bin", xtitle = "log_{10}(S/B)")
        first_h = self.draw_everything(True, True, xtitle = "log_{10}(S/B)", ytitle="Events / 0.5")
        # force y range
        the_max = self.find_maximum(True)
        self.cfg.set_y_range(first_h, 3, 1.0, 1.0, the_max, True, self.properties)
        binwidth = self.hsum.GetBinWidth(3)
        binCheck = self.hsum.GetBinWidth(1)
        for iB in range(2,self.hsum.GetNbinsX()+1):
            if binCheck != self.hsum.GetBinWidth(iB):
                logging.debug(f"Found 2 different bin-width: (bin 1, width {binCheck:.2f}) and (bin {iB:.0f} width {self.hsum.GetBinWidth(iB):.2f})")
                binwidth = -1
                break
        if binwidth>0: first_h.GetHistogram().GetYaxis().SetTitle(f"Events / {binwidth:.2f}")
        else: first_h.GetHistogram().GetYaxis().SetTitle("Events / GeV")
        first_h.SetMinimum(first_h.GetHistogram().GetYaxis().GetXmin())
        first_h.SetMaximum(first_h.GetHistogram().GetYaxis().GetXmax())
        first_h.Draw("sameaxis")
        if not self.sig_to_use is None and do_ratio:
            do.cd()
            self.draw_SoB_ratio(True, Ratioybounds, "log_{10}(S/B)", ratioType=ratioType)
            up.cd()
        ROOT.gPad.SetLogy()

        #leg_pos = [0.62, 0.48, 0.84, 0.88]
        leg_pos = [0.55, 0.48, 0.75, 0.88]
        leg = self.build_legend(leg_pos)
        draw(leg)
        ref_up = 0.85
        xref = 0.17
        self.draw_ATLAS_label((xref, ref_up))
        self.draw_lumi((xref, ref_up - self.normalFontSize - 0.01))
        return tc


    @init_finished
    def draw_data(self, first):
        """ Draw data """
        suff = suffix(first)
        if type(self.data.h) == ROOT.TH1F:
            draw(self.data.h, "e"+suff)
        else:
            if first:
                draw(self.data.h, "pza")
            else:
                draw(self.data.h, "pz")
        return self.data.h

    @init_finished
    def draw_bkg(self, first, draw_ylabels=False):
        """ Draw backgrounds alone """
        suff = suffix(first)
        opt = "ahist" if draw_ylabels else "hist"
        # draw(self.stack, opt+suff)
        # return self.stack
        tempstack = clone(self.stack)
        draw(tempstack, opt+suff)
        return tempstack

    @init_finished
    def draw_sig(self, first):
        """ Draw signal alone

        Signal can be nominal or expected (mu=1)
        """
        is_expected = False
        is_additional = self.plot_with_additional_signal()
        if self.sig_to_use is None: return None
        histo = self.sig_to_use.h
        if is_expected:
            histo = self.exp_sig.h
        elif is_additional:
            histo = self.add_sig.h
        else:
            histo = self.sig.h
        # just a hack for now, what is above seems not to work properly...
        if "AZh" in os.getenv("ANALYSISTYPE"):  histo = self.sig_to_use.h
        suff = suffix(first)
        draw(histo, "hist"+suff)
        return histo

    @init_finished
    def draw_bkg_plus_sig(self, first, is_expected=False, is_additional=False):
        """ Draw signal+backgrounds alone

        Signal can be nominal or expected (mu=1)
        """
        if is_expected:
            histo = self.exp_sig.h
        elif is_additional:
            histo = self.add_sig.h
        else:
            histo = self.sig.h
        if self.sig_to_use is not None: histo = self.sig_to_use.h
        suff = suffix(first)
        tempstack = clone(self.stack)
        if self.sig_to_use is not None: tempstack.Add(histo)
        draw(tempstack, "hist"+suff)
        return tempstack

    @init_finished
    def draw_MCstat(self, first):
        """ Draw MC stat error.

        WARNING: meaningless if called from a RooFit setup, as MC error bars are sqrt(value)
        """
        suff = suffix(first)
        self.hsum.SetFillColor(1)
        self.hsum.SetFillStyle(3004)
        self.hsum.SetMarkerStyle(0)
        draw(self.hsum, "e2"+suff)
        return self.hsum

    @init_finished
    def draw_FitErr(self, first):
        """ Draw Fit Error """
        if first:
            draw(self.fiterr.h, "fa")
        else:
            draw(self.fiterr.h, "f")
        return self.fiterr.h

    def draw_PreFit(self, first):
        """ Draw PreFit line """
        suff = suffix(first)
        draw(self.prefit.h, "hist"+suff)
        return self.prefit.h

    def build_legend(self, coords, logy = False):
        """ Create a legend with all existing stuff in the plot """
        leg = ROOT.TLegend(*coords)
        leg.SetFillColor(-1)
        leg.SetFillStyle(4000)
        leg.SetBorderSize(0)
        everything = [self.data]
        if self.sig_to_use is not None: everything.append(self.sig_to_use)
        sumbkgs = self.hsum.Integral()
        for b in reversed(self.bkgs):
            if (b.h.Integral() > sumbkgs * self.cfg.thresh_drop_legend) or (logy
                and b.h.Integral() > sumbkgs * self.cfg.thresh_drop_legend * self.cfg.thresh_drop_legend) or ("VHccRun2" in os.getenv("ANALYSISTYPE") and "VH125bb" in b.name):
                # drop some process in the legend
                logging.info('show bname')
                logging.info(f"the name is {b.name}")
                if self.properties:
                    prop = self.properties
                    if b.name in self.cfg.dropping_list_in_legend(prop): continue
                everything.append(b)
        if self.fiterr:
            everything.append(self.fiterr)

        if self.prefit and self.cfg.plot_prefit_curve:
            everything.append(self.prefit)
        if self.add_sig:
            everything.append(self.add_sig)
        for ds in everything:
            ds.add_to_legend(leg)
        nobj = len(everything)
        fontSize = min(self.legFontSize, 0.5/nobj)
        #fontSize *= 1.12 # init
        if "AZh" in os.getenv("ANALYSISTYPE"):
            fontSize *= 1.18
        else:
            fontSize *= 1.3
        leg.SetTextSize(fontSize)
        leg.SetY1(leg.GetY2() - 1.3*fontSize*nobj)
        return leg

    @init_finished
    def draw_dataMC_ratio(self, plot_ratio = False, ybounds=(.5, 1.5), xbounds=None, xtitle="", logx = False):
        """ Function to draw the bottom pad, i.e ratios

        Take care of horrendous things like adjusting all fontsizes
        """
        cfg = self.cfg
        htemp = clone(self.data.h)
        xvals  = htemp.GetX()
        yvals  = htemp.GetY()
        yerrup = htemp.GetEYhigh()
        yerrdo = htemp.GetEYlow()
        ymax=-999
        ymin=999
        histprepost_ratio = None

        if self.prefit != 0:
            histprepost_ratio  = clone(self.prefit.h)
            histpostfit = clone(self.hsum)
            histprepost_ratio.Divide(histpostfit)

        # no_trafo = True
        # if self.properties: no_trafo = not cfg.is_transformed(self.properties, self.data.hist)
        force_auto = (self.properties and cfg.auto_compute_ratio_yscale_from_properties(self.properties))
        do_yscale, yscale = cfg.scale_all_yvals(self.properties)

        for i in range(htemp.GetN()):
            b = self.hsum.FindBin(xvals[i])
            sum_val = self.hsum.GetBinContent(b)
            if self.sig_to_use is not None and cfg.add_sig_to_ratio_plot: sum_val += self.sig_to_use.h.GetBinContent(b)
            if sum_val != 0:
                yvals[i] /= sum_val
                yerrup[i] /= sum_val
                yerrdo[i] /= sum_val
            else:
                yvals[i] = 0
                yerrup[i] = 0
                yerrdo[i] = 0
            # for automatic y range
            #tmp_max_criteria = 1 # init
            tmp_max_criteria = 0.4 # new
            if yerrup[i]<tmp_max_criteria or force_auto:
                tmp_err_criteria = yerrup[i]
                if self.properties:
                    #do_yscale, yscale = cfg.scale_all_yvals(self.properties, not no_trafo)
                    if do_yscale: tmp_err_criteria = yvals[i]*yscale
                # if self.properties and self.properties["dist"] == "mva" and no_trafo: tmp_err_criteria = yvals[i]*0.05
                #
                if yvals[i]+tmp_err_criteria-1 > ymax:
                    ymax = yvals[i]+tmp_err_criteria-1
            if yerrdo[i]<tmp_max_criteria or force_auto:
                tmp_err_criteria = yerrdo[i]
                if self.properties:
                    #do_yscale, yscale = cfg.scale_all_yvals(self.properties, not no_trafo)
                    if do_yscale: tmp_err_criteria = yvals[i]*yscale
                # if self.properties and self.properties["dist"] == "mva" and no_trafo: tmp_err_criteria = yvals[i]*0.05
                #
                if yvals[i]-tmp_err_criteria-1 < ymin:
                    ymin = yvals[i]-tmp_err_criteria-1
        tmp_range = max( abs(ymax), abs(ymin) )
        tmp_range*=1.05
        # avoid to go in blank place
        final_range = round(tmp_range,2)
        if (tmp_range*100)>=10. : final_range = round(tmp_range,1) # don't want to see 11% for example

        # round correctly
        bounds = [ 0.01 ]
        bounds += [ 0.05 * i for i in range(1, 20) ]
        bounds += [ 0.5 * i for i in range(2, 11) ]
        idx = bisect.bisect_left(bounds, final_range)
        if idx < len(bounds):
            final_range = bounds[idx]
        # round fix (checked on dPhiLB L1 J2 T2lmt)
        if final_range <= 1 :
            if (final_range*100) % 10 == 0: final_range = round(final_range, 1)
            else : final_range = round(final_range, 2)
        else :
            if (final_range*10) % 10 == 0: final_range = int(final_range)
            else : final_range = round(final_range, 1)
        # to avoid horrible numbers due to bad ndiv
        ndiv=503
        if (final_range*100)%5==0 : ndiv=504
        # avoid overlap with higher canvas
        final_range_extra = 0.002
        if final_range > 0.01 and final_range < 1 : final_range_extra = 0.02
        if final_range >= 1 : final_range_extra = 0.2
        final_range += final_range_extra
        # fix 0.42 and 0.47 problem
        if final_range > 0.4  and final_range < 0.45 : final_range = 0.39
        if final_range > 0.45 and final_range < 0.5  : final_range = 0.52
        # max range = [2, 0] to avoid negative lower boundary
        if final_range > 1. : final_range = 1.

        hdash = clone(self.data.hist)
        hdash.Reset()
        for i in range(hdash.GetNbinsX()+1):
            hdash.SetBinContent(i, 1)
        hdash.SetLineStyle(ROOT.kDashed)
        max_bound = ybounds[1]
        min_bound = ybounds[0]
        if ("VHbbRun2" in os.getenv("ANALYSISTYPE") or "VHqqRun2" in os.getenv("ANALYSISTYPE")) and self.cfg.set_yratio_range:
            props = self.properties
            if (props["D"] == "CRLow" or props["D"] == "CRHigh" ) and not ( props["J"] == "2" and props["BMin"] == "250"):
                max_bound = 1.1
                min_bound = 0.9
            if props["D"] == "SR" and props["BMin"] == "150":
                max_bound = 1.25
                min_bound = 0.75
            if props["D"] == "SR" and props["BMin"] == "75":
                max_bound = 1.15
                min_bound = 0.85
        if self.cfg.prepost_ratio and self.prefit != 0:
            max_bound = 1.1
            min_bound = 0.9
        if "VHccRun2" in os.getenv("ANALYSISTYPE"):
            props = self.properties
            if props["T"] == "1":
                max_bound = 1.2
                min_bound = 0.8
        if cfg.find_optimal_yrange:
            max_bound = 1+final_range
            min_bound = 1-final_range
        if "AZh" in os.getenv("ANALYSISTYPE"):
            max_bound = 1.6
            min_bound = 0.4
            props = self.properties
            if props["T"] == "3" and props["D"] == "SR" and props["L"] == "2" :
                max_bound = 1.9
                min_bound = 0.1
        if "VHqqRun2" in os.getenv("ANALYSISTYPE"):
            max_bound = 1.6
            min_bound = 0.4
        hdash.SetMaximum(max_bound)
        hdash.SetMinimum(min_bound)
        if plot_ratio:
            if logx: ROOT.gPad.SetLogx()
            hdash.GetXaxis().SetTitleSize(0.15)
            hdash.GetXaxis().SetLabelSize(0.15)
            hdash.GetYaxis().SetLabelSize(0.15)
            hdash.GetYaxis().SetTitleSize(0.15)
#            hdash.GetYaxis().SetNdivisions(503) # init
            if "AZh" in os.getenv("ANALYSISTYPE"):
                hdash.GetYaxis().SetNdivisions(505)
                hdash.GetXaxis().SetMoreLogLabels(1)
            else:
                hdash.GetYaxis().SetNdivisions(ndiv)
            hdash.GetYaxis().SetTickLength(0.035)
            hdash.GetXaxis().SetTickLength(0.1)
            hdash.GetYaxis().SetTitleOffset(0.4)
            hdash.GetXaxis().SetTitleOffset(1.3)
            if (self.properties["dist"]=="NAdditionalCaloJets"):
                hdash.GetXaxis().SetNdivisions(107)
            elif (self.properties["dist"]=="Naddbtrackjets"):
                hdash.GetXaxis().SetNdivisions(103)

        if self.properties is not None:
            logging.info('generate the dash line for bottom ratio pad')
            if "VHbbRun2" in os.getenv("ANALYSISTYPE") or "AZh" in os.getenv("ANALYSISTYPE") or "VHccRun2" in os.getenv("ANALYSISTYPE") or "VHqqRun2" in os.getenv("ANALYSISTYPE") or "SemileptonicVBS" in os.getenv("ANALYSISTYPE") or "TemplateAnalysis" in os.getenv("ANALYSISTYPE"):
                hdash,l = cfg.postprocess_dataMC_ratio_histogram(self.properties, hdash, xbounds)
            else:
                hdash = cfg.postprocess_dataMC_ratio_histogram(self.properties, hdash, xbounds)

        draw(hdash, "hist")
        if "VHbbRun2" in os.getenv("ANALYSISTYPE") or "VHqqRun2" in os.getenv("ANALYSISTYPE") or "AZh" in os.getenv("ANALYSISTYPE") or "VHccRun2" in os.getenv("ANALYSISTYPE") or "SemileptonicVBS" in os.getenv("ANALYSISTYPE"): draw(l, "")
        draw(htemp, "pz0")


        ## Put arrows in ratio for points outside the range
        #props = self.properties
        #if ((props["L"] == "1") and (props["J"] == "2") and (props["D"] == "WhfCR") and (props["dist"] == "pTV") and (props['BMin'] == "150")):
        #    final_range = 0.5
        scale_range = 0.9*final_range
        scale_err = 0.5*final_range
        g_val_x_up = []
        g_val_y_up = []
        g_err_x_up = []
        g_err_y_up = []
        g_val_x_do = []
        g_val_y_do = []
        g_err_x_do = []
        g_err_y_do = []
        for i in range(htemp.GetN()):
            b = self.hsum.FindBin(xvals[i])
            if yvals[i] - yerrdo[i] > 1+final_range :
                g_val_x_up.append(self.hsum.GetBinCenter(b))
                g_val_y_up.append(1+scale_range)
                g_err_x_up.append(0.)
                g_err_y_up.append(scale_err)
            elif yvals[i] + yerrup[i] < 1-final_range :
                g_val_x_do.append(self.hsum.GetBinCenter(b))
                g_val_y_do.append(1-scale_range)
                g_err_x_do.append(0.)
                g_err_y_do.append(scale_err)
        if len(g_val_x_up) > 0 :
            htemp_up = ROOT.TGraphErrors(len(g_val_x_up), array.array('f',g_val_x_up), array.array('f',g_val_y_up), array.array('f',g_err_x_up), array.array('f',g_err_y_up))
            htemp_up.SetMarkerStyle(22)
            draw(htemp_up, "ep")
        if len(g_val_x_do) > 0 :
            htemp_do = ROOT.TGraphErrors(len(g_val_x_do), array.array('f',g_val_x_do), array.array('f',g_val_y_do), array.array('f',g_err_x_do), array.array('f',g_err_y_do))
            htemp_do.SetMarkerStyle(23)
            draw(htemp_do, "ep")

        if self.fiterr:
            # creation of the ratio hist done here. Could be moved if needed
            errtmp = clone(self.fiterr.h)
            npoints = errtmp.GetN()
            yvals = errtmp.GetY()
            xvals = errtmp.GetX()
            for i in range(errtmp.GetN()//2):
                if abs(yvals[i] - yvals[npoints-i-1]) < 0.000001: # Cut off point, removing error bands < 1e-6
                    continue
                midpoint = (yvals[i] + yvals[npoints-i-1])/2.
                if(abs(midpoint) > 1e-6):
                    yvals[i] /= midpoint
                    yvals[npoints-i-1] /= midpoint


            to_remove = [i for i in range(errtmp.GetN()) if yvals[i] == 0]
            # print to_remove
            # JWH
            for i in reversed(to_remove):
                errtmp.RemovePoint(i)

            # JWH
            draw(errtmp, "f")
        if self.cfg.prepost_ratio and self.prefit != 0:
            draw(histprepost_ratio, "histsame")

        if xtitle:
            hdash.GetXaxis().SetTitle(xtitle)
        else:
            hdash.GetXaxis().SetTitle(cfg.get_xTitle(self.properties, self.data.hist))
        #hdash.GetYaxis().SetTitle("Data/MC")
        if "AZh" in os.getenv("ANALYSISTYPE") and not cfg.add_sig_to_ratio_plot:
            hdash.GetYaxis().SetTitle("data/bkg")
        else:
            hdash.GetYaxis().SetTitle("Data/Pred.")
        if xbounds:
            hdash.GetXaxis().SetRangeUser(xbounds[0], xbounds[1])

    def draw_dataMC_difference(self, cname=""):
        """ Function to draw background-subtracted histograms.

        Subtract backgrounds from everything, and pass the resulting objects
        to make_complete_plot()
        """
        bkgsum = clone(self.hsum)
        model = clone(self.hsum)
        model.Reset()
        diboson = Bkg(self.cfg, model, self.cfg.bkg_substr_name, self.properties)
        for sample in self.cfg.bkg_substr_list:
            res = self.find_bkg(sample)
            if res:
                bkgsum.Add(res.h, -1)
                diboson.h.Add(res.h)

        setup_tmp = Setup(self.cfg,self.title,True)
        setup_tmp.determine_weighted(cname)
        setup_tmp.isBkgSub = True
        setup_tmp.data = self.data.subtract(bkgsum)
        setup_tmp.append_bkg(diboson)
        setup_tmp.sig = self.sig
        setup_tmp.sig_to_use = self.sig_to_use
        if self.fiterr:
            setup_tmp.fiterr = self.fiterr.center_at_0()
        setup_tmp.chi2 = self.chi2

        stack= ROOT.THStack("stack","stack")
        if diboson.h : stack.Add(diboson.h)
        stack.Add(self.sig_to_use.h)
        hdata = clone(setup_tmp.data.h)
        errtmp = clone(setup_tmp.fiterr.h)

        draw(stack, "hist")
        draw(errtmp, "fsame")
        draw(hdata, "epsame")

        stack.GetXaxis().SetTitle(self.cfg.get_xTitle(self.properties,hdata))
        stack.GetYaxis().SetTitle("Data - bkg")
        stack.SetMinimum(hdata.GetYaxis().GetXmin());
        stack.SetMaximum(hdata.GetYaxis().GetXmax());
        stack.GetXaxis().SetTitleSize(0.08)
        stack.GetXaxis().SetLabelSize(0.08)
        stack.GetYaxis().SetLabelSize(0.08)
        stack.GetYaxis().SetTitleSize(0.08)
        stack.GetYaxis().SetNdivisions(505)

        stack.GetXaxis().SetTitleOffset(1.1)
        stack.GetYaxis().SetTickLength(0.035)
        stack.GetXaxis().SetTickLength(0.060)
        stack.GetYaxis().SetTitleOffset(0.75)

    @init_finished
    def draw_SoB_ratio(self, plot_ratio = False, ybounds=(.5, 1.5), xtitle="", ratioType=0):
        """ Function to draw the bottom pad, i.e ratios, for S/B plot

        Take care of horrendous things like adjusting all fontsizes
        """
        if self.sig_to_use is None: return
        hdata = clone(self.data.hist)
        hdata.Sumw2(True)
        # FIXME wtf why the Divide does not work ? Error bars are wrong !?
        #hdata.Divide(self.hsum)
        hsig = clone(self.sig_to_use.h)
        for i in range(hdata.GetNbinsX()):
            if self.hsum.GetBinContent(i) != 0:
                D = hdata.GetBinContent(i)
                B = self.hsum.GetBinContent(i)
                S = hsig.GetBinContent(i)
                # data / bkg
                hdata.SetBinContent(i, D / B)
                hdata.SetBinError(i, math.sqrt(D) / B)
                hsig.SetBinContent(i, (S + B) / B)
                if ratioType == 1:
                    # (data - bkg) / sqrt(bkg)
                    hdata.SetBinContent(i, (D - B) / math.sqrt(B))
                    hdata.SetBinError(i, math.sqrt(D) / math.sqrt(B))
                    hsig.SetBinContent(i, S / math.sqrt(B))
                if ratioType == 2:
                    # (data - bkg) / signal
                    hdata.SetBinContent(i, (D - B) / S)
                    hdata.SetBinError(i, math.sqrt(D) / S)
                    hsig.SetBinContent(i, 1)
        #hsig = clone(self.exp_sig.h)
        #hsig.Add(self.hsum)
        #hsig.Divide(self.hsum)
        hsig.SetFillColor(0)
        hsig.SetLineColor(ROOT.kRed)
        hsig.SetLineWidth(4)
        gsig = make_tgraph_from_hist(hsig)

        hdash = clone(self.data.hist)
        hdash.Reset()
        for i in range(hdash.GetNbinsX()+1):
            hdash.SetBinContent(i, 1)
            if ratioType != 0:
                hdash.SetBinContent(i, 0)
        hdash.SetLineStyle(ROOT.kDashed)
        hdash.SetMaximum(ybounds[1])
        hdash.SetMinimum(ybounds[0])

        if plot_ratio:
            hdash.GetXaxis().SetTitleSize(0.15)
            hdash.GetXaxis().SetLabelSize(0.15)
            hdash.GetYaxis().SetLabelSize(0.15)
            hdash.GetYaxis().SetTitleSize(0.15)
            if "AZh" in os.getenv("ANALYSISTYPE"):
                hdash.GetYaxis().SetNdivisions(505)
                hdash.GetXaxis().SetTitleOffset(1.3)
                hdash.GetXaxis().SetMoreLogLabels(1)
            else:
                hdash.GetYaxis().SetNdivisions(503)
                hdash.GetXaxis().SetTitleOffset(1.1)
            hdash.GetYaxis().SetTickLength(0.035)
            hdash.GetXaxis().SetTickLength(0.1)
            hdash.GetYaxis().SetTitleOffset(0.4)

        draw(hdash, "hist")
        #draw(hsig, "histsame")
        draw(gsig, "l")
        draw(hdata, "esame")
        if xtitle:
            hdash.GetXaxis().SetTitle(xtitle)
        else:
            hdash.GetXaxis().SetTitle(self.get_xTitle())
        if "AZh" in os.getenv("ANALYSISTYPE") and not cfg.add_sig_to_ratio_plot:
            hdash.GetYaxis().SetTitle("data/bkg")
        else:
            hdash.GetYaxis().SetTitle("Data/Pred.")
        if ratioType == 1:
            hdash.GetYaxis().SetTitle("Pull (stat.)")
        if ratioType == 2:
            hdash.GetYaxis().SetTitle("(D-B)/S")

    def draw_title(self, pos):
        """ Draw title of the plot, i.e the category it shows """
        props = self.properties
        if not props:
            return

        l = self.new_TLatex(small = True)
        next_pos = self.cfg.draw_category_ids(props, l, pos, self.normalFontSize)

        if not self.cfg._weighted:
            if hasattr(self.cfg, 'showChi2') and self.cfg.showChi2:
                # pass
                self.draw_chi2((next_pos[0], next_pos[1]))
        else:
            self.draw_weight_title((next_pos[0], next_pos[1]))

    def draw_chi2(self, pos):
        """ Draw chi2 if present """
        if self.chi2 == -1:
            return
        l = self.new_TLatex(small = True)
        ts_chi2 = f"#chi^{{2}}={self.chi2:1.1f}"
        l.DrawLatex(pos[0], pos[1], ts_chi2)

    def draw_weight_title(self, pos):
        """ Draw special line for weighted plots """
        l = self.new_TLatex(small = True)
        text = f"Weighted by {self.cfg._weighted} S/B"
        l.DrawLatex(pos[0], pos[1], text)

    def draw_lumi(self, pos):
        """ Draw Lumi for 1 or 2 years """
        cfg = self.cfg
        l = self.new_TLatex(small = True)
        l.SetTextFont(42)
        def draw_line(x, y, s, lumi):
            l.DrawLatex(x, y, f"#sqrt{{s}} = {s} TeV, {lumi} fb^{{-1}} ")
        rinfo = cfg.get_run_info()
        # NOTE: combine com's that are the same
        com_set = {}
        for year in rinfo.keys():
            com = rinfo[year][1]
            if com in com_set.keys():
                prev_year = com_set[com]
                lumi = rinfo[year][0]
                prev_lumi = rinfo[prev_year][0]
                rinfo[prev_year][0] = str(float(rinfo[prev_year][0]) + float(lumi))
                del rinfo[year]
            else:
                com_set[com] = year
        for count, year in enumerate(rinfo.keys()):
            draw_line(pos[0], pos[1] - count*1.7*self.smallFontSize, rinfo[year][1], rinfo[year][0])

    def draw_ATLAS_label(self, pos):
        """ Reimplementation of the official macro with better spacing """
        x = pos[0]
        y = pos[1]
        l = self.new_TLatex()
        delx = 0.13
        l.DrawLatex(x, y, "ATLAS")
        p = self.new_TLatex()
        p.SetTextFont(42)
        p.DrawLatex(x+delx, y, self.cfg.ATLAS_suffix)

    def new_TLatex(self, small = False):
        """ Create a simple TLatex object with correct properties """
        l = ROOT.TLatex()
        l.SetNDC()
        l.SetTextFont(72)
        if small:
            l.SetTextSize(self.smallFontSize)
        else:
            l.SetTextSize(self.normalFontSize)
        l.SetTextColor(1)
        l.SetTextAlign(11)
        return l

    def plot_with_additional_signal(self):
        if self.isBkgSub:
            return False
        props = self.properties
        if props:
            if self.cfg.determine_additional_plots_from_properties(props): return True
        return False



class SetupMaker:
    """ A class that creates a Setup from various configurations """
    def __init__(self, cfg, title="", mass=125, muhat=None, guess_properties=True, bin_dir=None, bin_hName="", divide_width=True):
        cfg._year = cfg.determine_year_from_title(title)
        self.setup = Setup(cfg, title, guess_properties)
        self.mass = mass
        self.muhat = muhat
        self.setup.divide_width = divide_width
        self.cfg = cfg

        if bin_hName=="":
            logging.info("No bin histo name given")
            bin_hName = title

        logging.info("will extract binning using: "+bin_hName+" has histo")
        self.binhist = self.get_binning_hist(bin_dir, bin_hName)

    def make_from_directory(self, tdir):
        """ To be revived FIXME """
        for hist,name in ((k.ReadObj(), k.GetName()) for k in tdir.GetListOfKeys() if k.ReadObj().InheritsFrom("TH1")):
            self.add(name, hist)

    def make_from_ws_dir(self, tdir):
        """ To be revived FIXME """
        for key in tdir.GetListOfKeys():
            name = key.GetName()
            subdir = key.ReadObj()
            hist = [k.ReadObj() for k in subdir.GetListOfKeys() if not "_Sys" in k.GetTitle()]
            if len(hist) == 0:
                logging.error("could not find histogram "+name+" in region "+tdir.GetName())
                return
            if len(hist)>1:
                logging.info("found histograms "+name+" in region "+tdir.GetName())
                return
            self.add(name, hist[0])

    def get_binning_hist(self, binDir, title):
        ""
        cfg = self.cfg

        if binDir is None:
            return None

        # for r in cfg.get_binning_hist_removal:
        #     title = title.replace(r, "") # For combination

        binHist = binDir.Get("bins_" + title)

        if not binHist:
            binHist = None

        return binHist

    def rebin_plots(func):
        """ decorator to add() to extend functionality
        """
        def f(self, name, hist):
            new_hist = hist
            # # first, tackle bin label issues with MV1c
            # if isinstance(hist, ROOT.TH1):
            #     props = self.setup.properties
            #     if props:
            #         if "MV1c" in props["dist"]:
            #             relabel_mv1c_axis(hist)
            # Then, rebin 1 lepton histos that were made in MeV
            if isinstance(hist, ROOT.TH1) or isinstance(hist, ROOT.TGraph):
                new_hist = self.cfg.preprocess_main_content_histogram(new_hist, self)
                props = self.setup.properties
                # TODO: cfg
                if self.binhist and props and self.cfg.do_rebinning(props):
                    new_hist = rebin_hist(new_hist, self.binhist)
#                     try:
#                         for i in xrange(1, new_hist.GetNbinsX()+1):
#                             print "REBIN >>> ", i, new_hist.GetBinLowEdge(i), new_hist.GetBinWidth(i), new_hist.GetBinContent(i), new_hist.GetBinError(i)
#                     except AttributeError:
#                         pass

#                 if props:
#                     # Changes for MeV/GeV
#                     affected_dists = ["MEff", "MEff3", "MET", "mLL", "mTW", "pTB1", "pTB2", "pTJ3", "pTV", "mBB", "mBBJ"]
#                     if props["L"] == "1" and props["dist"] in affected_dists:
#                         new_hist = change_MeV_GeV(hist)

            elif isinstance(hist, list):
                for i,h in enumerate(hist):
                    if isinstance(h, ROOT.TH1) or isinstance(h, ROOT.TGraph):
                        hist[i] = self.cfg.preprocess_main_content_histogram(h, self)
                        props = self.setup.properties
                        # TODO: cfg
                        if self.binhist and props and self.cfg.do_rebinning(props):
                            newh = rebin_hist(h, self.binhist)
                            hist[i] = newh
                #     for i,h in enumerate(hist):
                #         if isinstance(h, ROOT.TH1) or isinstance(h, ROOT.TGraph):
                #             newh = rebin_hist(h, self.binhist)
                #             hist[i] = newh

            return func(self, name, new_hist)
        return f

    @rebin_plots
    def add(self, name, hist):
        """ Add objects one by one to the setup """
        logging.debug(f"attempting to add sample: {name}")
        if name == "data" or name == "My_Data":
            self.setup.data = Data(self.cfg, hist)
        elif "BeforeFit" in name:
            return
        elif "DataAsym" in name:
            return
        elif "My_FitError_AfterFit" in name:
            self.setup.fiterr = FitError(hist, self.cfg)
        elif name == "error":
            self.setup.fiterr = FitError(hist, self.cfg)
        elif True in (signame in name for signame in self.cfg.sig_names): # signal samples
            # Jake: self.mass = 1 for VHF analysis
            if (self.mass  != 0) and (not str(self.mass) in name) and (self.mass != 1):
                return
            if self.setup.sig:
                self.setup.sig.append(hist)
            else:
                self.setup.sig = Signal(self.cfg, hist, self.mass, muhat=self.muhat)
        elif name == "mass":
            self.setup.mass = hist
            self.mass = hist
        elif name == "chi2":
            self.setup.chi2 = hist
        elif name == "prefit":
            self.setup.prefit = PreFit(hist)

        else:
            if name.startswith("My"):
                name = name[3:]
            if name in self.cfg.bkg_tuple:
                self.setup.append_bkg(Bkg(self.cfg, hist, name, self.setup.properties))
            else:
                logging.debug(f"MC named {name} is unknown. Skipping it!")
            # try :
            #     if name.startswith("My"):
            #         name = name[3:]
            #     if name in self.cfg.bkg_tuple:
            #         self.setup.append_bkg(Bkg(hist, name))
            #     else:
            #         print "add():: MC named {0} is unknown. Skip it !".format(name)
            #     #self.cfg.__getattribute__(self.cfg, name)
            # except AttributeError:
            #     print "add():: MC named {0} is unknown. Skip it !".format(name)

# def change_MeV_GeV(hist):
#     if isinstance(hist, ROOT.TH1):
#         new_hist = hist.Clone()
#         bins = new_hist.GetXaxis().GetXbins()
#         for i in range(bins.GetSize()):
#             bins[i] /= 1000.
#         new_hist.SetBins(bins.GetSize()-1, bins.GetArray())
#         for i in range(new_hist.GetNbinsX()+2):
#             new_hist.SetBinContent(i, hist.GetBinContent(i))
#             new_hist.SetBinError(i, hist.GetBinError(i))
#     elif isinstance(hist, ROOT.TGraph):
#         new_hist = hist
#         xbins = new_hist.GetX()
#         for i in range(new_hist.GetN()):
#             xbins[i] /= 1000.
#         if isinstance(hist, ROOT.TGraphAsymmErrors):
#             xbinsup = new_hist.GetEXhigh()
#             xbinsdo = new_hist.GetEXlow()
#             for i in range(new_hist.GetN()):
#                 xbinsup[i] /= 1000.
#                 xbinsdo[i] /= 1000.
#     return new_hist

def rebin_hist(hist, binHist, divide_width=True):
    logging.info(f"Rebinning histogram {hist.GetName()}")
    bins = binHist.GetXaxis().GetXbins()
    if bins.GetSize()==0:
        logging.info('Size of bins-array is 0. Happens if it is a fix-bin histo, ie equidistant bins. I assume no rebinning is then needed!')
        return hist
    errband = bool('FitError' in hist.GetName())

    if isinstance(hist, ROOT.TH1):

        if hist.GetNbinsX() != binHist.GetNbinsX():
            logging.warning(f'Rebinning hist has a different length ({binHist.GetNbinsX()}) than the original hist ({hist.GetNbinsX()}). Skipping rebinning!')
            return hist

        new_hist = hist.Clone()
        new_hist.SetBins(bins.GetSize()-1, bins.GetArray())
        for i in range(new_hist.GetNbinsX()+2):

            w = new_hist.GetBinWidth(i)
            if divide_width and w != 0:
                new_hist.SetBinContent(i, hist.GetBinContent(i)/w)
                new_hist.SetBinError(i, hist.GetBinError(i)/w)

    elif isinstance(hist, ROOT.TGraph) and errband:
        new_hist = hist.Clone()
        xbins = new_hist.GetX()
        ybins = new_hist.GetY()
        binArray = bins.GetArray()
        npt = new_hist.GetN()

        ibin = -1
        for i in range(new_hist.GetN()//2):
            if i == (new_hist.GetN()//2 - 3):
                xbins[i] = binArray[binHist.GetNbinsX()]
                xbins[npt -i -1] = binArray[binHist.GetNbinsX()]
            elif abs(i - new_hist.GetN()//2) < 3:
                xbins[i] = binArray[binHist.GetNbinsX()] + (binArray[binHist.GetNbinsX()] - binArray[binHist.GetNbinsX()-1])
                xbins[npt -i -1] = binArray[binHist.GetNbinsX()] + (binArray[binHist.GetNbinsX()] - binArray[binHist.GetNbinsX()-1])
            elif ibin >= 0:
                xbins[i] = binArray[ibin]
                xbins[npt -i -1] = binArray[ibin]

                if divide_width:
                    if ibin == binHist.GetNbinsX():
                        w = binArray[ibin] - binArray[ibin-1]
                    else:
                        if i%2 != 0:
                            w = binArray[ibin+1] - binArray[ibin]
                        else:
                            if ibin > 0:
                                w = binArray[ibin] - binArray[ibin-1]
                            else:
                                w = 0

                    if w != 0:
                        ybins[i] /= w
                        ybins[npt -i -1] /= w

            logging.debug(f'bin {i}, x {xbins[i]}, y {ybins[i]}')
            if i%2 != 0: ibin += 1

    elif isinstance(hist, ROOT.TGraph):
        new_hist = hist
        xbins = new_hist.GetX()
        ybins = new_hist.GetY()
        binArray = bins.GetArray()

        for i in range(new_hist.GetN()):
            xbins[i] = (binArray[i+1]+binArray[i])/2.
            w = (binArray[i+1]-binArray[i])
            if divide_width and w != 0:
                ybins[i] /= w

        if isinstance(hist, ROOT.TGraphAsymmErrors):
            xbinsup = new_hist.GetEXhigh()
            xbinsdo = new_hist.GetEXlow()
            for i in range(new_hist.GetN()):
                xbinsup[i] = (binArray[i+1]-binArray[i])/2.
                xbinsdo[i] = (binArray[i+1]-binArray[i])/2.

                w = (binArray[i+1]-binArray[i])
                if divide_width and w != 0:
                    ybinsup = new_hist.GetEYhigh()
                    ybinsdo = new_hist.GetEYlow()
                    ybinsup[i] /= w
                    ybinsdo[i] /= w



    return new_hist

# def relabel_mv1c_axis(hist):
#     nbins = hist.GetXaxis().GetNbins()
#     if nbins is 4 or 5:
#         print "Adjusting x-axis labels..."
#         for ibin in range(1, nbins+1):
#             hist.GetXaxis().SetBinLabel(ibin, "")
#             hist.GetXaxis().SetNdivisions(-1)

# Types of samples:

class Data:
    """ A class that represents data
    At present self.h is a TGraphAsymmErrors, self.hist is a TH1 built from it """
    # TODO: put ifs to handle h as both TGraph and TH1 gracefully
    def __init__(self, cfg, h):
        self.cfg = cfg
        self.color = ROOT.kBlack
        if cfg.generate_pseudodata:
            self.color = ROOT.kBlue
        self.h = clone(h)
        self.h.SetMarkerColor(self.color)
        self.h.SetMarkerStyle(20)
        self.h.SetMarkerSize(1)
        self.h.SetLineWidth(2)
        self.h.SetLineColor(self.color)
        if "AZh" in os.getenv("ANALYSISTYPE"):
            self.title = f"data {cfg.get_year_str()}"
        elif cfg.generate_pseudodata:
            self.title = f"Pseudo-Data {cfg.get_year_str()}"
        else:
            self.title = f"Data {cfg.get_year_str()}"
        #if cfg.year>2100: # UGLY
        #    self.title = "Data"
        #else:
        #    self.title = "Data {0}".format(cfg.year)

    def blind(self, minval, maxval):
        """ Remove data points between minval and maxval """
        if type(self.h) == ROOT.TH1F:
            for i in range(1, self.h.GetNbinsX()+1):
                bincenter = self.h.GetXaxis().GetBinCenter(i)
                if bincenter > minval and bincenter < maxval:
                    self.h.SetBinContent(i, 0)
                    self.h.SetBinError(i, 0)
        else:
            xvals = self.h.GetX()
            xerrup = self.h.GetEXhigh()
            xerrdo = self.h.GetEXlow()
            to_remove = [i for i in range(self.h.GetN())
                         if (xvals[i]+xerrup[i])>minval and (xvals[i]-xerrdo[i])<maxval]
            for i in reversed(to_remove):
                self.h.RemovePoint(i)

    def randomize(self, htemplate):
        """ Replace actual data by pseudo-data according to htemplate """
        yval = self.h.GetY()
        errhi = self.h.GetEYhigh()
        errlo = self.h.GetEYlow()

        # TODO this works for the propaganda S/B weighted plots.
        # should make a version for unweighted (Poisson) data instead
        rd = ROOT.TRandom3(random.randint(0,1000000))
        for i in range(htemplate.GetNbinsX()):
            data_err = (errhi[i]+errlo[i])*1./2
            old_y = yval[i]
            val = rd.Gaus(htemplate.GetBinContent(i+1), data_err)
            yval[i] = val

    def clean(self):
        """ Remove empty data points """
        if type(self.h) == ROOT.TH1F:
            return
        yvals = self.h.GetY()
        to_remove = [i for i in range(self.h.GetN()) if yvals[i] == 0]
        for i in reversed(to_remove):
            self.h.RemovePoint(i)

    def add_to_legend(self,leg):
        """ Add object to legend """
        leg.AddEntry(self.h, self.title, "pl")

    def make_data_hist(self, hist_model):
        """ Create histogram from TGraphAsymmErrors """
        if type(self.h) == ROOT.TH1F:
            self.hist = clone(self.h)
        else:
            self.hist = clone(hist_model)
            self.hist.Reset()
            yvals = self.h.GetY()
            xvals = self.h.GetX()
            yerrup = self.h.GetEYhigh()
            yerrdo = self.h.GetEYlow()
            for i in range(self.h.GetN()):
                b = self.hist.FindBin(xvals[i])
                self.hist.SetBinContent(b, self.hist.GetBinContent(b) + yvals[i])
                errmean = (yerrup[i] + yerrdo[i]) / 2
                curr_err = self.hist.GetBinError(b)
                new_err = (errmean**2 + curr_err**2)**.5
                self.hist.SetBinError(b, new_err)
        self.hist.SetMarkerColor(self.color)
        self.hist.SetMarkerStyle(20)
        self.hist.SetMarkerSize(1)
        self.hist.SetLineColor(self.color)
        self.hist.SetFillStyle(0)

    def subtract(self, hist):
        """ Subtract contents of hist from self TGraphAsymmErrors """
        res = clone(self.h)
        if type(res) == ROOT.TH1F:
            res.Add(hist, -1)
        else:
            yvals = res.GetY()
            xvals = res.GetX()
            for i in range(res.GetN()):
                b = hist.FindBin(xvals[i])
                val = hist.GetBinContent(b)
                yvals[i] -= val
        return Data(self.cfg,res)


class PreFit:
    """ A class that represents prefit sum of MC """
    def __init__(self, couple):
        hist = couple[0]
        leg = couple[1]
        self.h = clone(hist)
        #self.h.SetLineColor(ROOT.kBlue)
        #self.h.SetLineColor(ROOT.kGray+3)
        self.h.SetLineColor(ROOT.kBlue+2)
        self.h.SetLineWidth(4)
        self.h.SetLineStyle(ROOT.kDashed)
        self.title = leg

    def add_to_legend(self,leg):
        """ Add object to legend """
        leg.AddEntry(self.h, self.title, "l")

    def subtract(self, hist):
        """ Subtract contents of hist from self """
        res = clone(self.h)
        res.Add(hist, -1)
        return PreFit((res, self.title))



class FitError:
    """ A class that represents postfit error """
    def __init__(self, hist, cfg):
        self.cfg = cfg
        self.h = clone(hist)
        self.h.SetFillColor(ROOT.kBlack)
        self.h.SetLineColor(ROOT.kBlack)
        #self.h.SetFillStyle(3444) # > 3100 problems -> need to find new bands
        if "AZh" in os.getenv("ANALYSISTYPE"):
            self.title = "uncertainty"
            self.h.SetFillStyle(3002)  # init
        else:
            if cfg.isMoneyPlot:
                self.title = "B-only uncertainty"
            else:
                self.title = "Uncertainty"
            self.h.SetFillStyle(3004) # init
        self.h.SetMarkerStyle(0)
    def add_to_legend(self,leg):
        """ Add object to legend """
        leg.AddEntry(self.h, self.title, "f")

    def subtract(self, hist):
        """ Subtract contents of hist from self

        LOOKS BUGGED FIXME
        """
        res = clone(self.h)
        yvals = res.GetY()
        xvals = res.GetX()
        for i in range(res.GetN()):
            b = hist.FindBin(xvals[i])
            val = hist.GetBinContent(b)
            if yvals[i]!=0:
                yvals[i] -= val
        return FitError(res, self.cfg)

    def center_at_0(self):
        """ Center this crazy TGraphAsymmErrors around 0 """
        res = clone(self.h)
        yvals = res.GetY()
        xvals = res.GetX()
        size = res.GetN()
        for i in range(size):
            mean = (yvals[i] + yvals[size-1-i]) /2
            yvals[i] -= mean
            yvals[size-1-i] -= mean
        return FitError(res, self.cfg)


class Signal:
    """ A class that represents signal MC """
    # STACK = 1
    # OVERPRINT = 2

    def __init__(self, cfg, hist, mass, muhat=None, is_expected=False, is_additional=False):
        self.cfg = cfg
        self.h = clone(hist)
        self.mass = mass
        self.muhat = muhat
        if is_expected:
            sigconf = cfg.expected_signal
        elif is_additional:
            sigconf = cfg.additional_signal
        else:
            sigconf = cfg.signal
        self.title = sigconf[0]
        self.mode = sigconf[1]
        if self.mode == cfg._STACK:
            self.h.SetFillColor(sigconf[2])
            self.h.SetLineWidth(0)
        else:
            logging.debug(f"MODE IS NOT STACK: {cfg._STACK} =/= {self.mode}")
            self.h.SetFillColor(0)
            self.h.SetLineColor(sigconf[2])
            self.h.SetLineWidth(4)
            if "AZh" in os.getenv("ANALYSISTYPE"):
                self.h.SetLineStyle(ROOT.kDashed)
                self.h.SetLineStyle(9)
        self.mult_factor = cfg.force_mu_value()[1]#sigconf[3]
        if self.mult_factor > 1 and not ("AZh" in os.getenv("ANALYSISTYPE") or "VHbbRun2" in os.getenv("ANALYSISTYPE") or "VHqqRun2" in os.getenv("ANALYSISTYPE")):
            self.title += f"#times{self.mult_factor}"
        self.has_scaled = False

    def scale(self):
        """ Scale histogram by a multiplicative factor """
        if not self.has_scaled:
            self.h.Scale(self.mult_factor)
            self.has_scaled = True

    def append(self, hist):
        """ Merge different signal samples """
        self.h.Add(hist)

    def add_to_legend(self, leg):
        """ Add object to legend """
        if self.mode == self.cfg._STACK:
            leg.AddEntry(self.h, self.title, "f")
            if not "AZh" in os.getenv("ANALYSISTYPE"): self.cfg.add_additional_signal_info_to_legend(leg, self)
        else:
            leg.AddEntry(self.h, self.title, "l")
            if not "AZh" in os.getenv("ANALYSISTYPE"): self.cfg.add_additional_signal_info_to_legend(leg, self)

    def make_expected_signal(self):
        """ Create a new Signal object with muhat = self.muhat """
        logging.info(f"Creating signal with muhat = {self.muhat}")
        if self.muhat is None:
            return None
        newsig = Signal(self.cfg, self.h, self.mass, self.muhat, True)
        if self.muhat != 0:
            newsig.mult_factor /= self.muhat
        newsig.scale()
        return newsig

    def make_additional_signal(self, new_mult_factor, dist, prop):
        """ Create a new Signal object with muhat = self.muhat """
        if self.muhat is None:
            return None
        logging.info(f"Signal with muhat = {self.muhat}")
        newsig = Signal(self.cfg, self.h, self.mass, self.muhat, False, True)
        if self.muhat != 0:
            tmp_scale=0.5
            new_mult_factor = tmp_scale*new_mult_factor/self.h.Integral()
            new_mult_factor = self.cfg.fine_tune_additional_signal_mult_factor(dist, prop, new_mult_factor)
            # pass final new_mult_factor
            newsig.mult_factor = new_mult_factor
            newsig.title += f" #times {int(new_mult_factor)}"
        logging.info(f"Scaled down by muhat = {self.muhat}")
        newsig.mult_factor /= self.muhat
        newsig.scale()
        logging.info(f"Post scaled yields = {newsig.h.Integral()}")
        return newsig



class Bkg:
    """ A class that represents background MC """
    def __init__(self, cfg, hist, name, prop):
        self.cfg = cfg
        self.h = clone(hist)
        bkgconf = cfg.bkg_tuple[name]
        self.title = bkgconf[0]
        self.h.SetFillColor(bkgconf[2])
        self.h.SetLineWidth(0)
        self.h.SetFillStyle(1001)
        if len(bkgconf) > 4:
            self.h.SetFillStyle(bkgconf[4])
            self.h.SetLineWidth(2)
            self.h.SetLineColor(ROOT.kBlack)
        #logging.info("add background for {0}".format(prop["dist"]))
        # let Z+jets on top of the rest bkg, this only done for mLL
        #if prop["dist"]=="mLL" and name in ['Zl','Zhf','Zcc','Zcl','Zbl','Zclbl','Zbc','Zbb']:
        #if prop["L"] == "2" and name in ['Zl','Zhf','Zcc','Zcl','Zbl','Zclbl','Zbc','Zbb']:
        #    self.priority = bkgconf[1]+34
        #else:
        #    self.priority = bkgconf[1]
        if prop is None:
            self.priority = bkgconf[1]
        else:
            if "L" in prop and prop["L"] == "2" :
                if (prop["dist"] == "pTV") and (prop["D"] == "topemucr"):
                    self.priority = bkgconf[1]
                elif name in ['Zl','Zhf','Zcc','Zcl','Zbl','Zclbl','Zbc','Zbb','diboson','Diboson','ZZ','WW']:
                    self.priority = bkgconf[1]+34
                elif (prop['dist'] == "mvadiboson") and name in ['VH125','WW']:
                    self.priority = bkgconf[1]+34
                else:
                    self.priority = bkgconf[1]
            else:
                self.priority = bkgconf[1]
        self.name = name
        self.mergelist = bkgconf[3]


    def __lt__(self, other):
        return self.priority < other.priority

    def __eq__(self, other):
        return self.priority == other.priority

    def add_to_legend(self,leg):
        """ Add object to legend """
        leg.AddEntry(self.h, self.title, "f")

    def append(self, other):
        """ Merge a Bkg object with the current one """
        self.h.Add(other.h)


def suffix(first_drawn):
    """ False->"same" or True->"" """
    if first_drawn:
        return ""
    else:
        return "same"


def divide_canvas(canvas, ratio_fraction):
    """ Divide the canvas into two pads; the bottom is ratio_fraction tall.
    """
    canvas.Clear()
    p1 = ROOT.TPad("p1", "p1", 0, ratio_fraction, 1, 1)
    #p1.SetFillStyle(4000) # transparent
    draw(p1)
    #p1.SetBottomMargin(0.00) # init
    p1.SetBottomMargin(0.012) # test
    p2 = ROOT.TPad("p2", "p2", 0, 0 ,1 , ratio_fraction)
    #p2.SetFillStyle(4000) # transparent
    #p2.SetTopMargin(0.04) # top margin -> init
    p2.SetTopMargin(0.045) # top margin -> test
    p2.SetBottomMargin(0.4)
    p1.SetLeftMargin(0.13)
    p1.SetRightMargin(0.075)
    p2.SetLeftMargin(0.13)
    p2.SetRightMargin(0.075)
    draw(p2)
    return p1, p2


# All util functions to workaround pyROOT shortcomings concerning pointers and scope

def clone(hist):
    """ Create real clones that won't go away easily """
    h_cl = hist.Clone()
    if hist.InheritsFrom("TH1"):
        h_cl.SetDirectory(0)
    release(h_cl)
    return h_cl

def draw(obj, opt=""):
    """ Draw something that will stay, even when current file is closed or function returns """
    # if is already released, do not clone/release
    if obj in pointers_in_the_wild:
        obj.Draw(opt)
    elif obj.InheritsFrom("TH1"):
        clone(obj).Draw(opt)
    else:
        release(obj).Draw(opt)

pointers_in_the_wild = set()
def release(obj):
    """ Tell python that no, we don't want to lose this one when current function returns """
    global pointers_in_the_wild
    pointers_in_the_wild.add(obj)
    ROOT.SetOwnership(obj, False)
    return obj

def purge():
    """ Delete all objects that we took control of """
    global pointers_in_the_wild
    for p in pointers_in_the_wild:
        if p:
            p.Delete()
    pointers_in_the_wild.clear()


def getPropertiesFromTag(cfg, regname):
    """ decompose a region name in nleptons, ntags, njets, VpT, year, distribution... with WSMaker 2 conventions """
    """ SKC: added some hacks to deal with some WSMaker <2 conventions """
    print( f'GETTING PROPERTIES FROM TAG: {regname}')
    properties = {}
    blocks = regname.split('_')[1 if (regname.find('Region_')==0 or regname.find('Htt_')==0) else 0:]  # remove "Region_" # remove "Htt_"
    for b in blocks: # SKC
        for bit in translateBlock(b):
            properties.update(getTagValuePair(cfg, bit))
    return properties

def translateBlock(b): # SKC
    if b=='mjj':
        return ['isMVA0','distmjj']
    elif b=='topemucr':
        return ['Dtopemucr','T2']
    elif b=='ZeroLepton':
        return ['L0']
    elif b=='OneLepton':
        return ['L1']
    elif b=='TwoLepton':
        return ['L2']
    pattern0 = re.findall('[0-5][TJ]',b) # 2011 lepton/jet convention
    if len(pattern0)!=0:
        return [bit[::-1] for bit in pattern0]
    pattern1 = re.findall('20[0-9][0-9]',b) # some years don't have 'Y' in front
    if len(pattern1)==1:
        if pattern1[0]==b:
            return [f'Y{b}']
    return [b]

def getTagValuePair(cfg, block):
    logging.debug(f"{block}")
    tags = cfg.file_tags
    matching_tags = [t for t in tags if block.startswith(t)]
    # if several matches, the right one is the one that macthes with most letters
    the_tag = max(matching_tags, key=len)
    val = block.replace(the_tag, '', 1)
    logging.debug(f"{block}, {the_tag}, {val}")
    return {the_tag : val}

def make_tgraph_from_hist(h):
    g = ROOT.TGraph(h)
    g.Expand(2*h.GetNbinsX())
    for i in range(h.GetNbinsX()):
        g.SetPoint(2*i, h.GetBinLowEdge(i+1), h.GetBinContent(i+1))
        g.SetPoint(2*i+1, h.GetBinLowEdge(i+2), h.GetBinContent(i+1))
    yvals = g.GetY()
    #to_remove = [i for i in range(g.GetN()) if yvals[i]==0]
    #for i in reversed(to_remove):
        #g.RemovePoint(i)
    return g
