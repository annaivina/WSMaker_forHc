import re
import logging
import ROOT
import plottingConfig as cfg
import os

moneyPlot=False # True #
pTVsum=True # False #

vh_fit=False
hc_fit = True
vh_cba=False
if moneyPlot :
    vh_cba=True

class Config(cfg.PlottingConfig):

    def __init__ (self, options):
        self.options = options
        super(Config, self).__init__()
        
        if moneyPlot:
            self.isMoneyPlot = True
        # BEWARE: fixing mu to 1 !!!!!
        self.force_mu = (False, 1) # SM VH
        if vh_cba :
            self.force_mu = (True, 1.17) #Full Run2 mbb-analysis - 2020

        # for child classes to use
        # self.loggingLvl = logging.INFO
        self.dataname='obsData'
        self.loggingLvl = logging.DEBUG
        self.verbose = False
        self.formats = [ 'pdf', 'png' ] #, 'C' ]
        Blinding = os.getenv("IS_BLINDED")
        self.blind = "1" in Blinding
        self.generate_pseudodata = False
        self.find_optimal_yrange = False
        self.thresh_drop_legend = 0.01
        self.restrict_to = []
        self.excludes = []
        self.additionalPlots = []
        self.add_sig_to_ratio_plot = True
        self.use_exp_sig = False
        self.atlas_rounding = True
        #This flag is to control the range of the postfit plots (0.9,1.1) and plot the ratio of the prefit over postfit. This flag only affects the postfit plots 
        self.prepost_ratio = False
        # flag to adjust the y-axis in the lower pad. Only for VHbb Resolved
        self.set_yratio_range = True
        # flag to have pTv binning as 75-150-250-400 and make sum pTV plot
        self.pTVin3bins = True
        # flag to know if running SoB plot
        self.isSoBplot = False 
        # self.transferResults_fitName = "HiggsNorm"
        # self.get_binning_hist_removal = ["_meas2l2q2v2q"]
        self.file_tags = ["B", "Y", "L", "J", "T", "TType", "Flv", "Sgn", "isMVA", "dist", "Spc", "D", "nAddTag", "BMax", "BMin", "Fat", "incFat", "incJet", "incAddTag"] #'B' is the Run1 binning convention (lo,lo+loMET,hi pTV)
        self.weight_tags = ["Higgsweighted", "Dibosonweighted"]
        self.sig_names = ["VH",'Hc', "VHSTXS"] if vh_fit else ["VZ"]
        if vh_fit:
            self.signal = ["VH, H #rightarrow b#bar{b}", self._STACK, ROOT.kRed + 1, 1] # last = mult factor
            self.additional_signal = ["VH, H #rightarrow b#bar{b}", self._OVERPRINT, ROOT.kRed +1, 50.]
            self.expected_signal = ["VH(bb) (#mu=1.0)", self._STACK, ROOT.kRed +1, self.force_mu[1]] # last = expected mu
            self.bkg_substr_name = "Diboson"
            self.bkg_substr_list = ["diboson", "Diboson", "WZ", "ZZ", "VZ", "allZZ", "ggZZ"]
            if moneyPlot :
                self.bkg_substr_list = []
        
        if hc_fit:
            self.signal = ["H+c, H#rightarrow#gamma#gamma", self._STACK, ROOT.kBlue, 1] # last = mult factor

        else:
            self.signal = ["VZ, Z #rightarrow b#bar{b}", self._STACK, ROOT.kGray + 1, 1] # last = mult factor
            self.additional_signal = ["VZ, Z #rightarrow b#bar{b}", self._OVERPRINT, ROOT.kGray +1, 50.]
            #self.signal = ["VZ #rightarrow Vbb", self._STACK, ROOT.kGray + 1, 1] # last = mult factor
            #self.additional_signal = ["SM VZ #rightarrow Vbb", self._OVERPRINT, ROOT.kGray + 1, 50.]
            self.expected_signal = ["VZbb", self._STACK, ROOT.kGray +1, self.force_mu[1]] # last = expected mu
            self.bkg_substr_name = "VH125"
            self.bkg_substr_list = ["VH125"]
        self.bkg_tuple = {
                'ttbar': ("t#bar{t}", 42, ROOT.kOrange, []),
                'stopt': ("t, s+t chan", 41, ROOT.kOrange - 1, ["stops"]),
                'stops': ("t, s+t chan", 41, ROOT.kOrange - 1, ["stopt"]),
                'stopWt': ("Wt", 40, ROOT.kYellow - 7, []),
                'stop': ("Single top", 40, ROOT.kOrange - 1, []),
                'emuCRData': ("Top", 42, ROOT.kOrange - 3, []),
                'emuCRSumMC': ("Sum of e#mu-CR MCs", 42, ROOT.kOrange - 3, []),
                'VH125': ("VH", 49, ROOT.kRed - 6, ['VH125','ZllH125','ZvvH125','WlvH125']), #dangerous, I know, but if VH125, other samples shouldn't be there
                'Zbb': ("Z+bb", 25, ROOT.kAzure + 3, []),
                'Zbc': ("Z+bc", 24, ROOT.kAzure + 2, []),
                'Zclbl': ("Z+(bl,cl)", 23, ROOT.kAzure + 1, []),
                'Zbl': ("Z+bl", 23, ROOT.kAzure + 1, []),
                'Zcl': ("Z+cl", 21, ROOT.kAzure - 8, []),
                'Zcc': ("Z+cc", 22, ROOT.kAzure - 4, []),
                'Zhf': ("Z+(bb,bc,cc,bl)", 22, ROOT.kAzure + 2, []),
                'Zl': ("Z+ll", 20, ROOT.kAzure - 9, []),
                'Wbl': ("W+bl", 33, ROOT.kGreen + 2, []),
                'Wbb': ("W+bb", 35, ROOT.kGreen + 4, []),
                'Wbc': ("W+bc", 34, ROOT.kGreen + 3, []),
                'Wcc': ("W+cc", 32, ROOT.kGreen + 1, []),
                'Whf': ("W+(bb,bc,cc,bl)", 32, ROOT.kGreen + 3, []),
                'Wcl': ("W+cl", 31, ROOT.kGreen - 6, []),
                'Wl': ("W+ll", 30, ROOT.kGreen - 9, []),
                'VZ': ("VZ", 51, ROOT.kGray + 1, ['ZZ','WZ','allZZ','ggZZ']),
                'WZ': ("WZ", 53, ROOT.kGray + 1, ["WZ"]),
                'diboson': ("Diboson", 51, ROOT.kGray + 1, []),
                'Diboson': ("Diboson", 50, ROOT.kGray + 1, []),
                'ZZ': ("ZZ", 52, ROOT.kGray + 1, ["ZZ","ggZZ","allZZ"]),
                'WW': ("WW", 50, ROOT.kGray + 3, []),
                'multijetEl': ("Multijet", 39, ROOT.kViolet-9, ["multijetMu", "multijet"]),
                'multijetMu': ("Multijet", 39, ROOT.kViolet-9, ["multijetEl", "multijet"]),
                # specific stuff for pretty S/B plot
                'bkg': ("Background", 10, ROOT.kGray+1, [])}
        W_Z_merged=1
        if (W_Z_merged):
            self.bkg_tuple.update({
                'W' : ("W+jets",37, ROOT.kGreen+3,["Whf","Wl","Wcl"]),
                'Whf' : ("W+jets",37, ROOT.kGreen+3,["Wjets","Wl","Wcl"]),
                'Wl' : ("W+jets",37, ROOT.kGreen+3,["Whf","Wjets","Wcl"]),
                'Wcl' : ("W+jets",37, ROOT.kGreen+3,["Whf","Wl","Wjets"]),
                'Z' : ("Z+jets",27, ROOT.kAzure+2,["Zhf","Zl","Zcl"]),
                'Zhf' : ("Z+jets",27, ROOT.kAzure+2,["Zjets","Zl","Zcl"]),
                'Zl' : ("Z+jets",27, ROOT.kAzure+2,["Zhf","Zjets","Zcl"]),
                'Zcl' : ("Z+jets",27, ROOT.kAzure+2,["Zhf","Zl","Zjets"]),
                })
        else:
            self.bkg_tuple.update({
                'Whf': ("W+(bb,bc,cc,bl)", 32, ROOT.kGreen + 3, []),
                'Wcl': ("W+cl", 31, ROOT.kGreen - 6, []),
                'Wl': ("W+ll", 30, ROOT.kGreen - 9, []),
                'Zhf': ("Z+(bb,bc,cc,bl)", 22, ROOT.kAzure + 2, []),
                'Zcl': ("Z+cl", 21, ROOT.kAzure - 8, []),
                'Zl': ("Z+ll", 20, ROOT.kAzure - 9, []),
                    })
        self.ATLAS_suffix = "Internal"
        # self.ATLAS_suffix = "Simulation"
        #self.ATLAS_suffix = "Preliminary"
        #self.ATLAS_suffix = ""
        # for yields
        self.make_slides = False
        self.window = None
        self.priorities = {
        "data" : 80,
        "S/sqrt(S+B)" : 73,
        "S/B" : 72,
        "Bkg" : 60,
        "MC" : 75,
        "SignalExpected" : 71,
        "Signal" : 70,
        "VHSTXS" : 57,
        "VH125" : 57,
        "WlvH125" : 57,
        "qqWlvH125" : 57,
        "qqZvvH125" : 56,
        "qqZllH125" : 55,
        "ggZvvH125" : 54,
        "ggZllH125" : 53,
        "ttbar" : 45,
        "stop" : 40,
        "stopWt" : 40,
        "stopt" : 41,
        "stops" : 42,
        "emuCRData" : 45,
        "emuCRSumMC" : 45,
        "Tops" : 46,
        "Z" : 28,
        "Zjets" : 28,
        "Zhf" : 27,
        "Zbb" : 27,
        "Zbc" : 26,
        "Zcc" : 25,
        "Zbl" : 24,
        "Zcl" : 21,
        "Zl" : 20,
        "W" : 38,
        "Wjets" : 38,
        "Whf" : 37,
        "Wbb":37,
        "Wbc":36,
        "Wcc":35,
        "Wbl":34,
        "Wcl" : 32,
        "Wl" : 30,
        "diboson" : 50,
        "ZZ": 49,
        "ggZZ": 49,
        "allZZ": 49,
        "WZ": 50,
        "WW": 51,
        "VZ": 52,
        "multijet" : 55,
        "multijetEl" : 55,
        "multijetMu" : 56,
        }
        self.yTabGrps = {
            "Wjets" : {"Whf","Wcl","Wl"},
            "Zjets" : {"Zhf","Zcl","Zl"},
            "Tops" : {"ttbar","stop","emuCRData"},
            "multijet" : {"multijetEl","multijetMu"}
        }
        # for reduced diag plots only
        self.exclude_str = 'HiggsNorm'
        self.cov_classification = {
        "BTag": [False, ["SysFT_EFF_Eigen", "SysFT_EFF_extrapolation"], []],
        #"Top": [False, ["SysWt", "SysTop", "SysTtbar", "SysMVH"], []],
        "Top": [False, ["TTbar", "ttbar", "stop", "Stop"], ["JET_Flav"]],
        #"ModelBoson": [False, ["SysVV", "SysWM","SysZM","SysWD","SysZD","SysWP","SysZP","SysVj"], []],
        "Norm": [False, ["Norm","Ratio"], []],
        "FloatNorm": [False, ["norm"], []],
        "Lepton": [False, ["SysMUON","SysEL","SysEG"], []],
        "Jet": [False, ["SysJET","FATJET"], []],
        "MET": [False, ["SysMET"], []],
        "LUMI": [False, ["LUMI"], []],
        "Wjets": [False, ["WMbb","WPtV","BDTr_W_SHtoMG5","Wbb","Wbc","Wbl","Wcc","Wcl","Wl"], []],
        "Zjets":[False, ["ZMbb","ZPtV","Zbb","Zbc","Zbl","Zcc","Zcl","Zl"], []],
        "MJ":[False, ["MJ"], []],
        "Diboson":[False, ["WZ","ZZ","WW","VZ","SysVV"], []],
        "VH":[False, ["VH","Theory"], []],
        "DDttbar":[False,["MCStat"], [], True],
        "Gammas":[False, ["bin"], ["MCStat"]],
        "GammasL2":[False, ["L2_Y", "L2_inc"], ["MCStat"]],
        "GammasL1":[False, ["L1_Y", "L1_inc"], []],
        "GammasL1":[False, ["L0_Y", "L0_inc"], []],
        #"Shifted": [True, [], ["blablabla"]]
        }
        self.cov_special = {
        #"noMCStat": [[], ["gamma"]],
        "SignalStrength": [["SigX"], []],
        #"JES": [["SigX", "norm_", "Jet"], []],
        "BTag": [["SigX", "norm_", "BTag"], []],
        #"Mbb": [["SigX", "norm_", "Mbb"], []],
        #"Modelling": [["SigX", "norm_", "Norm", "Ratio", "PtBi"], []],
        #"SF": [["SigX", "norm_"], []],
        "Norm": [["3JNorm", "norm_", "Norm", "Ratio"], []],
        "EFT": [["E0", "E1", "E2", "E3", "E4"], []]
        }
        self.cov_blind = ["VH", "Theory", "QCDScaleDelta", "HiggsNorm"]
        self.syst_to_study = ["JetEResol", "Mbb_Whf", "V_Whf", "METScale", "TChanP",
        "ttbarHigh", "BJetReso", "ZblZbb", "BTagB1", "norm_Wbb", "WblWbbRatio"]
        self.suspicious_syst = ["norm_"]
        # for yield ratios only
        self.category_condenser = {
        # "_HistSyst": ["_Exp", False],
        # "_dist(mva|mjj)": ["_dist", False],
        # "_distMV1cBTag": ["_dist", False],
        #"_distmV": ["_dist", False],
        # "_isMVA[01]": ["_isMVA", False],
        # "_B[0-5]_": ["_B9_", False],
        #"_B(Max500_BMin0|BMin500)_": ["_Bresolvedmerged_", False],
        # "_TType(ll|mm|tt|xx)": ["_TType", False],
        #"_T[012]": ["_Tx", False],
        #"_(incJet1_J|incFat1_Fat|J)[1235]": ["_Jx", False],
        # "_Spc[0-9a-z]*top[a-z]*cr": ["_TType", False],
        # "(multijet)(.*_L)([0123])(.*)": [r'MJ\3lep\2\3\4', False],
        #"_L[012]": ["_Lx", False],
        "_D(SR|topemucr)": ["_DallRegions", False],
        # "_W(bb|bl|bc|cc)_": ["_Whf_", True],
        # "_Z(bb|bl|bc|cc)_": ["_Zhf_", True]
        }
        self.EFT_operator_labels = {"cHW": "Q_{HW}", "cHq3": "Q_{Hq}^{(3)}", "cHB": "Q_{HB}", "cHq1": "Q_{Hq}^{(1)}", "cHd": "Q_{Hd}", "cHDD": "Q_{HDD}",
                                    "cHl1": "Q_{Hl}^{(1)}", "cHbox": "Q_{H#Box}", "cHl3": "Q_{Hl}^{(3)}", "cll1": "Q_{ll}^{(1)}", "cHWB": "Q_{HWB}", "cHu": "Q_{Hu}"}
        self.EFT_lambda = 1 # in TeV

        logging.basicConfig(format='%(levelname)s in %(module)s: %(message)s', level=self.loggingLvl)

    def do_rebinning (self, prop):
        # NOTE: JWH - ED board requests
        #if prop["dist"] == "mVH":
        #    if "mBBcr" in prop["D"] or "topemucr" in prop["D"]:
        #        if prop["L"] == "2" or prop["L"] == "0":
        #            if prop.get("incFat", "-1") == "1" or prop.get("incJet", "-1") == "1":
        #                return False
        #    if "SR" in prop["D"]:
        #        if prop["L"] == "2" or prop["L"] == "0":
        #            if prop.get("incFat", "-1") == "1":
        #                return False
        #            if prop["L"] == "0":
        #                return False
        if (prop["dist"] == "mva" or prop["dist"] == "mvadiboson"):
            return False
        else:
            return True

    def is_signal(self, compname):
        """ Check if a component is Higgs. If yes, return mass """
        # Spyros: Add ggA to list of signal names - has to be first in list otherwise we get problems
        signames = self.sig_names
        has_mass = False
        mass = ""
        # Spyros: if sg in compname matches also mVH so doesn't work for resonance analyses
        # remove mVH from compname
        compname = re.sub('mVH', '', compname)
        for sg in signames:
            if sg in compname:
                has_mass = True
                pos = compname.find(sg) + len(sg)
                try:
                    mass = int(re.sub("[^0-9]", "", compname[pos:pos + compname[pos:].find('_')]))
                except:
                    mass = 0
                break
        return has_mass, mass

    def determine_additional_plots_from_properties (self, prop):
        if prop["D"] == "topemucr":       return False
        if prop["D"] == "WhfCR":          return False
        if prop["dist"] == "MEff" :       return True
        if prop["dist"] == "HT" :         return True
        if prop["dist"] == "MEff3" :      return True
        if prop["dist"] == "MET" :        return True
        if prop["dist"] == "METSig" :     return True
        if prop["dist"] == "softMET" :    return True
        if prop["dist"] == "mLL" :        return True
        if prop["dist"] == "mTW" :        return True
        if prop["dist"] == "pTB1" :       return True
        if prop["dist"] == "pTB2" :       return True
        if prop["dist"] == "pTJ3" :       return True
        if prop["dist"] == "pTV" :        return True
        if prop["dist"] == "VpT" :        return True
        if prop["dist"] == "mva" :        return True
        if prop["dist"] == "Mtop" :       return True
        if prop["dist"] == "dYWH" :       return True
        if prop["dist"] == "mvadiboson" : return True
        if prop["dist"] == "mjj" :        return True
        if prop["dist"] == "mBB" :        return True
        if prop["dist"] == "mBBMVA" :     return True
        if prop["dist"] == "mBBJ" :       return True
        if prop["dist"] == "mBBJ3" :      return True
        if prop["dist"] == "MV1cB1" :     return True
        if prop["dist"] == "MV1cB2" :     return True
        if prop["dist"] == "MV1cBTag" :   return True
        if prop["dist"] == "dEtaBB" :     return True
        if prop["dist"] == "dEtaVBB"  :   return True
        if prop["dist"] == "dPhiLBmin" :  return True
        if prop["dist"] == "dPhiVBB" :    return True
        if prop["dist"] == "dRBB" :       return True
        if prop["dist"] == "binMV2c10B1B2" : return True
        if prop["dist"] == "cosThetaLep" :   return True
        return False

    def blind_data (self, setup):
        def _do_blinding (title):
            return "T2" in title, [80, 140]

        do_blinding, blind_range = _do_blinding(setup.title)
        #(1) mva: blind 60% of signal from right.

        if not do_blinding:
            return

        if "mva" in setup.title and ("Dtopemucr" not in setup.title) :
            for i in range(1, setup.sig.h.GetNbinsX()+1):
                if setup.sig.h.GetBinContent(i) > 0:
                    sos = setup.sig.h.Integral(i, setup.sig.h.GetNbinsX()+1) / ( setup.sig.h.Integral(0, setup.sig.h.GetNbinsX()+1) )
                    if sos <= 0.6:
                        setup.data.blind(setup.hsum.GetBinLowEdge(i), setup.hsum.GetBinLowEdge((setup.sig.h.GetNbinsX()+1)+1))
                        break
            # WORKING ALTERNATIVE: CUT ON S/(S+B)
            #for i in range(1, setup.hsum.GetNbinsX()+1):
            #    if setup.hsum.GetBinContent(i) > 0:
            #        sob = setup.sig.h.GetBinContent(i) / ( setup.sig.h.GetBinContent(i) + setup.hsum.GetBinContent(i) )
            #        if sob > 0.05:
            #            setup.data.blind(setup.hsum.GetBinLowEdge(i), setup.hsum.GetBinLowEdge(i+1))
            #    elif setup.sig.h.GetBinContent(i) > 0:
            #        setup.data.blind(setup.hsum.GetBinLowEdge(i), setup.hsum.GetBinLowEdge(i+1))
            #
        #(2) mass: blind 80 -- 140 GeV
        elif "mBB" in setup.title and ("DSR" in setup.title or "DWhfSR" in setup.title) and "mBBJ" not in setup.title:
            # blind entire range
            if blind_range[0] == 0 and blind_range[1] == 0:
                blind_range[0] = setup.data.h.GetXaxis().GetXmin()
                blind_range[1] = setup.data.h.GetXaxis().GetXmax()
            setup.data.blind(blind_range[0], blind_range[1])
        #(3) others: blind s/b > 5%
        elif  "Dtopemucr" not in setup.title:
            for i in range(1, setup.hsum.GetNbinsX()+1):
              if setup.hsum.GetBinContent(i) > 0:
                sob = setup.sig.h.GetBinContent(i) / ( setup.sig.h.GetBinContent(i) + setup.hsum.GetBinContent(i) )
                if sob > 0.05:
                  setup.data.blind(setup.hsum.GetBinLowEdge(i), setup.hsum.GetBinLowEdge(i+1))

    def preprocess_main_content_histogram (self, hist, setupMaker):
        return hist
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
        #
        # new_hist = hist
        # props = sm.setup.properties
        # if props:
        #     # Changes for MeV/GeV
        #     affected_dists = ["MEff", "MEff3", "MET", "mLL", "mTW", "pTB1", "pTB2", "pTJ3", "pTV", "mBB", "mBBJ"]
        #     if props["L"] == "1" and props["dist"] in affected_dists:
        #         new_hist = change_MeV_GeV(hist)
        #
        # return new_hist

    def make_sum_plots (self, func):

        if pTVsum and not moneyPlot:
            func("Region_BMin0_Y6051_DCRLow_T2_L0_distMET_J2", rt=['_distMET',"_L0", "_DCRLow", "_J2"],ea=[],bhn="Region_BMin250_Y6051_DCRLow_T2_L0_distMET_J2")
            func("Region_BMin0_Y6051_DCRLow_T2_L0_distMET_J3", rt=['_distMET',"_L0", "_DCRLow", "_J3"],ea=[],bhn="Region_BMin250_Y6051_DCRLow_T2_L0_distMET_J3")
            func("Region_BMin0_Y6051_DCRHigh_T2_L0_distMET_J2", rt=['_distMET',"_L0", "_DCRHigh", "_J2"],ea=[],bhn="Region_BMin250_Y6051_DCRHigh_T2_L0_distMET_J2")
            func("Region_BMin0_Y6051_DCRHigh_T2_L0_distMET_J3", rt=['_distMET',"_L0", "_DCRHigh", "_J3"],ea=[],bhn="Region_BMin250_Y6051_DCRHigh_T2_L0_distMET_J3")
            func("Region_BMin0_Y6051_DSR_T2_L0_distMET_J2", rt=['_distMET',"_L0", "_DSR", "_J2"],ea=[],bhn="Region_BMin250_Y6051_DSR_T2_L0_distMET_J2")
            func("Region_BMin0_Y6051_DSR_T2_L0_distMET_J3", rt=['_distMET',"_L0", "_DSR", "_J3"],ea=[],bhn="Region_BMin250_Y6051_DSR_T2_L0_distMET_J3")

            func("Region_BMin0_Y6051_DCRLow_T2_L1_distpTV_J2", rt=['_distpTV',"_L1", "_DCRLow", "_J2"],ea=[],bhn="Region_BMin250_Y6051_DCRLow_T2_L1_distpTV_J2")
            func("Region_BMin0_Y6051_DCRLow_T2_L1_distpTV_J3", rt=['_distpTV',"_L1", "_DCRLow", "_J3"],ea=[],bhn="Region_BMin250_Y6051_DCRLow_T2_L1_distpTV_J3")
            func("Region_BMin0_Y6051_DCRHigh_T2_L1_distpTV_J2", rt=['_distpTV',"_L1", "_DCRHigh", "_J2"],ea=[],bhn="Region_BMin250_Y6051_DCRHigh_T2_L1_distpTV_J2")
            func("Region_BMin0_Y6051_DCRHigh_T2_L1_distpTV_J3", rt=['_distpTV',"_L1", "_DCRHigh", "_J3"],ea=[],bhn="Region_BMin250_Y6051_DCRHigh_T2_L1_distpTV_J3")
            func("Region_BMin0_Y6051_DSR_T2_L1_distpTV_J2", rt=['_distpTV',"_L1", "_DSR", "_J2"],ea=[],bhn="Region_BMin250_Y6051_DSR_T2_L1_distpTV_J2")
            func("Region_BMin0_Y6051_DSR_T2_L1_distpTV_J3", rt=['_distpTV',"_L1", "_DSR", "_J3"],ea=[],bhn="Region_BMin250_Y6051_DSR_T2_L1_distpTV_J3")

            func("Region_BMin0_Y6051_DCRLow_T2_L2_distpTV_J2", rt=['_distpTV',"_L2", "_DCRLow", "_J2"],ea=[],bhn="Region_BMin250_Y6051_DCRLow_T2_L2_distpTV_J2")
            func("Region_BMin0_incJet1_Y6051_DCRLow_T2_L2_distpTV_J3", rt=['_distpTV',"_L2", "_incJet1", "_DCRLow", "_J3"],ea=[],bhn="Region_BMin250_incJet1_Y6051_DCRLow_T2_L2_distpTV_J3")
            func("Region_BMin0_Y6051_DCRHigh_T2_L2_distpTV_J2", rt=['_distpTV',"_L2", "_DCRHigh", "_J2"],ea=[],bhn="Region_BMin250_Y6051_DCRHigh_T2_L2_distpTV_J2")
            func("Region_BMin0_incJet1_Y6051_DCRHigh_T2_L2_distpTV_J3", rt=['_distpTV',"_L2", "_incJet1", "_DCRHigh", "_J3"],ea=[],bhn="Region_BMin250_incJet1_Y6051_DCRHigh_T2_L2_distpTV_J3")
            func("Region_BMin0_Y6051_DSR_T2_L2_distpTV_J2", rt=['_distpTV',"_L2", "_DSR", "_J2"],ea=[],bhn="Region_BMin250_Y6051_DSR_T2_L2_distpTV_J2")
            func("Region_BMin0_incJet1_Y6051_DSR_T2_L2_distpTV_J3", rt=['_distpTV',"_L2", "_incJet1", "_DSR", "_J3"],ea=[],bhn="Region_BMin250_incJet1_Y6051_DSR_T2_L2_distpTV_J3")

            #merge pTV into one plot
            for nJet in ['2','3']:
                func("Region_BMin0_T2_L2_J{}_Y6051_distpTV_DSR".format(nJet), rt=['_distpTV',"_L2", "_DSR", "_J{}".format(nJet)],ea=[],bhn="Region_BMin250_Y6051_DSR_T2_L2_distpTV_J2")
                func("Region_BMin0_T2_L2_J{}_Y6051_distpTV_Dtopemucr".format(nJet), rt=['_distpTV',"_L2", "_Dtopemucr", "_J{}".format(nJet)],ea=[],bhn="Region_BMin250_Y6051_Dtopemucr_T2_L2_distpTV_J2")

        if not pTVsum:
            func("Region_BMin75_J23_T2_L3_Y6051_distmBB_DSR", rt=["_T2","SR"], ea=[],bhn="")

        return

    def get_run_info (self):
        lumi = {}
        if self._year == "4023":
            lumi["2011"] = ["4.7", 7]
            lumi["2012"] = ["20.3", 8]
        elif self._year == "2011":
            lumi["2011"] = ["4.7", 7]
        elif self._year == "2012":
            lumi["2012"] = ["20.3", 8]
        elif self._year == "2015":
	          #lumi["2015"] = ["3.2", 13]
            lumi["2015"] = ["36.1", 13]
        elif self._year == "2016":
            lumi["2016"] = ["36.2", 13]
        elif self._year == "2017":
            lumi["2017"] = ["43.6", 13]
        elif self._year == "4033":
            lumi["2017"] = ["79.8", 13]
        elif self._year == "2018":
            lumi["2018"] = ["58.5", 13]
        elif self._year == "6051":
            lumi["2018"] = ["140", 13]
        return lumi

    def get_title_height (self):
        return 3.5 if self._year == "4023" else 2

    def draw_category_ids (self, props, l, pos, nf):

        merged = False
        plural_jets = False
        nf += 0.25*nf # a bit more vertical spacing

        nleps = props.get("L", "-100")
        if nleps == '3':
            nleps = "0+1+2"
        njets = props.get("J", "-1")
        nincjets = props.get("incJet", "-1")
        if njets == "23":
            plural_jets = True
            njets = "2+3"
        elif nincjets == '1':
            plural_jets = True
            # njets += '+'
            njets = '#geq {}'.format(njets)
        elif int(njets) > 1:
            plural_jets = True
        nfatjets = props.get("Fat", "-1")
        nincfatjets = props.get("incFat", "-1")
        if int(nfatjets) > 0 and nincfatjets == '1':
            plural_jets = True
            merged = True
            # nfatjets += '+'
            nfatjets = '#geq {}'.format(nfatjets)
            # nfatjets += ' #leq'
        elif int(nfatjets) > 1:
            plural_jets = True
        ntags = props.get("T", "-100")

        region = ""
        regionline2 = ""

        if nleps == "0+1+2":
            if not nleps == '-100':
                if len(region) > 0:
                    region += ', '
                region += "{} leptons".format(nleps)
            if not njets == '-1' or not nfatjets == '-1':
                if len(regionline2) > 0:
                    regionline2 += ', '
                regionline2 += "{} {}jet{}".format(nfatjets if merged else njets,
                                                   "large-R " if merged else "",
                                                   "s" if plural_jets else "")
            if not ntags == '-100':
                if len(regionline2) > 0:
                    regionline2 += ', '
                regionline2 += "{} b-tag{}".format(ntags,
                                                   "s" if not int(ntags) == 1 else "")



        else:
            if not nleps == '-100':
                if len(region) > 0:
                    region += ', '
                if nleps == '2':
                    region += "{} leptons".format(nleps)
                else:
                    region += "{} lepton".format(nleps)
            if not njets == '-1' or not nfatjets == '-1':
                if len(region) > 0:
                    region += ', '
                region += "{} {}jet{}".format(nfatjets if merged else njets,
                                              "large-R " if merged else "",
                                              "s" if plural_jets else "")
            if not ntags == '-100':
                if len(region) > 0:
                    region += ', '
                region += "{} b-tag{}".format(ntags,
                                              "s" if not int(ntags) == 1 else "")


        pTVBin = ""
        pTVmin = props.get("BMin", "-999")
        pTVmax = props.get("BMax", "-999")
        if not pTVmin == "-999" and pTVmax == "-999" and not pTVmin == "0":
            pTVBin = "p_{{T}}^{{V}} #geq {0} GeV".format(pTVmin)
        elif (pTVmin == "0" or pTVmin == "-999") and not pTVmax == "-999":
            pTVBin = "p_{{T}}^{{V}} < {0} GeV".format(pTVmax)
        elif not pTVmin == "-999" and not pTVmax == "-999":
            pTVBin = "{0} GeV #leq p_{{T}}^{{V}} < {1} GeV".format(pTVmin, pTVmax)

        signalControl = props.get("D", "")
        if not signalControl == "":
            def add_strings (base, addition):
                if base == "":
                    return addition
                else:
                    return base + ", " + addition
            temp = signalControl
            signalControl = ""
            reduce_SR_CR_mBB = props["dist"] == "pTV" or props["dist"] == "MET"
            if "topemucr" in temp:
                signalControl = add_strings(signalControl, "e#mu CR")
                temp = temp.replace("topemucr", "")
            if "WhfCR" in temp:
                signalControl = add_strings(signalControl, "W+HF CR")
                temp = temp.replace("WhfCR", "")
            if "CRHigh" in temp:
                signalControl = add_strings(signalControl, "High #DeltaR CR")
                temp = temp.replace("CRHigh", "")
            if "CRLow" in temp:
                signalControl = add_strings(signalControl, "Low #DeltaR CR")
                temp = temp.replace("CRLow", "")



        pos_next = pos[1] - 0.1*nf # a bit more spacing

        if regionline2 is not "":
            detailtype = "VH #rightarrow ll/l#nu/#nu#nu bb"
            analtype = "Dijet mass analysis"
            # comment next line and uncomment bottom two of this block to get background subtracted plot on bottom pad

            if not moneyPlot :
                l.DrawLatex(0.575, pos_next -(1.75*nf) - 0.01, analtype)
            l.DrawLatex(pos[0], pos_next, region)
            pos_next -= nf # nfd
            l.DrawLatex(pos[0], pos_next, regionline2)
            if moneyPlot :
                pos_next -= nf # nfd
                l.DrawLatex(pos[0], pos_next, analtype)

        else:
            l.DrawLatex(pos[0], pos_next, region)
            if not pTVBin == "":
                pos_next -= nf
                l.DrawLatex(pos[0], pos_next, pTVBin)
            if not signalControl == "":
                pos_next -= nf
                l.DrawLatex(pos[0], pos_next, signalControl)

        pos_next -= nf
        return (pos[0], pos_next)

    def force_mu_value (self):
        return self.force_mu

    def get_year_str (self):
        return self._year if int(self._year) < 2015 else ""

    def fine_tune_additional_signal_mult_factor (self, dist, prop, current_mult_factor):
        pTVmin = prop.get("BMin", "-999")
        logging.debug("The org mult factor is {}".format(current_mult_factor))
        if dist == "mBB"       : current_mult_factor /= 8
        if dist == "mBBMVA"       : current_mult_factor /= 8
        if dist == "mLL"       : current_mult_factor /= 2
        if dist == "pTB1"       : current_mult_factor /= 2
        if dist == "pTJ3"       : current_mult_factor /= 2
        if dist == "dEtaBB"    : current_mult_factor /= 4
        if dist == "dEtaVBB"   : current_mult_factor /= 2
        if dist == "Mtop"      : current_mult_factor /= 4
        if dist == "dYWH"      : current_mult_factor /= 2
        if dist == "dPhiLBmin" : current_mult_factor /= 4
        if dist == "dPhiVBB"   : current_mult_factor /= 4
        if dist == "mjj"       : current_mult_factor /= 2
        if dist == "mva"       : current_mult_factor /= 2
        if dist == "mvadiboson": current_mult_factor /= 2
        if dist == "mBBJ"      : current_mult_factor /= 2
        if dist == "mBBJ3"     : current_mult_factor /= 2
        if dist == "dRBB"      : current_mult_factor /= 2
        if dist == "cosThetaLep"      : current_mult_factor /= 2
        if dist == "mva" and prop["L"] == "0" : current_mult_factor *= 0.8
        if dist == "MV1cBTag" : current_mult_factor *= 0.5
        # do current_mult_factor rounded
        current_mult_factor = int(current_mult_factor)
        if current_mult_factor > 9 :
            tmp_new_mult_factor = current_mult_factor%10
            if tmp_new_mult_factor != 0 :
                if tmp_new_mult_factor < 5 : current_mult_factor = current_mult_factor - tmp_new_mult_factor
                else                       : current_mult_factor = current_mult_factor + (30 - tmp_new_mult_factor)
        else :
            if current_mult_factor > 4 : current_mult_factor = 5
            elif current_mult_factor > 1 : current_mult_factor = 2
            else : current_mult_factor = 1
        # turning for paper: FIXME temp solution Changqiao
        if dist == "mva" and prop["L"] == "1" :
            if current_mult_factor > 100: current_mult_factor = 100
            #if (prop["J"] == "2" ) and (prop["D"] == "WhfSR") : current_mult_factor = 15

        if dist == "mvadiboson" :
            if (prop["L"] == "0"):
                if (prop["J"] == "2" ): current_mult_factor = 10
                if (prop["J"] == "3" ): current_mult_factor = 15
            if (prop["L"] == "1"):
                if (prop["J"] == "2" ): current_mult_factor = 20
                if (prop["J"] == "3" ): current_mult_factor = 30
            if (prop["L"] == "2"):
                if (prop["J"] == "2" ): current_mult_factor = 10
                if (prop["J"] == "3" ): current_mult_factor = 12
            if (prop["BMin"] == "250"): current_mult_factor = current_mult_factor/2


        if (dist == "mBBMVA" and prop["L"] == "2"):
            if (prop["J"] == "2" ):
                if ( pTVmin == "150" ) : current_mult_factor = 5
                if ( pTVmin ==  "75" ) : current_mult_factor = 30
            if (prop["J"] == "3" ):
                if ( pTVmin == "150" ) : current_mult_factor = 20
                if ( pTVmin ==  "75" ) : current_mult_factor = 50

        if dist == "mBB" :
            if not vh_cba:
                if (prop["L"] == "0") :
                    if prop["J"] == "2" : current_mult_factor = 5
                    if prop["J"] == "3" : current_mult_factor = 10
                if (prop["L"] == "2"):
                    if (current_mult_factor < 5): current_mult_factor = 5
                    if (prop["D"] == "SR") and (prop["J"] == "3") : current_mult_factor = 10
                if (prop["J"] == "3" ) and (prop["D"] == "WhfSR") : current_mult_factor = 70
            else:
            #######
            #  for CBA, Changqiao, temp. solution
            #######
                if (prop["L"] == "0"):
                    if prop["J"] == "2":
                        if ( pTVmin == "150" ) : current_mult_factor = 7
                        else: current_mult_factor = 2
                    else :
                        if ( pTVmin == "150" ) : current_mult_factor = 20
                        else : current_mult_factor = 4
                if (prop["L"] == "1"):
                    if prop["J"] == "2":
                        if ( pTVmin == "150" ) : current_mult_factor = 15
                        else : current_mult_factor = 3
                    else:
                        if ( pTVmin == "150" ) : current_mult_factor = 50
                        else: current_mult_factor = 10
                if prop["L"] == "2":
                    if prop["J"] == "2":
                        if ( pTVmin == "75" ) : current_mult_factor = 20
                        elif ( pTVmin == "150" ) : current_mult_factor = 5
                        else: current_mult_factor = 1
                    else:
                        if (pTVmin == "75" ) : current_mult_factor = 30
                        elif (pTVmin == "150" ) : current_mult_factor = 10
                        else: current_mult_factor = 3

        if dist == "mBBJ3" :
            if (prop["L"] == "2"):
                if (prop["D"] == "SR") : current_mult_factor = 20

        if dist == "dPhiLBmin" :
            if (prop["J"] == "2" ) and (prop["D"] == "WhfSR") : current_mult_factor = 20

        if dist == "MET" :
            if (prop["L"] == "0"):
              if (prop["J"] == "2"): current_mult_factor = 30
              if (prop["J"] == "3"): current_mult_factor = 60
            if (prop["L"] == "2"):
              if (prop["D"] == "SR"): current_mult_factor = 20
            if (prop["L"] == "1"):
                if (prop["D"] == "SR"): current_mult_factor = 20
                if (prop["J"] == "2" and prop["BMin"] == "150" and prop["D"] == "SR"): current_mult_factor = 20
                if (prop["J"] == "3" and prop["BMin"] == "250" and prop["D"] == "SR"): current_mult_factor = 20
                if (prop["J"] == "2" and prop["BMin"] == "250" and prop["D"] == "SR"): current_mult_factor = 5

        if dist == "softMET" :
            if (prop["L"] == "0"):
                current_mult_factor = 10

        if dist == "METSig" :
            if (prop["L"] == "0"):
                current_mult_factor = 10

        if dist == "cosThetaLep" :
            if (prop["L"] == "2"):
                if (prop["D"] == "SR" and prop["J"] == "3" and prop["BMin"] == "250"): current_mult_factor = 5
                if (prop["D"] == "SR" and prop["J"] == "3" and prop["BMin"] == "150"): current_mult_factor = 20
                if (prop["D"] == "SR" and prop["J"] == "2" and prop["BMin"] == "75"): current_mult_factor = 50
                if (prop["D"] == "SR" and prop["J"] == "3" and prop["BMin"] == "75"): current_mult_factor = 100

        if dist == "binMV2c10B1B2" :
            if (prop["L"] == "0"):
                if (prop["J"] == "3" and prop["BMin"] == "150" and prop["D"] == "SR"): current_mult_factor = 20
                if (prop["J"] == "2" and prop["BMin"] == "150" and prop["D"] == "SR"): current_mult_factor = 10
                if (prop["J"] == "2" and prop["BMin"] == "250" and prop["D"] == "SR"): current_mult_factor = 5
                if (prop["J"] == "3" and prop["BMin"] == "250" and prop["D"] == "SR"): current_mult_factor = 5
            if (prop["L"] == "1"):
                if (prop["J"] == "3" and prop["BMin"] == "150" and prop["D"] == "SR"): current_mult_factor = 100
                if (prop["J"] == "2" and prop["BMin"] == "150" and prop["D"] == "SR"): current_mult_factor = 20
                if (prop["J"] == "2" and prop["BMin"] == "250" and prop["D"] == "SR"): current_mult_factor = 5
                if (prop["J"] == "3" and prop["BMin"] == "250" and prop["D"] == "SR"): current_mult_factor = 20

        if dist == "mLL" :
            if (prop["L"] == "2"):
                if (prop["D"] == "SR" and prop["BMin"] == "250"): current_mult_factor = 2
                if (prop["D"] == "SR" and prop["BMin"] == "150"): current_mult_factor = 10

        if dist == "dEtaVBB" :
            if (prop["L"] == "2"):
              if (prop["D"] == "SR"): current_mult_factor = 20

        if dist == "dEtaBB" :
            if (prop["L"] == "0"):
              if (prop["J"] == "2"): current_mult_factor = 20
              if (prop["J"] == "3"): current_mult_factor = 60
            if (prop["L"] == "2"):
              if (prop["D"] == "SR"): current_mult_factor = 20

        if dist == "dPhiVBB" :
            if (prop["L"] == "0"):
              if (prop["J"] == "2"): current_mult_factor = 20
              if (prop["J"] == "3"): current_mult_factor = 60
            if (prop["L"] == "1"):
              if (prop["J"] == "2") and (prop["D"] == "WhfSR") : current_mult_factor = 20
            if (prop["L"] == "2"):
              if (prop["D"] == "SR"): current_mult_factor = 20

        if dist == "MEff" or dist == "MEff3" or dist == "HT":
            if (prop["L"] == "0"):
                if (prop["BMin"] == "250"):
                    if (prop["J"] == "2"): current_mult_factor = 5
                    if (prop["J"] == "3"): current_mult_factor = 5
                else:
                    if (prop["J"] == "2"): current_mult_factor = 20
                    if (prop["J"] == "3"): current_mult_factor = 60

        if dist == "dRBB" :
            if (prop["L"] == "2") and (prop["J"] == "2") and (prop["D"] == "SR"):
                if current_mult_factor == 70 : current_mult_factor = 30
            if (prop["L"] == "2") and (prop["J"] == "3") and (prop["D"] == "SR"):
                if current_mult_factor == 50 : current_mult_factor = 30
            if (prop["L"] == "0"):
              if (prop["J"] == "2"): current_mult_factor = 10
              if (prop["J"] == "3"): current_mult_factor = 20

        if dist == "mTW" :
            if (prop["L"] == "1") and (prop["J"] == "2") and (prop["D"] == "SR") and (prop["BMin"] == "150"): current_mult_factor = 20
            if (prop["L"] == "1") and (prop["J"] == "3") and (prop["D"] == "SR") and (prop["BMin"] == "250"): current_mult_factor = 20


        if dist == "pTB1" :
            if (prop["L"] == "0"):
              if (prop["J"] == "2"): current_mult_factor = 20
              if (prop["J"] == "3"): current_mult_factor = 60
            if (prop["L"] == "2"):
              if (prop["D"] == "SR"): current_mult_factor = 20

        if dist == "pTB2" :
            if (prop["L"] == "0"):
              if (prop["J"] == "2"): current_mult_factor = 20
              if (prop["J"] == "3"): current_mult_factor = 60
            if (prop["L"] == "2"):
              if (prop["D"] == "SR"): current_mult_factor = 20

        if dist == "pTJ3" :
            if (prop["L"] == "2"):
              if (prop["D"] == "SR"): current_mult_factor = 20

        if dist == "Mtop" :
            if (prop["L"] == "1"):
                if (prop["J"] == "2"): current_mult_factor = 60
                if (prop["J"] == "2" and prop["BMin"] == "150" and prop["D"] == "SR"): current_mult_factor = 20
                if (prop["J"] == "2" and prop["BMin"] == "250" and prop["D"] == "SR"): current_mult_factor = 5

        if dist == "dYWH" :
            if (prop["L"] == "1"):
              if (prop["J"] == "2") and (prop["D"] == "WhfSR") : current_mult_factor = 40

        if moneyPlot :
            current_mult_factor = 5

        logging.debug("The tuned mult factor is {}".format(current_mult_factor))
        return current_mult_factor

    def get_xbound_from_properties (self, prop):
        if prop["dist"] == "pTV" and prop["J"] == "2" and prop["D"] == "topemucr":
            return (80, 285)
        else :
            return None

    def get_legend_pos_from_properties (self, prop):
        result = None
        result = [0.62-0.05, 0.42, 0.865-0.05, 0.925]
        if 'L' in prop:
            if prop["L"] == '0' and prop["dist"] == "VpT":
                result = [0.155, 0.13, 0.375, 0.65]
            if prop["L"] == '0' and prop["dist"] == "mvadiboson":
                result = [0.6, 0.42, 0.845, 0.925]
            if prop["L"] == '1' and prop["dist"] == "mvadiboson" and prop["D"] == "WhfSR" and prop["J"] == '3':
                result = [0.6, 0.42, 0.835, 0.925]
        if prop["dist"] == "dPhiVBB":
            result = [0.16, 0.12, 0.38, 0.64]

        if moneyPlot :
            result = [0.62-0.07, 0.415, 0.865-0.07, 0.920]

        return result

    def get_yscale_factor_from_properties (self, prop, logy):
        # if prop["dist"] == "MV1cB1" or prop["dist"] == "MV1cB2" or prop["dist"] == "MV1cBTag":
        #     if not logy: return 1.5
        # if prop["dist"] == "dPhiVBB" :
        #     if logy: return 5
        #     else : return 0.7
        # if prop["dist"] == "dPhiLBmin" :
        #     if not logy: return 1.3
        # if prop["dist"] == "mjj" :
        #     if not logy: return 1.1
        # if prop["dist"] == "dRBB" :
        #     if logy: return 500
        # if prop["dist"] == "MV1cBTag" :
        #     if not logy: return 0.75
        # if prop["L"] == "0" :
        #     if prop["dist"] == "MV1cB1" or prop["dist"] == "MV1cB2" or prop["dist"] == "mjj" :
        #         if not logy: return 1.1
        #     if prop["dist"] == "MET" :
        #         if not logy: return 1.0/1.15
        return 1.0

    def postprocess_main_content_histogram (self, prop, hist):
        hist.GetYaxis().SetTitleOffset(1.3)
        if (prop["dist"] == "binMV2c10B1B2"):
            hist.GetXaxis().SetRangeUser(2,6)
        elif (prop["L"] == "0" and prop["dist"] == "MET" and hist.GetXaxis().GetNbins() > 3) or (prop["L"] == "1" and prop["dist"] == "pTV" and hist.GetXaxis().GetNbins()>3):
            hist.GetXaxis().SetRangeUser(150,400)
        return hist

        # draw line denoting the transition of merged and resolved
        if prop["dist"] == "MET" or prop["dist"] == "pTV":
            max_value = hist.GetMaximum()
            min_value = 0#hist.GetYaxis().GetXmin()
            x_value = hist.GetXaxis().GetBinLowEdge(hist.GetXaxis().FindBin(500))
            l = ROOT.TLine(x_value, min_value, x_value, max_value)
            l.SetLineStyle(2)
            l.SetLineWidth(4)
            l.SetNDC(False)
            l.DrawLine(x_value, min_value, x_value, max_value)
            logging.debug("drawing line with endpoint coordinates ({},{}) and ({},{})".format(x_value, min_value, x_value, max_value))
        return hist

    def get_xTitle (self, prop, data_hist):
        """ get title of X-axis from properties """
        if not prop:
            return ""
        varname = prop["dist"]
        result = varname
        labels = {
            # new
            "MV1cB1": "MV1c(b_{1}) OP",
            "MV1cB2": "MV1c(b_{2}) OP",
            "MV1cBTag": "MV1c(b) OP",
            "binMV2c10B1B2": "Binned MV2 category",
            "dEtaBB": "|#Delta#eta(b_{1},b_{2})|",
            "dEtaVBB": "|#Delta#eta(V,bb)|",
            "dPhiLBmin": "|#Delta#phi(lep,b)_{min}|",
            "dPhiVBB": "|#Delta#phi(V,bb)|",
            "dRBB": "#DeltaR(b_{1},b_{2})",
            "MEff": "m_{eff} [GeV]",
            "HT": "m_{eff} [GeV]",
            "MEff3": "m_{eff3} [GeV]",
            #"MEff": "H_{T} [GeV]",
            #"MEff3": "H_{T} [GeV]",
            "MET": "E_{T}^{miss} [GeV]",
            "METSig": "E_{T}^{miss}/#sqrt{S_{T}} [GeV^{1/2}]",
            "softMET": "p_{T}^{miss,st} [GeV]",
            "mLL": "m_{ll} [GeV]",
            #"mLL": "m_{{\ell}{\ell}} [GeV]",
            #"mLL": "m_{\\mathscr{l}\\mathscr{l}} [GeV]",
            "mTW": "m_{T}(W) [GeV]",
            "dYWH": "|#DeltaY(#it{W},#it{H})|",
            "Mtop": "m_{top} [GeV]",
            "mva": "BDT_{#it{VH}} output",
            "mvaVZ": "BDT_{#it{VZ}} output",
            "mvadiboson": "BDT_{#it{VZ}} output",
            "pTB1": "p_{T}(b_{1}) [GeV]",
            "pTB2": "p_{T}(b_{2}) [GeV]",
            "pTJ3": "p_{T}(j_{3}) [GeV]",
            "pTV": "p_{T}^{V} [GeV]",
            "VpT": "p_{T}^{V} [GeV]",
            "mVH": "m_{T}(Vh) [GeV]",
            "cosThetaLep": "cos#theta(l^{-},Z)",
            "Hc": "Hc categories",
            }
        if "mjj" in varname:
            # nominal
            tmp_extra = ""
            tmp_extra2 = " [GeV]"
            # hack for mjj trafo D
            #tmp_extra = "Transformed "
            #tmp_extra2 = ""
            #
            if prop["T"] == "2":
                result = tmp_extra+"m_{bb}"+tmp_extra2
            elif prop["T"] == "1":
                result = tmp_extra+"m_{bj}"+tmp_extra2
            else:
                result = tmp_extra+"m_{jj}"+tmp_extra2
        elif "mUnBB" in varname:
            if prop["T"] == "2":
                result = "m_{bb,uncorr} [GeV]"
            elif prop["T"] == "1":
                result = "m_{bj,uncorr} [GeV]"
            else:
                result = "m_{jj,uncorr} [GeV]"
        elif "mCorrBB" in varname:
            if prop["T"] == "2":
                result = "m_{bb,corr} [GeV]"
            elif prop["T"] == "1":
                result = "m_{bj,corr} [GeV]"
            else:
                result = "m_{jj,corr} [GeV]"
        elif "mBBJ" in varname:
            if prop["T"] == "2":
                result = "m_{bbj} [GeV]"
            elif prop["T"] == "1":
                result = "m_{bjj} [GeV]"
            else:
                result = "m_{jjj} [GeV]"
        elif "mBB" in varname:
            if prop["T"] == "2":
                #result = "m_{b#bar{b}} [GeV]"
                result = "m_{bb} [GeV]"
            elif prop["T"] == "1":
                result = "m_{bj} [GeV]"
            else:
                result = "m_{jj} [GeV]"
        elif "mVH" in varname:
            if prop["L"] == "1" or prop["L"] == "0":
                result = "m_{T}(Vh) [GeV]"
            else:
                result = "m(Vh) [GeV]"
        elif varname in labels:
            result = labels[varname]
            #for k in labels:
                #if k in varname:
                    #return labels[k]
        return result

    def get_yTitle_tag (self, prop, data_hist):
        if prop is None:
            return ""

        extra_unit = ""
        if prop["dist"] == "MEff" :  extra_unit = " GeV"
        if prop["dist"] == "HT" :    extra_unit = " GeV"
        if prop["dist"] == "MEff3" : extra_unit = " GeV"
        if prop["dist"] == "MET" :   extra_unit = " GeV"
        if prop["dist"] == "softMET" : extra_unit = " GeV"
        if prop["dist"] == "mLL" :   extra_unit = " GeV"
        if prop["dist"] == "mTW" :   extra_unit = " GeV"
        if prop["dist"] == "Mtop" :  extra_unit = " GeV"
        if prop["dist"] == "pTB1" :  extra_unit = " GeV"
        if prop["dist"] == "pTB2" :  extra_unit = " GeV"
        if prop["dist"] == "pTJ3" :  extra_unit = " GeV"
        if prop["dist"] == "pTV" :   extra_unit = " GeV"
        #if prop["dist"] == "VpT" :   extra_unit = " GeV" # new
        if prop["dist"] == "mjj" :   extra_unit = " GeV" # hack -> comment when trafoD
        if prop["dist"] == "mBB" :   extra_unit = " GeV"
        if prop["dist"] == "mUnBB" :   extra_unit = " GeV"
        if prop["dist"] == "mCorrBB" :   extra_unit = " GeV"
        if prop["dist"] == "mBBJ" :  extra_unit = " GeV"
        if prop["dist"] == "mVH" :  extra_unit = " GeV"
        if prop["dist"] == "binMV2c10B1B2" :  extra_unit = " bin"

        # if use variable bin-width add extra label " / [unit]"
        #binCheck = data_hist.GetBinWidth(1)
        #for iB in range(2,data_hist.GetNbinsX()+1):
        #    if binCheck != data_hist.GetBinWidth(iB):
        #        logging.debug("Found 2 different bin-width: (bin 1, width {0:.2f}) and (bin {1:.0f} width {2:.2f})".format(binCheck, iB, data_hist.GetBinWidth(iB)))
        #        return " /"+extra_unit

        # NOTE: JWH - ED board requests
        if not self.do_rebinning(prop):
        # if not (prop["dist"] == "mVH" and prop.get("incFat", "-1") == "-1" and
        #     prop.get("D", "") == "SR" and prop.get("L", "0") == "2") :
            extra_number = str(data_hist.GetBinWidth(1))
            if not extra_number.find('.') == -1: extra_number = extra_number[:extra_number.find('.')]
            extra_unit = " " + extra_number + extra_unit
            if 'mva' in prop["dist"]: extra_unit=""

        y_ratio = round(data_hist.GetBinWidth(1), 2)
        y_str = str(y_ratio)
        #if (y_ratio*10) % 10 == 0 and (y_ratio*100) % 100 == 0: y_str = str(int(y_ratio))
        #else:
        #    y_str=y_str.rstrip('0')
        if prop["dist"] == "VpT": extra_str = " / bin" # new
        elif prop["dist"] == "mVH":  extra_str = " /" + extra_unit
        else: extra_str = " / " + y_str + extra_unit # new

        if prop["dist"] == "MV1cB1":   extra_str = ""
        if prop["dist"] == "MV1cB2":   extra_str = ""
        if prop["dist"] == "MV1cBTag": extra_str = ""
        
        return extra_str

    def set_y_range (self, hist, nlegend_items, miny, total_miny, maxy, log_scale, prop, keep_neg=False):
        # if log_scale and prop["dist"] == "mVH":
        #     hist.SetMaximum(maxy * 100)
        #     hist.SetMinimum(0.001)
        #     return
        
        if prop is not None:
            keep_neg = (prop["L"] == "3")

        bottom_padding = 1.0/16.0
        content_faction = 4.0/7.0 if nlegend_items <= 8 else 3.0/7.0
        
        if self.isSoBplot :
            if total_miny < 1e-2: total_miny = 1e-2
            log_miny = ROOT.TMath.Log10(total_miny)
            log_maxy = ROOT.TMath.Log10(maxy)
            log_maxy = ROOT.TMath.Log10(maxy)
            plot_scale = (log_maxy - log_miny)
            bottom = log_miny
            top = bottom + plot_scale/content_faction
            hist.GetYaxis().SetLimits(1, ROOT.TMath.Power(10, top*1.2))
            return
        
        if prop is not None:
            pTVmin = prop.get("BMin", "-999")
            if not log_scale:
                if prop["dist"] == "mvadiboson":
                    if (prop["L"] == "0") or (prop["L"] == "1") or (prop["L"] == "2" and prop["D"] == "SR") :
                        content_faction *= 1.15

                if prop["dist"] == "mBB":
                    if prop["L"] == "0" : content_faction *= 1.35 
                    if (prop["D"] == "WhfSR"):
                        if (prop["J"] == "2") :
                           if vh_cba: content_faction *= 1.4
                           else: content_faction *= 1.5
                        if (prop["J"] == "3"):
                            if vh_cba:
                                if (pTVmin=="150"): content_faction *= 1.4
                                else: content_faction *= 1.5
                            else: content_faction *= 1.15
                    if (prop["L"] == "2"):
                        if (prop["D"] == "SR") :
                          if (prop["J"] == "2") :
                              if (pTVmin=="75") : content_faction *= 1.1 
                              elif (pTVmin=="150") : content_faction *= 1.2
                              elif (pTVmin=="200"):
                                  if vh_cba: content_faction *= 1.2
                                  else: content_faction *= 1.2
                              else : content_faction *= 1.1 
                          if (prop["J"] == "3") :
                              if (pTVmin=="150") : content_faction *= 1.
                              if (pTVmin=="200") and vh_cba: content_faction *= 1.2
                              else : content_faction *= 1.1
                        else :
                          if (prop["J"] == "2") :
                              if (pTVmin=="75") and vh_cba: content_faction *= 0.9
                              elif (pTVmin=="150") and vh_cba: content_faction *= 0.75
                              else:
                                  content_faction *= 1.2
                          if (prop["J"] == "3") : content_faction *= 1.

                if prop["dist"] == "mBBMVA":
                    if (prop["J"] == "2") and (prop["D"] == "SR") : content_faction *= 1.50

                if prop["dist"] == "mLL":
                    if (prop["J"] == "2") and (prop["D"] == "SR") : content_faction *= 1.20

                if prop["dist"] == "HT":
                    if (prop["BMin"] == "150") : content_faction *= 1.40
                    if (prop["BMin"] == "250") : content_faction *= 1.40

                if (prop["dist"] == "pTV") :
                    if (prop["D"] == "CRLow" or prop["D"] == "CRHigh") :
                        content_faction *= 0.9
                    elif (prop["BMin"] == "0" and prop["D"] == "SR") :
                        if (prop["L"] == "1") : content_faction *= 0.9
                    else : content_faction *= 1.0

                if prop["dist"] == "binMV2c10B1B2": content_faction *= 0.85

                if prop["dist"] == "cosThetaLep":
                    if (prop["L"] == "2") : content_faction *= 0.80

                if prop["dist"] == "mTW":
                    if (prop["J"] == "2") and (prop["D"] == "WhfSR") : content_faction *= 1.30

                if prop["dist"] == "Mtop":
                    if (prop["J"] == "3") and (prop["D"] == "WhfSR") : content_faction *= 1.15
                    if (prop["L"] == "1") :
                        if (prop["J"] == "2" or prop["J"] == "3") and (prop["D"] == "SR") and (prop["BMin"] == "150"): content_faction *= 1.20
                        if (prop["J"] == "2" or prop["J"] == "3") and (prop["D"] == "SR") and (prop["BMin"] == "250"): content_faction *= 1.20
                    else : content_faction *= 1.6

                if prop["dist"] == "dYWH":
                    if (prop["J"] == "3") and (prop["D"] == "WhfSR"): content_faction *= 1.2
                    else: content_faction *= 1.30

                if prop["dist"] == "pTB1":
                    if (prop["L"] == "0") : content_faction *= 1.50
                    if (prop["L"] == "1") :
                        if (prop["J"] == "3") and (prop["D"] == "WhfSR") : content_faction *= 1.2
                        else : content_faction *= 1.30

                if prop["dist"] == "pTB2":
                    if (prop["L"] == "0") : content_faction *= 1.50
                    if (prop["L"] == "1") :
                        if (prop["J"] == "3") and (prop["D"] == "SR") : content_faction *= 1.25
                        else: content_faction *= 1.40

                if prop["dist"] == "MET":
                    if (prop["D"] == "CRLow" or prop["D"] == "CRHigh") :
                        content_faction *= 0.9
                    else :	
                        if (prop["L"] == "0") : content_faction *= 1.50
                        if (prop["L"] == "1") :
                            if (prop["D"] == "WhfSR") and (prop["J"] == "3") : content_faction *= 1.25
                            if (prop["J"] == "3") and (prop["BMin"] == "150") and (prop["D"] == "SR"): content_faction *= 0.60
                            if (prop["J"] == "2") and (prop["BMin"] == "250") and (prop["D"] == "SR"): content_faction *= 0.60
                            if (prop["J"] == "3") and (prop["BMin"] == "250") and (prop["D"] == "SR"): content_faction *= 1.00
                        else: content_faction *= 1.50
                        if (prop["L"] == "2") and (prop["D"] == "SR") : content_faction *= 1.25

                if (prop["dist"] == "MEff") or (prop["dist"] == "MEff3") :
                    if (prop["L"] == "0") : content_faction *= 1.40

                if (prop["dist"] == "softMET"): 
                    if(prop["BMin"] == "150"): content_faction *= 1.30
                    if(prop["BMin"] == "250"): content_faction *= 1.50

                if (prop["dist"] == "dPhiVBB") :
                    if (prop["L"] == "0") : content_faction *= 2.0
                    if (prop["L"] == "1") :
                       if (prop["D"] == "WhfSR") :
                          if ( prop["J"] == "2" ) : content_faction *= 2.00
                          if ( prop["J"] == "3" ) : content_faction *= 1.40
                       else :
                          if ( prop["J"] == "2" ) : content_faction *= 1.40
                          if ( prop["J"] == "3" ) : content_faction *= 1.40
                    if (prop["L"] == "2") : content_faction *= 1.50

                if (prop["dist"] == "dRBB") :
                    if (prop["L"] == "0") :
                        if (prop["J"] == "2") and (prop["BMin"] == "250") : content_faction *= 1.3
                        elif (prop["J"] == "2") and (prop["BMin"] == "150") : content_faction *= 1.0
                        else : content_faction *= 1.40
                    if (prop["L"] == "1" and prop["D"] == "SR"):
                        if (prop["BMin"] == "150") : content_faction *= 0.80
                        elif (prop["BMin"] == "250") : content_faction *= 1.20
                    if (prop["L"] == "2") :
                        if (prop["D"] == "SR") :
                            if (prop["J"] == "2") and (prop["BMin"] == "150") : content_faction *= 0.9
                            elif (prop["J"] == "2") and (prop["BMin"] == "250") : content_faction *= 1.0
                            if (prop["J"] == "3") :
                                content_faction *= 1.2

                if (prop["dist"] == "mBBJ") :
                    if (prop["L"] == "0") : content_faction *= 1.45

                if (prop["dist"] == "mBBJ3") :
                    if (prop["L"] == "2") :
                        if (prop["D"] == "SR") :
                           if (pTVmin=="150") : content_faction *= 1.65
                           else : content_faction *= 1.25
                        else :
                           if (pTVmin=="150") : content_faction *= 1.3
                           else : content_faction *= 1.2

                if (prop["dist"] == "dEtaBB") :
                    if (prop["L"] == "0") :
                        if (prop["J"] == "2") : content_faction *= 1.45
                        else : content_faction *= 1.30
                    if (prop["L"] == "2") and (prop["D"] == "SR") : content_faction *= 1.30

                if (prop["dist"] == "dEtaVBB") :
                    if (prop["L"] == "2") and (prop["D"] == "SR"): content_faction *= 1.25

                if (prop["dist"] == "pTJ3") :
                    if (prop["L"] == "0") : content_faction *= 1.40
                    if (prop["D"] == "WhfSR") :
                        if (prop["J"] == "3") : content_faction *= 1.25
                        else : content_faction *= 1.30
                    if (prop["L"] == "2") and (pTVmin=="150") : content_faction *= 1.50

            else:
                if prop["dist"] == "mva":
                    if (prop["L"] == "0" and prop["J"]=="3") : content_faction *= 1.23
                    elif (prop["L"] == "2") : 
                        if (prop["BMin"] == "250" and prop["J"]=="2") : content_faction *= 1.23
                        elif (prop["BMin"] == "75") : 
                            if (prop["J"] == "2") : content_faction *= 0.85
                            else : content_faction *= 1.0
                        else : content_faction *= 1.15
                    else: content_faction *= 1.30

                if prop["dist"] == "mvadiboson":
                    if (prop["L"] == "2") : 
                        if (prop["J"] == "2") : 
                            if (prop["BMin"] == "250") : content_faction *= 0.8
                            else : content_faction *= 0.65
                        else : 
                            if (prop["BMin"] == "250") : content_faction *= 1.1							
                            else : content_faction *= 1.30
                    if (prop["L"] == "0") : 
                            if (prop["BMin"] == "250") : content_faction *= 1.1
                            else : content_faction *= 1.02 

                    if (prop["L"] == "1") : 
                        if (prop["BMin"] == "250") : content_faction *= 0.8
                        else : content_faction *= 0.8 
                    if (prop["L"] == "1" and prop["D"] == "WhfCR") : content_faction *= 0.7

                if (prop["dist"] == "pTV") :
                    if (prop["BMin"] == "0") :
                        if (prop["L"] == "1") : content_faction *= 0.8
                        else : content_faction *= 0.9
                    elif (prop["L"] == "2") and (prop["D"] == "SR" ) : content_faction *= 1.40*1.30
                    elif (prop["L"] == "2") and (prop["D"] == "topemucr" ) : content_faction *= 1.20
                    elif (prop["L"] == "1") and (prop["D"] == "WhfCR") and (prop["J"] == "3")  : content_faction *= 1.2
                    else : content_faction *= 1.30

                if (prop["dist"] == "MEff") or (prop["dist"] == "MEff3") :
                    if (prop["L"] == "0") : content_faction *= 1.40

                if (prop["dist"] == "dEtaBB") :
                    if (prop["D"] == "SR"): content_faction *= 1.30

                if (prop["dist"] == "dEtaVBB") :
                    if (prop["L"] == "2") and (prop["D"] == "SR"): content_faction *= 1.40

                if (prop["dist"] == "dPhiLBmin") :
                    if (prop["D"] == "WhfSR"): content_faction *= 0.80
                    if (prop["D"] == "WhfCR") and (prop["J"] == "3"): content_faction *= 0.80

                if prop["dist"] == "Mtop":
                    if (prop["J"] == "3") and (prop["D"] == "WhfSR") : content_faction *= 1.20
                    elif (prop["J"] == "3") and (prop["BMin"] == "150"): content_faction *= 1.30
                    elif (prop["J"] == "2") and (prop["BMin"] == "250"): content_faction *= 1.30
                    else : content_faction *= 1.10

                if prop["dist"] == "pTB2":
                    if (prop["L"] == "0") : content_faction *= 1.20
                    if (prop["L"] == "1") : content_faction *= 1.30

                if (prop["dist"] == "pTJ3") :
                    if (prop["L"] == "0") : content_faction *= 1.20
                    if (prop["D"] == "WhfSR") : content_faction *= 1.30
                    if (prop["L"] == "2") :
                        if (prop["D"] == "SR") and (pTVmin=="150") : content_faction *= 1.40

                if prop["dist"] == "MET":
                    if (prop["L"] == "0") : content_faction *= 1.40
                    if (prop["L"] == "1") : content_faction *= 1.30
                    if (prop["L"] == "2") and (prop["D"] == "SR") : content_faction *= 1.40

                if prop["dist"] == "pTB1":
                    if (prop["L"] == "1") :
                        if (prop["J"] == "3") and (prop["D"] == "WhfSR") : content_faction *= 1.25

                if prop["dist"] == "dYWH":
                    if (prop["J"] == "3") and (prop["D"] == "WhfSR"): content_faction *= 1.30

        if not log_scale:
            if not keep_neg: miny = 0
            logging.info( "AnaPlotCfg: check non-log min/max y for {0} {1} {2}".format(hist.GetName(),miny,maxy))
            plot_scale = (maxy - miny)
            bottom = miny - bottom_padding*plot_scale
            top = bottom + plot_scale/content_faction

            if moneyPlot :
                top = 40

            # hist.SetMinimum(bottom)
            # hist.SetMaximum(top)

            hist.GetYaxis().SetLimits(bottom, top)
            logging.debug("--- setting histogram {0} y-range ({1}, {2})".format(hist.GetName(),bottom,top))

            # hist.GetHistogram().GetYaxis().SetRangeUser(bottom, top)
            logging.debug("check plot y-range to ({0}, {1}){2}".format(hist.GetHistogram().GetYaxis().GetXmin(), hist.GetHistogram().GetYaxis().GetXmax(),keep_neg))
            return
        else:
            # miny is the minimum of the each process, total_miny is the minimum of entire bkg
            if total_miny < 1e-2: total_miny = 1e-2
            # miny is special for WhfCR L1 pTV
            if prop is not None:
                if (prop["dist"] == "pTV") and (prop["L"] == "1") and (prop["D"] == "WhfCR") and (prop["J"] == "2"):
                    total_miny = 1
                elif (prop["dist"] == "MET") and (prop["L"] == "0") and (prop["D"] == "SR"):
                    total_miny = 10
                elif (prop["dist"] == "pTV") and (prop["L"] == "1") and (prop["D"] == "SR") and (prop["J"] == "3"):
                    maxy = ROOT.TMath.Power(10, 3)
                    total_miny = 20
                elif (prop["dist"] == "pTV") and (prop["L"] == "1") and (prop["D"] == "SR") and (prop["J"] == "2"):
                    maxy = ROOT.TMath.Power(10, 2.7)
                    total_miny = 10
                elif (prop["dist"] == "pTV") and (prop["L"] == "2") and (prop["D"] == "SR") and (prop["J"] == "3"):
                    maxy = ROOT.TMath.Power(10, 3)
                elif (prop["dist"] == "pTV") and (prop["L"] == "2") and (prop["D"] == "SR") and (prop["J"] == "2"):
                    maxy = ROOT.TMath.Power(10, 2)

            log_miny = ROOT.TMath.Log10(total_miny)
            log_maxy = ROOT.TMath.Log10(maxy)
            plot_scale = (log_maxy - log_miny)
            # 0.25 is just fine tuning
            # bottom = log_miny - 0.25*bottom_padding*plot_scale
            bottom = log_miny
            top = bottom + plot_scale/content_faction

            # hist.SetMinimum(ROOT.TMath.Power(10, bottom))
            # hist.SetMaximum(ROOT.TMath.Power(10, top))
            if prop is not None:
                if ((prop["J"] == "2") and (prop["L"]=="2") and (prop["D"] == "SR") ):
                    hist.GetYaxis().SetLimits(2., ROOT.TMath.Power(10, top))
                else :
                    hist.GetYaxis().SetLimits(ROOT.TMath.Power(10, bottom), ROOT.TMath.Power(10, top))
            else:
                hist.GetYaxis().SetLimits(ROOT.TMath.Power(10, bottom), ROOT.TMath.Power(10, top))

            # hist.GetHistogram().GetYaxis().SetRangeUser(ROOT.TMath.Power(10, bottom), ROOT.TMath.Power(10, top))
            logging.debug("setting log scale plot y-range to ({0}, {1})".format(hist.GetHistogram().GetYaxis().GetXmin(), hist.GetHistogram().GetYaxis().GetXmax()))
            return

        # if not log_scale and miny > 0:
        #     miny = 0
        # if log_scale and miny <= 1:
        #     miny = 0.25
        # mini = miny
        #
        # if mini < 0:
        #     hist.SetMinimum(mini*1.25)
        # else:
        #     mini = 0
        #     # fix 0 cut in the Y axis
        #     #hist.SetMinimum(0.01)
        # if log_scale:
        #     hist.SetMaximum(maxy * 100)
        #     hist.SetMinimum(miny / 2.5)
        # else:
        #     hist.SetMaximum(mini + (maxy - mini) * 1.5)

    def auto_compute_ratio_yscale_from_properties (self, prop):
        #return (prop["dist"] == "mva" or prop["dist"] == "mvaVZ")
        return False

    def scale_all_yvals(self, prop):
        return prop["dist"] == "mva", 0.05

    def postprocess_dataMC_ratio_histogram (self, prop, hist, xbounds=None):
        logging.debug("create the dash line")
        #draw dashed line at 1
        y_value = 1# hist.GetYaxis().GetBinCenter(hist.GetYaxis().FindBin(1))

        if prop["dist"] == "binMV2c10B1B2":
            x_lo=2
            x_hi=6
        elif (prop["L"] == "0" and prop["dist"] == "MET" and hist.GetXaxis().GetNbins() > 3) or (prop["L"] == "1" and prop["dist"] == "pTV" and hist.GetXaxis().GetNbins() > 3):
            x_lo=150
            x_hi=400
        else:
            x_hi=hist.GetXaxis().GetBinUpEdge(hist.GetXaxis().GetNbins())
            x_lo=hist.GetXaxis().GetBinLowEdge(1)

        if xbounds :
            x_lo = xbounds[0]
            x_hi = xbounds[1]

        l = ROOT.TLine(x_lo, y_value, x_hi, y_value)
        l.SetLineStyle(1)
        l.SetLineColor(ROOT.kGray + 1)
        l.SetLineWidth(1)
        l.SetNDC(False)
        #l.DrawLine(x_lo, y_value, x_hi, y_value)
        #l.Draw()
        #logging.debug("drawing line with endpoint coordinates ({},{}) and ({},{})".format(x_lo, y_value, x_hi, y_value))
        hist.GetXaxis().SetLabelOffset(0.05)
        hist.GetYaxis().SetLabelOffset(0.02)

        if prop["dist"] == "binMV2c10B1B2":
            hist.GetXaxis().SetRangeUser(2,6)
            hist.GetXaxis().SetBinLabel(3,"(60-70%,60-70%)")
            hist.GetXaxis().SetBinLabel(4,"(60-70%,0-60%)")
            hist.GetXaxis().SetBinLabel(5,"(0-60%,60-70%)")
            hist.GetXaxis().SetBinLabel(6,"(0-60%,0-60%)")
            hist.GetXaxis().SetLabelSize(0.17)
            hist.GetXaxis().CenterLabels()
        elif prop["dist"] == "METSig":
            hist.GetXaxis().SetRangeUser(0,5)
        elif prop["dist"] == "softMET":
            hist.GetXaxis().SetRangeUser(0,40)
        elif (prop["L"] == "0" and prop["dist"] == "MET" and hist.GetXaxis().GetNbins() > 3) or (prop["L"] == "1" and prop["dist"] == "pTV" and hist.GetXaxis().GetNbins() > 3):
            hist.GetXaxis().SetRangeUser(150,400)

        logging.debug("create the dash line")

        return hist,l

    def add_additional_signal_info_to_legend (self, legend, signal):
        return

    def dropping_list_in_legend (self, prop):
        result = ['None']
        if prop is None: result = ['None']
        else:
            if (prop["dist"] == "mva" and prop["L"] == "2") :
                if (prop["D"] == "SR"):
                    if (prop["J"] == "3") : result = ['W', 'Whf', 'Wl', 'Wcl']
                    elif (prop["J"] == "2") : result = ['W', 'Whf', 'Wl', 'Wcl']
                elif (prop["D"] == "CR"):  result = ['W', 'Whf', 'Wl', 'Wcl']
            #if prop["dist"] == 'mva':
            #    if (prop["D"] == "WhfSR") : result = ['Zcl','Zl']
            elif prop["dist"] == 'mvadiboson':
                if (prop["D"] == "WhfSR") : result = ['Zcl','Zl']
                if (prop["L"] == "0") : result = ['Zcl','Zl']
            else : result = ['None']
        return result

    def getTableTitle(self, region, part):
        import plotMaker
        props = plotMaker.getPropertiesFromTag(self, region)

        if part ==1 :
            return props['L']+"-lepton"
        elif part == 2:
            reg=props['D']+", "
            j = props['J']
            if props['BMin'] == "250":
                reg+="$\ptv>250\,\GeV$, "
            elif props['BMin'] == "150":
                reg+="$150\,\GeV<\ptv<250\,\GeV$, "
            elif props['BMin'] == "75":
                reg+="$75\,\GeV<\ptv<150\,\GeV$, "
            if props['L']!="2" or j!="3":
                reg+= j+"-jet, 2-$b$-tag"
            else:
                reg+= "$\geq$3-jet, 2-$b$-tag"
            return reg
        elif part == 3:
            j = props['J']
            if props['L']!="2" or j!="3":
                return j+"-jet"
            else:
                return "$\geq$3-jet"

        return "blih"
