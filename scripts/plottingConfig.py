import os
import os.path
import copy
import pickle
import logging
import ROOT
import re

class PlottingConfig:
    """ This is the class each analysis needs to inherit from to configure the plotting code """

    def __init__ (self):
        # hidden! expert use only!
        # _is_conditional, _is_asimov, and _mu describe the type of fit chosen for the FitResult
        self._is_conditional = False
        self._is_asimov = False
        self._mu = None
        self._fcc_directory = None
        self._main_suffix = ""
        self._main_plotdir = ""
        self._main_is_prefit = False
        self._main_save_hists = False
        self._weighted = ''
        self._yields = None
        self._comps = None
        self._plot_objs = None
        self._muhat = None
        self._yieldsfile = None
        self._plot_objs_file = None
        self._STACK = 1
        self._OVERPRINT = 2

        # hidden, but users are encouraged to use (but not set)
        self._year = None

        # for child classes to use
        self.loggingLvl = logging.DEBUG
        self.verbose = False # deprecated in favor of loggingLvl
        self.formats = [ 'eps' ]
        self.blind = False
        self.generate_pseudodata = False
        self.thresh_drop_legend = 0.01
        # restrict_to and excludes are there to search the
        # file names for sub-strings to limit samples
        self.restrict_to = []
        self.excludes = []
        self.additionalPlots = []
        self.add_sig_to_ratio_plot = False
        self.use_exp_sig = False
        self.draw_error_band_on_b_only = False
        self.bkg_substr_name = "None"
        self.bkg_substr_list = []
        self.file_tags = []
        self.weight_tags = []
        self.sig_names = ["AZhllbb"]
        self.signal = ["Signal (best fit)", self._STACK, ROOT.kRed + 1, 1] # last = mult factor
        self.expected_signal = ["Signal (#mu=1.0)", self._STACK, ROOT.kRed + 1, 1]
        # self.additional_signal = ["Signal", self._OVERPRINT, ROOT.kRed + 1, 1.]
        self.bkg_tuple = {'Background': ("bkg", 2, ROOT.kOrange, [])}
        self.ATLAS_suffix = "Internal"
        # for yields only
        self.make_slides = False
        self.window = None
        self.priorities = {}
        self.yTabGrps = {} # exple {"Wjets" : {"Whf","Wcl","Wl"}} to mrg Whf/Wcl/Wl in Wjets 
        # sub-pull plots
        self.NP_classification = {}
        # sub-correlation matrices
        self.cov_classification = {}
        # NPs to blind
        self.NP_blind = []
        # NP you want to add manually to the correlation plot of systs with >15% 
        # correlation with# signal
        self.NP_for_highSysts_cov = []
        # used to put priorities on NPs when ordering them
        self.NP_ordering = []
        # How many NP show in ranking plot by default. Can be overridden on command
        # line
        self.ranking_max_NP= 20
        # Split NPs in ranking plot in various categories
        self.ranking_classification = {}
        # Fancy names for POIs in ranking plots
        self.ranking_POI_titles = {}
        # for yield ratios only
        self.category_condenser = {}
        # To force recomputing yields/plotobjs
        self.force_recompute_yields = False
        self.force_recompute_plotobjs = False        
        self.plot_prefit_curve = True        
        self.find_optimal_yrange = True
        #This flag is to control the range of the postfit plots (0.9,1.1) and plot the ratio of the prefit over postfit. This flag only affects the postfit plots 
        self.prepost_ratio = False
        #Flag to remove gamma when ploting different bin/var than fitting
        self.remove_gamma = False
        self.set_yratio_range = False
        self.isSoBplot = False
        self.isMoneyPlot = False

    # for child classes to override
    def do_rebinning (self, prop):
        """ should do rebinning? (from binning histogram in workspace) """
        return True

    def blind_data (self, setup):
        """ 
        do blinding of data (look in plotMaker.py for Setup class details)
        eg: setup.data.blind(105, 145)
        """
        return

    def preprocess_main_content_histogram (self, hist, setupMaker):
        """ executed before rebinning """
        return hist

    def postprocess_main_content_histogram (self, prop, hist):
        """ executed after everything is drawn """
        return hist

    def postprocess_dataMC_ratio_histogram (self, prop, hist, xbounds=None):
        """ executed before arrows and titles are create (is not drawn yet) """
        return hist

    def make_sum_plots (self, func):
        """ 
        if sum plots is enabled (combining regions), specify those plots
        eg: func("Region_BMin150_T1_L0_Y2015_distMET_DSR",
                 rt=["_L0","_T1", "_distMET","_DSR"], ea=["_L2","_DmBBcr","_Dtopemucr"], bhn="Region_BMin250_T1_L0_Y2015_distMET_DSR")
            where the first argument is the name of the plot, rt is "restrict to",
            ea is "exclude any",
            bhn is the name of an histo entering the sum to recover specific binning - use "" if non-necessary
        """
        pass

    def get_run_info (self):
        """ 
        create a dictionary of the form {year : [lumi, COM energy]}
        all years in the dictionary will be printed
        """
        lumi = {}
        if self._year == "2011":
            lumi["2011"] = ["4.7", 7]
        if self._year == "2012":
            lumi["2012"] = ["20.3", 8]
        if self._year == "2015":
            lumi["2015"] = ["3.2", 13]
        return lumi

    def get_title_height (self):
        """ multiple of normal font size to make title """
        return 2

    def draw_category_ids (self, props, l, pos, nf):
        """ 
        draw region info after lumi info
        can draw more than one line
        must return position of suitable next line
        eg: l.DrawLatex(pos[0], pos[1], "SR")
            return (pos[0], pos[1] - nf)
        """
        return (pos[0], pos[1])

    def force_mu_value (self):
        """ 
        returns a (boolean, float) tuple that indicates whether to force
        an expected mu value and what that value should be
        """
        return False, 1.0

    def get_year_str (self):
        """ 
        returns the year appended to the label for the data histogram
        (can be empty)
        """
        return self._year

    def get_xbound_from_properties (self, prop):
        """ 
        if special x-axis range is desired, it can be determined here from
        the plot's properties
        if the default range is sufficient, return None
        eg: return (40, 400) if prop["dist"] == "pTB1" else None
        """
        return None

    def get_legend_pos_from_properties (self, prop):
        """ 
        if special legend position is desired, it can be determined here
        from the plot's properties
        if the default position is sufficient, return None
        eg: result = None
            if prop["L"] == '0' and prop["dist"] == "VpT":
                result = [0.155, 0.13, 0.375, 0.65]
            return result
        """
        return None

    def get_yscale_factor_from_properties (self, prop, log_scale):
        """ 
        if the y-axis scale needs a multiplicative factor, it be be
        determined here from the plot's properties
        return 1.0 if nothing should be done
        """
        return 1.0

    def get_xTitle (self, prop, data_hist):
        """ 
        determine the x-axis label from the plot's properties and the data
        histogram
        """
        return ""

    def get_yTitle_tag (self, prop, data_hist):
        """ 
        the y-axis label is simply "Events" by default
        if an additional unit is needed (i.e. " / 200 GeV"), it can be
        determined here from the plot's properties and the data
        histogram
        return "" if nothing should be added
        be sure to add an additional space at the beginning
        """
        return ""

    def set_y_range (self, hist, nlegend_items, miny, total_miny, maxy, log_scale, prop):
        """ 
        the y-axis range can be set here if necessary
        the minimum and maximum values of the of the contents of the
        stack are given as well as the number of legend entries
        """
        pass

    def auto_compute_ratio_yscale_from_properties (self, prop):
        """ 
        force the y-axis on the data/MC ratio subplot to be automatically
        determined from its content (this is already done in most
        circumstances - this is just here to force it to happen if you
        notice that it's not happening by default)
        """
        return False

    def scale_all_yvals(self, prop):
        """ 
        if the y-values of the pltos need to be scaled, it can be determined
        here from the from the plot's properties
        should return a (boolean, float) tuple indicating whether to scale
        and by how much
        """
        return False, 0.05

    def fine_tune_additional_signal_mult_factor (self, dist, prop, current_mult_factor):
        """
        Fine tuning (reg dependent for e.g.) of the multiplication-factor for processes (signal only ?)
        """
        return current_mult_factor

    def determine_year_from_title (self, title):
        """ 
        determine the year from the histogram title - this will be stored
        in self._year
        """
        return re.findall(r'Y(\d*)',title)[0]

    def add_additional_signal_info_to_legend (self, legend, signal):
        """ 
        this information will appear beneath the signal title in the legend
        """
        pass

    def dropping_list_in_legend (self, prop):
        """ 
        the list is used to drop a particular bkg when generate the legends
        """
        DropList = []
        return DropList

    # Functions used for pull and ranking plots

    def get_NP_name_for_ordering(self, oldname):
        """Allows to change NP names before ordering them
        Typically useful to add padding for JES or FTAG EVs"""
        return oldname

    def get_ranking_NP_name(self, oldname):
        """Return nicely formatted NP name for public ranking plot"""
        return oldname

    def get_nice_NP_name(self, oldname):
        """Return nicely formatted NP name for pull plots"""
        return oldname

    # hidden, for experts only
    def _save_yields(self):
        os.system(f"rm -f {self._yieldsfile}")
        f = open(self._yieldsfile, "wb")
        pickle.dump(copy.deepcopy(self._yields), f)
        f.close()

    def _read_yields(self):
        if os.path.isfile(self._yieldsfile):
            if self.force_recompute_yields:
                os.remove(self._yieldsfile)
                print( "Forced regeneration of yields file")
                yields = {}
            else:
                f = open(self._yieldsfile, "rb")
                yields = pickle.load(f)
                f.close()
        else:
            print( "Yields file does not exist yet... Generate it.")
            yields = {}
        self._yields = yields

    def _save_plot_objs(self):
        if self._plot_objs is not None:
            os.system(f"rm -f {self._plot_objs_file}")
            f = open(self._plot_objs_file, "wb")
            pickle.dump(copy.deepcopy(self._plot_objs), f)
            f.close()

    def _read_plot_objs(self):
        if os.path.isfile(self._plot_objs_file):
            if self.force_recompute_plotobjs:
                os.remove(self._plot_objs_file)
                print( "Forced regeneration of plot objs file")
                plot_objs = {}
            else:
                f = open(self._plot_objs_file, "rb")
                plot_objs = pickle.load(f)
                f.close()
        else:
            print( "Plot objs file does not exist yet... Generate it.")
            plot_objs = {}
        self._plot_objs = plot_objs

    def _reset(self):
        self._yields = None
        self._comps = None
