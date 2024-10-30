#include <iostream>

#include "TString.h"

class MuHatModes {

 public:
  MuHatModes(int mode = 2)
  {
    npsetands = vector<TString*>(npsets_max, new TString(""));
    initialize(mode);
  }

  static const int npsets_max = 40;
  static const int nstrmax    = 60;
  TString*         npsetname[npsets_max];
  bool             npsetsubtract[npsets_max];
  TString*         npsetstring[npsets_max][nstrmax];
  vector<TString*> npsetands;
  int              npnstr[npsets_max];
  int              npsets      = 0;
  int              dataStatSet = 1;
  bool             npsetexclude[npsets_max];

  unsigned int get_nCat() { return npsets; }

  void initialize(int mode)
  {

    for( int iset = 0; iset < npsets_max; iset++ ) {
      npsetname[iset]     = new TString("xxxxx");
      npsetsubtract[iset] = true;
      for( int istr = 0; istr < nstrmax; istr++ ) {
        npsetstring[iset][istr] = new TString("xxxxx");
      }
      npsetexclude[iset] = false;
    }

    //*********************************************************************************
    //*********************************************************************************
    //                           Common to all modes
    //*********************************************************************************
    //*********************************************************************************

    npsetname[0]     = new TString("Total                  ");
    npsetsubtract[0] = false;

    npsetname[1]     = new TString("DataStat               ");
    npsetexclude[1]  = true;
    npsetsubtract[1] = false;

    npsetname[2] = new TString("FullSyst               ");

    // Warning: Start all NP set indexes with 2 in the mode-specific section!

    std::cout << std::endl << "NP breakdown with mode " << mode << std::endl;

    //*********************************************************************************
    //*********************************************************************************
    //                           Mode 0
    //*********************************************************************************
    //*********************************************************************************

    if( mode == 0 ) {

      npsetname[3]      = new TString("Floating norms");
      npsetstring[3][0] = new TString("norm");

      npsetname[4]      = new TString("All Norms");
      npsetstring[4][0] = new TString("norm");
      npsetstring[4][1] = new TString("Norm");

      npsetname[5]      = new TString("AllOtherSysts");
      npsetstring[5][0] = new TString("norm");
      npsetstring[5][1] = new TString("Norm");
      npsetexclude[5]   = true;

      npsetname[6]      = new TString("ThH");
      npsetstring[6][0] = new TString("Theory");

      npsetname[7]      = new TString("ThD");
      npsetstring[7][0] = new TString("VV");

      //*********************************************************************************
      //*********************************************************************************
      //                           Mode 1
      //*********************************************************************************
      //*********************************************************************************
    } else if( mode == 1 ) {

      npsetname[3]      = new TString("Floating normalizations");
      npsetstring[3][0] = new TString("norm");

      npsetname[4]      = new TString("All normalizations");
      npsetstring[4][0] = new TString("norm");
      npsetstring[4][1] = new TString("Norm");

      npsetname[5]      = new TString("All but normalizations");
      npsetstring[5][0] = new TString("norm");
      npsetstring[5][1] = new TString("Norm");
      npsetexclude[5]   = true;

      npsetname[6]      = new TString("Jets MET");
      npsetstring[6][0] = new TString("SysJET");
      npsetstring[6][1] = new TString("SysMET");
      npsetstring[6][2] = new TString("SysFATJET");
      npsetstring[6][3] = new TString("SysJER");

      npsetname[7]      = new TString("BTag");
      npsetstring[7][0] = new TString("SysFT");

      npsetname[8]      = new TString("Leptons");
      npsetstring[8][0] = new TString("SysEG");
      npsetstring[8][1] = new TString("SysEL");
      npsetstring[8][2] = new TString("SysMUONS");

      npsetname[9]      = new TString("Luminosity");
      npsetstring[9][0] = new TString("LUMI");

      npsetname[10]      = new TString("Diboson");
      npsetstring[10][0] = new TString("VV");
      npsetstring[10][1] = new TString("WW");
      npsetstring[10][2] = new TString("ZZ");
      npsetstring[10][3] = new TString("WZ");

      npsetname[11]      = new TString("Zjets");
      npsetstring[11][0] = new TString("ZDPhi");
      npsetstring[11][1] = new TString("ZMbb");
      npsetstring[11][2] = new TString("ZPt");
      npsetstring[11][3] = new TString("Zcl");
      npsetstring[11][4] = new TString("Zbb");
      npsetstring[11][5] = new TString("Zl");
      npsetstring[11][6] = new TString("Zbc");
      npsetstring[11][7] = new TString("Zbl");
      npsetstring[11][8] = new TString("Zcc");

      npsetname[12]      = new TString("Wjets");
      npsetstring[12][0] = new TString("WDPhi");
      npsetstring[12][1] = new TString("WMbb");
      npsetstring[12][2] = new TString("WbbMbb");
      npsetstring[12][3] = new TString("WPt");
      npsetstring[12][4] = new TString("Wbb");
      npsetstring[12][5] = new TString("Wbc");
      npsetstring[12][6] = new TString("Wbl");
      npsetstring[12][7] = new TString("Wcc");
      npsetstring[12][8] = new TString("Wcl");
      npsetstring[12][9] = new TString("Wl");

      npsetname[13]      = new TString("Model ttbar");
      npsetstring[13][0] = new TString("TtBar");
      npsetstring[13][1] = new TString("ttBarHigh");
      npsetstring[13][2] = new TString("TopPt");
      npsetstring[13][3] = new TString("TTbarPTV");
      npsetstring[13][4] = new TString("TTbarMBB");
      npsetstring[13][5] = new TString("ttbar");

      npsetname[14]      = new TString("Model Single Top");
      npsetstring[14][0] = new TString("stop");
      npsetstring[14][1] = new TString("Stop");

      npsetname[15]      = new TString("Model Multi Jet");
      npsetstring[15][0] = new TString("MJ");

      npsetname[16]      = new TString("Signal Systematics");
      npsetstring[16][0] = new TString("Theory");
      npsetstring[16][1] = new TString("VH");

      npsetname[17]      = new TString("MC stat");
      npsetstring[17][0] = new TString("gamma");

      //*********************************************************************************
      //*********************************************************************************
      //                           Mode 3
      //                      VH run 1 paper table
      //*********************************************************************************
      //*********************************************************************************
    } else if( mode == 3 ) {

      int i = 2;
      int j = 0;

      i++;
      j                   = 0;
      npsetname[i]        = new TString("W+jets");
      npsetstring[i][j++] = new TString("WPtV");
      npsetstring[i][j++] = new TString("WDPhi");
      npsetstring[i][j++] = new TString("WMbb");
      npsetstring[i][j++] = new TString("WbbRatio");
      npsetstring[i][j++] = new TString("WlNorm");
      npsetstring[i][j++] = new TString("WclNorm");
      npsetstring[i][j++] = new TString("WhfNorm");
      npsetstring[i][j++] = new TString("norm_W");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("W+jets norm");
      npsetstring[i][j++] = new TString("norm_W");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("W+jets model");
      npsetstring[i][j++] = new TString("WPtV");
      npsetstring[i][j++] = new TString("WDPhi");
      npsetstring[i][j++] = new TString("WMbb");
      npsetstring[i][j++] = new TString("WbbRatio");
      npsetstring[i][j++] = new TString("WlNorm");
      npsetstring[i][j++] = new TString("WclNorm");
      npsetstring[i][j++] = new TString("WhfNorm");

      // HERE
      i++;
      j                   = 0;
      npsetname[i]        = new TString("Z+jets");
      npsetstring[i][j++] = new TString("ZPtV");
      npsetstring[i][j++] = new TString("ZDPhi");
      npsetstring[i][j++] = new TString("ZMbb");
      npsetstring[i][j++] = new TString("ZbbRatio");
      npsetstring[i][j++] = new TString("ZlNorm");
      npsetstring[i][j++] = new TString("ZclNorm");
      npsetstring[i][j++] = new TString("ZbbNorm");
      npsetstring[i][j++] = new TString("norm_Z");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Z+jets norm");
      npsetstring[i][j++] = new TString("norm_Z");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Z+jets modelling");
      npsetstring[i][j++] = new TString("ZPtV");
      npsetstring[i][j++] = new TString("ZDPhi");
      npsetstring[i][j++] = new TString("ZMbb");
      npsetstring[i][j++] = new TString("ZbbRatio");
      npsetstring[i][j++] = new TString("ZlNorm");
      npsetstring[i][j++] = new TString("ZclNorm");
      npsetstring[i][j++] = new TString("ZbbNorm");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Signal Theory");
      npsetstring[i][j++] = new TString("Theory");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("All b-tagging");
      npsetstring[i][j++] = new TString("BTag");
      npsetstring[i][j++] = new TString("TruthTagDR");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Diboson");
      npsetstring[i][j++] = new TString("VVMbb");
      npsetstring[i][j++] = new TString("VVJet");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("b-tagging (c-jets)");
      npsetstring[i][j++] = new TString("BTagC");
      npsetstring[i][j++] = new TString("TruthTagDR");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("b-tagging (b-jets)");
      npsetstring[i][j++] = new TString("BTagB");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("b-tagging (light-jets)");
      npsetstring[i][j++] = new TString("BTagL");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("MJ");
      npsetstring[i][j++] = new TString("MJ");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Jets");
      npsetstring[i][j++] = new TString("JVF");
      npsetstring[i][j++] = new TString("JetN");
      npsetstring[i][j++] = new TString("JetE");
      npsetstring[i][j++] = new TString("JetF");
      npsetstring[i][j++] = new TString("JetPile");
      npsetstring[i][j++] = new TString("JetB");
      npsetstring[i][j++] = new TString("JetM");
      npsetstring[i][j++] = new TString("JetR");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("MET");
      npsetstring[i][j++] = new TString("MET");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Jets&MET");
      npsetstring[i][j++] = new TString("JVF");
      npsetstring[i][j++] = new TString("JetN");
      npsetstring[i][j++] = new TString("JetE");
      npsetstring[i][j++] = new TString("JetF");
      npsetstring[i][j++] = new TString("JetPile");
      npsetstring[i][j++] = new TString("JetB");
      npsetstring[i][j++] = new TString("JetM");
      npsetstring[i][j++] = new TString("JetR");
      npsetstring[i][j++] = new TString("MET");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Leptons");
      npsetstring[i][j++] = new TString("Elec");
      npsetstring[i][j++] = new TString("Muon");
      npsetstring[i][j++] = new TString("LepVeto");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Single Top");
      npsetstring[i][j++] = new TString("stop");
      npsetstring[i][j++] = new TString("Chan");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("ttbar");
      npsetstring[i][j++] = new TString("norm_ttbar");
      npsetstring[i][j++] = new TString("TopPt");
      npsetstring[i][j++] = new TString("Ttbar");
      npsetstring[i][j++] = new TString("ttbarHighPtV");
      npsetstring[i][j++] = new TString("ttbarNorm");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("ttbar Norm");
      npsetstring[i][j++] = new TString("norm_ttbar");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("ttbar Model");
      npsetstring[i][j++] = new TString("TopPt");
      npsetstring[i][j++] = new TString("Ttbar");
      npsetstring[i][j++] = new TString("ttbarHighPtV");
      npsetstring[i][j++] = new TString("ttbarNorm");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Float + Norm");
      npsetstring[i][j++] = new TString("norm");
      npsetstring[i][j++] = new TString("Norm");
      npsetstring[i][j++] = new TString("Ratio");
      npsetstring[i][j++] = new TString("MJ_");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Float");
      npsetstring[i][j++] = new TString("norm");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Norm");
      npsetstring[i][j++] = new TString("Norm");
      npsetstring[i][j++] = new TString("Ratio");
      npsetstring[i][j++] = new TString("MJ_");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Lumi");
      npsetstring[i][j++] = new TString("LUMI_2012");

    }

    else if( mode == 4 ) {
      npsetname[3] = new TString("Top shape systematics");
      // npsetstring[3][0]    = new TString("SysTTbarPTV");
      // npsetstring[3][1]    = new TString("SysTTbarMBB");
      npsetstring[3][0] = new TString("SysTTbarPTVMBB");
      //
      npsetname[4] = new TString("All but top shape systematics");
      // npsetstring[4][0]    = new TString("SysTTbarPTV");
      // npsetstring[4][1]    = new TString("SysTTbarMBB");
      npsetstring[4][0] = new TString("SysTTbarPTVMBB");
      npsetexclude[4]   = true;

    }

    else if( mode == 5 ) {
      npsetname[3]      = new TString("MC stat");
      npsetstring[3][0] = new TString("gamma");

      npsetname[4]      = new TString("All Sys");
      npsetstring[4][0] = new TString("gamma");
      npsetexclude[4]   = true;

    }

    else if( mode == 6 ) {
      npsetname[3]      = new TString("TTbar syst");
      npsetstring[3][0] = new TString("TTbar");

      npsetname[4]      = new TString("TTbar syst and ttbar norm");
      npsetstring[4][0] = new TString("TTbar");
      npsetstring[4][1] = new TString("ttbar");

      npsetname[4]      = new TString("All but TTBar syst");
      npsetstring[4][0] = new TString("TTbar");
      npsetexclude[4]   = true;

      npsetname[5]      = new TString("All but TTBar syst and ttbar norm");
      npsetstring[5][0] = new TString("TTbar");
      npsetstring[5][1] = new TString("ttbar");
      npsetexclude[5]   = true;

    } else if( mode == 7 ) {
      npsetname[3]      = new TString("V syst");
      npsetstring[3][0] = new TString("ZPtV");
      npsetstring[3][1] = new TString("WPtV");
      npsetstring[3][2] = new TString("ZMbb");
      npsetstring[3][3] = new TString("WMbb");

      npsetname[4]      = new TString("All but V syst");
      npsetstring[4][0] = new TString("ZPtV");
      npsetstring[4][1] = new TString("WPtV");
      npsetstring[4][2] = new TString("ZMbb");
      npsetstring[4][3] = new TString("WMbb");
      npsetexclude[4]   = true;

    } else if( mode == 8 ) {
      // SM Htautau.
      npsetname[3]      = new TString("Ztt normalization");
      npsetstring[3][0] = new TString("_Ztt");

      npsetname[4]      = new TString("All normalizations");
      npsetstring[4][0] = new TString("norm");
      npsetstring[4][1] = new TString("Norm");

      npsetname[5]      = new TString("All but normalizations");
      npsetstring[5][0] = new TString("norm");
      npsetstring[5][1] = new TString("Norm");
      npsetexclude[5]   = true;

      npsetname[6]      = new TString("Jets MET");
      npsetstring[6][0] = new TString("MET");
      npsetstring[6][1] = new TString("JES");
      npsetstring[6][2] = new TString("JER");
      npsetstring[6][3] = new TString("JVT");
      npsetstring[6][4] = new TString("jet");

      npsetname[7]      = new TString("BTag");
      npsetstring[7][0] = new TString("FT_EFF");

      npsetname[8]      = new TString("Electron Muon");
      npsetstring[8][0] = new TString("EG");
      npsetstring[8][1] = new TString("EL_EFF");
      npsetstring[8][2] = new TString("MUON");

      npsetname[9]      = new TString("Tau");
      npsetstring[9][0] = new TString("TAU");

      npsetname[10]      = new TString("Pileup reweighting");
      npsetstring[10][0] = new TString("PRW");

      npsetname[11]      = new TString("Fake estimation");
      npsetstring[11][0] = new TString("fake");
      npsetstring[11][1] = new TString("dPhi");

      npsetname[12]      = new TString("Luminosity");
      npsetstring[12][0] = new TString("LumiUnc");

      npsetname[13]      = new TString("Theory unc. (Signal)");
      npsetstring[13][0] = new TString("ATLAS_BR_tautau");
      npsetstring[13][1] = new TString("ATLAS_UE");
      npsetstring[13][2] = new TString("QCDscale_");
      npsetstring[13][3] = new TString("NLO_EW_Higgs");
      npsetstring[13][4] = new TString("pdf_Higgs");
      npsetstring[13][5] = new TString("Theo_");

      npsetname[14]      = new TString("Theory unc. (Ztautau)");
      npsetstring[14][0] = new TString("Z_EWK");
      npsetstring[14][1] = new TString("ZttTheory");

      npsetname[15]      = new TString("MC stat");
      npsetstring[15][0] = new TString("gamma");

    } else if( mode == 9 ) {
      // HHbbtautau.
      npsetname[3]      = new TString("All normalizations");
      npsetstring[3][0] = new TString("norm");
      npsetstring[3][1] = new TString("Norm");
      npsetname[4]      = new TString("All but normalizations");
      npsetstring[4][0] = new TString("norm");
      npsetstring[4][1] = new TString("Norm");
      npsetexclude[4]   = true;
      npsetname[5]      = new TString("Jets MET");
      npsetstring[5][0] = new TString("MET");
      npsetstring[5][1] = new TString("JES");
      npsetstring[5][2] = new TString("JER");
      npsetstring[5][3] = new TString("JVT");
      npsetstring[5][4] = new TString("JET");

      npsetname[6]      = new TString("BTag");
      npsetstring[6][0] = new TString("FT_EFF");

      npsetname[7]      = new TString("Electron Muon");
      npsetstring[7][0] = new TString("EG");
      npsetstring[7][1] = new TString("EL_EFF");
      npsetstring[7][2] = new TString("MUON");
      npsetstring[7][3] = new TString("MUONS");

      npsetname[8]      = new TString("Tau");
      npsetstring[8][0] = new TString("TAUS");

      npsetname[9]      = new TString("Pileup reweighting");
      npsetstring[9][0] = new TString("PRW");

      npsetname[10]      = new TString("Fake estimation");
      npsetstring[10][0] = new TString("Fake");
      npsetstring[10][1] = new TString("ANTITAU");
      npsetstring[10][2] = new TString("MCINCREASEF");
      npsetstring[10][3] = new TString("DECREASEFF");
      npsetstring[10][4] = new TString("FFStat");
      npsetstring[10][5] = new TString("SS");
      npsetstring[10][6] = new TString("Subtract");
      npsetstring[10][7] = new TString("FF_MTW");
      npsetstring[10][8] = new TString("FFQCD");

      npsetname[11]      = new TString("Luminosity");
      npsetstring[11][0] = new TString("LUMI");

      npsetname[12]      = new TString("Top Modelling");
      npsetstring[12][0] = new TString("TTBAR");
      npsetstring[12][1] = new TString("TTbarMBB");
      npsetstring[12][2] = new TString("TTbarPTH");
      npsetstring[12][3] = new TString("Stop");
      npsetstring[12][4] = new TString("norm_ttbar"); // Should we include norm?

      npsetname[13]      = new TString("Ztautau Modelling");
      npsetstring[13][0] = new TString("Ztautau");
      npsetstring[13][1] = new TString("norm_Zbb"); // Should we include norm?

      npsetname[14]      = new TString("MC stat");
      npsetstring[14][0] = new TString("gamma");

    } else if( mode == 10 ) { // This is Valerio's way
      int Vin = 3;

      npsetname[Vin]      = new TString("Floating normalizations");
      npsetstring[Vin][0] = new TString("ATLAS_norm");
      Vin++;

      npsetname[Vin]      = new TString("Multi Jet              ");
      npsetstring[Vin][0] = new TString("SysMJ");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: single top  ");
      npsetstring[Vin][0] = new TString("Sysstop");
      npsetstring[Vin][1] = new TString("SysStop");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: ttbar       ");
      npsetstring[Vin][0] = new TString("SysTTbar");
      npsetstring[Vin][1] = new TString("Systtbar");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: W+jets      ");
      npsetstring[Vin][0] = new TString("SysWMbb");
      npsetstring[Vin][1] = new TString("SysWPtV");
      npsetstring[Vin][2] = new TString("SysWb");
      npsetstring[Vin][3] = new TString("SysWc");
      npsetstring[Vin][4] = new TString("SysWl");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: Z+jets      ");
      npsetstring[Vin][0] = new TString("SysZMbb");
      npsetstring[Vin][1] = new TString("SysZPtV");
      npsetstring[Vin][2] = new TString("SysZb");
      npsetstring[Vin][3] = new TString("SysZc");
      npsetstring[Vin][4] = new TString("SysZl");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: Diboson     ");
      npsetstring[Vin][0] = new TString("SysVV");
      npsetstring[Vin][1] = new TString("SysWZ");
      npsetstring[Vin][2] = new TString("SysZZ");
      npsetstring[Vin][3] = new TString("SysVZ");
      npsetstring[Vin][4] = new TString("SysWW");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: VH          ");
      npsetstring[Vin][0] = new TString("SysTheory");
      npsetstring[Vin][1] = new TString("SysVH");
      Vin++;

      ///////////////////////////////////////////////////////////////////////////////////////

      npsetname[Vin]      = new TString("Detector: lepton       ");
      npsetstring[Vin][0] = new TString("SysEG");
      npsetstring[Vin][1] = new TString("SysEL");
      npsetstring[Vin][2] = new TString("SysMUON");
      Vin++;

      npsetname[Vin]      = new TString("Detector: MET          ");
      npsetstring[Vin][0] = new TString("SysMET");
      Vin++;

      npsetname[Vin]      = new TString("Detector: JET          ");
      npsetstring[Vin][0] = new TString("SysJET");
      Vin++;

      npsetname[Vin]      = new TString("Detector: FTAG (b-jet) ");
      npsetstring[Vin][0] = new TString("SysFT_EFF_Eigen_B");
      Vin++;

      npsetname[Vin]      = new TString("Detector: FTAG (c-jet) ");
      npsetstring[Vin][0] = new TString("SysFT_EFF_Eigen_C");
      Vin++;

      npsetname[Vin]      = new TString("Detector: FTAG (l-jet) ");
      npsetstring[Vin][0] = new TString("SysFT_EFF_Eigen_Light");
      Vin++;

      npsetname[Vin]      = new TString("Detector: FTAG (extrap)");
      npsetstring[Vin][0] = new TString("SysFT_EFF_extrap");
      Vin++;

      npsetname[Vin]      = new TString("Detector: PU           ");
      npsetstring[Vin][0] = new TString("SysPRW_DATASF");
      Vin++;

      npsetname[Vin]      = new TString("Lumi                   ");
      npsetstring[Vin][0] = new TString("ATLAS_LUMI");
      Vin++;

      //////////////////////////////////////////////////////////////////////////////////////

      npsetname[Vin]      = new TString("MC stat                ");
      npsetstring[Vin][0] = new TString("gamma");
      Vin++;

    }
    ////  STXS paper mode: floating norms in data ////
    else if( mode == 11 ) {
      int Vin           = 3;
      npsetname[1]      = new TString("DataStat                ");
      npsetstring[1][0] = new TString("ATLAS_norm");
      npsetstring[1][1] = new TString("gamma_MCStat"); // top-emu CR data stat. uncertainties (resolved VHbb)
      npsetsubtract[1]  = false;
      npsetexclude[1]   = true;

      npsetname[Vin]     = new TString("Data stat only          ");
      npsetexclude[Vin]  = true;
      npsetsubtract[Vin] = false;
      Vin++;

      npsetname[Vin]      = new TString("Top-emu CR stat         ");
      npsetstring[Vin][0] = new TString("gamma_MCStat");
      Vin++;

      npsetname[Vin]      = new TString("Floating normalizations ");
      npsetstring[Vin][0] = new TString("ATLAS_norm");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: VH           ");
      npsetstring[Vin][0] = new TString("SysTheory");
      npsetstring[Vin][1] = new TString("SysVH");
      npsetstring[Vin][2] = new TString("QCDScaleDelta");
      Vin++;

      int j                 = 0;
      npsetname[Vin]        = new TString("Modelling: Background   ");
      npsetstring[Vin][j++] = new TString("SysMJ");
      npsetstring[Vin][j++] = new TString("Sysstop");
      npsetstring[Vin][j++] = new TString("SysStop");
      npsetstring[Vin][j++] = new TString("SysTTbar");
      npsetstring[Vin][j++] = new TString("Systtbar");
      npsetstring[Vin][j++] = new TString("SysW");
      npsetstring[Vin][j++] = new TString("SysZ");
      npsetstring[Vin][j++] = new TString("SysVV");
      npsetstring[Vin][j++] = new TString("SysVZ");
      npsetstring[Vin][j++] = new TString("gamma_stat");
      Vin++;
      j = 0;

      npsetname[Vin]      = new TString("Multi Jet               ");
      npsetstring[Vin][0] = new TString("SysMJ");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: single top   ");
      npsetstring[Vin][0] = new TString("Sysstop");
      npsetstring[Vin][1] = new TString("SysStop");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: ttbar        ");
      npsetstring[Vin][0] = new TString("SysTTbar");
      npsetstring[Vin][1] = new TString("Systtbar");
      npsetstring[Vin][2] = new TString("SysBDTr_ttbar");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: W+jets       ");
      npsetstring[Vin][0] = new TString("SysWMbb");
      npsetstring[Vin][1] = new TString("SysWPtV");
      npsetstring[Vin][2] = new TString("SysBDTr_W");
      npsetstring[Vin][3] = new TString("SysWb");
      npsetstring[Vin][4] = new TString("SysWc");
      npsetstring[Vin][5] = new TString("SysWl");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: Z+jets       ");
      npsetstring[Vin][0] = new TString("SysZMbb");
      npsetstring[Vin][1] = new TString("SysZPtV");
      npsetstring[Vin][2] = new TString("SysZb");
      npsetstring[Vin][3] = new TString("SysZc");
      npsetstring[Vin][4] = new TString("SysZl");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: Diboson      ");
      npsetstring[Vin][0] = new TString("SysVV");
      npsetstring[Vin][1] = new TString("SysWZ");
      npsetstring[Vin][2] = new TString("SysZZ");
      npsetstring[Vin][3] = new TString("SysVZ");
      npsetstring[Vin][4] = new TString("SysWW");
      Vin++;

      npsetname[Vin]      = new TString("MC stat                 ");
      npsetstring[Vin][0] = new TString("gamma_stat");
      Vin++;

      ///////////////////////////////////////////////////////////////////////////////////////

      npsetname[Vin]        = new TString("Experimental Syst       ");
      npsetstring[Vin][j++] = new TString("SysEG");
      npsetstring[Vin][j++] = new TString("SysEL");
      npsetstring[Vin][j++] = new TString("SysMUON");
      npsetstring[Vin][j++] = new TString("SysMET");
      npsetstring[Vin][j++] = new TString("SysJET");
      npsetstring[Vin][j++] = new TString("SysFT_EFF_Eigen_");
      npsetstring[Vin][j++] = new TString("SysPRW_DATASF");
      npsetstring[Vin][j++] = new TString("ATLAS_LUMI");
      Vin++;
      j = 0;

      npsetname[Vin]      = new TString("Detector: lepton        ");
      npsetstring[Vin][0] = new TString("SysEG");
      npsetstring[Vin][1] = new TString("SysEL");
      npsetstring[Vin][2] = new TString("SysMUON");
      Vin++;

      npsetname[Vin]      = new TString("Detector: MET           ");
      npsetstring[Vin][0] = new TString("SysMET");
      Vin++;

      npsetname[Vin]      = new TString("Detector: JET           ");
      npsetstring[Vin][0] = new TString("SysJET");
      Vin++;

      npsetname[Vin]      = new TString("Detector: FTAG (b-jet)  ");
      npsetstring[Vin][0] = new TString("SysFT_EFF_Eigen_B");
      Vin++;

      npsetname[Vin]      = new TString("Detector: FTAG (c-jet)  ");
      npsetstring[Vin][0] = new TString("SysFT_EFF_Eigen_C");
      Vin++;

      npsetname[Vin]      = new TString("Detector: FTAG (l-jet)  ");
      npsetstring[Vin][0] = new TString("SysFT_EFF_Eigen_Light");
      Vin++;

      npsetname[Vin]      = new TString("Detector: FTAG (extrap) ");
      npsetstring[Vin][0] = new TString("SysFT_EFF_extrap");
      Vin++;

      npsetname[Vin]      = new TString("Detector: PU            ");
      npsetstring[Vin][0] = new TString("SysPRW_DATASF");
      Vin++;

      npsetname[Vin]      = new TString("Lumi                    ");
      npsetstring[Vin][0] = new TString("ATLAS_LUMI");
      Vin++;

      //////////////////////////////////////////////////////////////////////////////////////
    } else if( mode == 12 ) {
      //*********************************************************************************
      //*********************************************************************************
      //
      //              STXS systematics dedicated mode
      //
      //*********************************************************************************
      //*********************************************************************************
      int Vin = 3;
      // npsetname[Vin]      = new TString("Modelling: VH STXS UEPS"); // when this update, we will have a look
      // npsetstring[Vin][0] = new TString("SysTheoryUEPS");
      // Vin++;

      npsetname[Vin]      = new TString("Modelling: STXS QCD ");
      npsetstring[Vin][0] = new TString("SysTheoryQCD");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: STXS PDF ");
      npsetstring[Vin][0] = new TString("SysTheoryPDF_");
      npsetstring[Vin][1] = new TString("SysTheoryalphas");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: STXS HistoSys ");
      npsetstring[Vin][0] = new TString("SysVH");
      Vin++;

    }
    //*****************************************
    //              Boosted VHbb
    //*****************************************
    else if( mode == 13 ) {
      int Vin           = 3;
      npsetname[1]      = new TString("DataStat                ");
      npsetstring[1][0] = new TString("not@ATLAS_norm");
      npsetsubtract[1]  = false;
      npsetexclude[1]   = false;

      npsetname[Vin]     = new TString("Data stat only          ");
      npsetexclude[Vin]  = true;
      npsetsubtract[Vin] = false;
      Vin++;

      npsetname[Vin]      = new TString("Floating normalizations ");
      npsetstring[Vin][0] = new TString("ATLAS_norm");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: VH           ");
      npsetstring[Vin][0] = new TString("SysTheory");
      npsetstring[Vin][1] = new TString("SysVH");
      npsetstring[Vin][2] = new TString("_Sig");
      npsetstring[Vin][3] = new TString("QCDScaleDelta");
      Vin++;

      int j                 = 0;
      npsetname[Vin]        = new TString("Modelling: Background   ");
      npsetstring[Vin][j++] = new TString("multijetEl");
      npsetstring[Vin][j++] = new TString("Sysstop");
      npsetstring[Vin][j++] = new TString("SysStop");
      npsetstring[Vin][j++] = new TString("J0_Stop");
      npsetstring[Vin][j++] = new TString("400_Stop");
      npsetstring[Vin][j++] = new TString("topaddbjetcr_Stop");
      npsetstring[Vin][j++] = new TString("SysTTbar");
      npsetstring[Vin][j++] = new TString("Systtbar");
      npsetstring[Vin][j++] = new TString("J0_ttbar");
      npsetstring[Vin][j++] = new TString("L0_ttbar");
      npsetstring[Vin][j++] = new TString("L1_ttbar");
      npsetstring[Vin][j++] = new TString("SysWMbb");
      npsetstring[Vin][j++] = new TString("SysWPtV");
      npsetstring[Vin][j++] = new TString("SysWb");
      npsetstring[Vin][j++] = new TString("SysWc");
      npsetstring[Vin][j++] = new TString("SysWl");
      npsetstring[Vin][j++] = new TString("_Whf");
      npsetstring[Vin][j++] = new TString("SysZMbb");
      npsetstring[Vin][j++] = new TString("SysZPtV");
      npsetstring[Vin][j++] = new TString("SysZb");
      npsetstring[Vin][j++] = new TString("SysZc");
      npsetstring[Vin][j++] = new TString("SysZl");
      npsetstring[Vin][j++] = new TString("_Zhf");
      npsetstring[Vin][j++] = new TString("SysVV");
      npsetstring[Vin][j++] = new TString("SysVZ");
      npsetstring[Vin][j++] = new TString("SysWZ");
      npsetstring[Vin][j++] = new TString("SysZZ");
      npsetstring[Vin][j++] = new TString("SysWW");
      npsetstring[Vin][j++] = new TString("_ZZ_");
      npsetstring[Vin][j++] = new TString("_WZ_");
      npsetstring[Vin][j++] = new TString("gamma");
      Vin++;
      j = 0;

      npsetname[Vin]      = new TString("Multi Jet               ");
      npsetstring[Vin][0] = new TString("multijetEl");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: single top   ");
      npsetstring[Vin][0] = new TString("Sysstop");
      npsetstring[Vin][1] = new TString("SysStop");
      npsetstring[Vin][2] = new TString("J0_Stop");
      npsetstring[Vin][3] = new TString("400_Stop");
      npsetstring[Vin][4] = new TString("topaddbjetcr_Stop");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: ttbar        ");
      npsetstring[Vin][0] = new TString("SysTTbar");
      npsetstring[Vin][1] = new TString("Systtbar");
      npsetstring[Vin][2] = new TString("J0_ttbar");
      npsetstring[Vin][3] = new TString("L0_ttbar");
      npsetstring[Vin][4] = new TString("L1_ttbar");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: W+jets       ");
      npsetstring[Vin][0] = new TString("SysWMbb");
      npsetstring[Vin][1] = new TString("SysWPtV");
      npsetstring[Vin][2] = new TString("SysWb");
      npsetstring[Vin][3] = new TString("SysWc");
      npsetstring[Vin][4] = new TString("SysWl");
      npsetstring[Vin][5] = new TString("_Whf");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: Z+jets       ");
      npsetstring[Vin][0] = new TString("SysZMbb");
      npsetstring[Vin][1] = new TString("SysZPtV");
      npsetstring[Vin][2] = new TString("SysZb");
      npsetstring[Vin][3] = new TString("SysZc");
      npsetstring[Vin][4] = new TString("SysZl");
      npsetstring[Vin][5] = new TString("_Zhf");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: Diboson      ");
      npsetstring[Vin][0] = new TString("SysVV");
      npsetstring[Vin][1] = new TString("SysWZ");
      npsetstring[Vin][2] = new TString("SysZZ");
      npsetstring[Vin][3] = new TString("SysVZ");
      npsetstring[Vin][4] = new TString("SysWW");
      npsetstring[Vin][5] = new TString("_WZ_");
      npsetstring[Vin][6] = new TString("_ZZ_");
      npsetstring[Vin][7] = new TString("_VZ_");
      Vin++;

      npsetname[Vin]      = new TString("MC stat                 ");
      npsetstring[Vin][0] = new TString("gamma");
      Vin++;

      ///////////////////////////////////////////////////////////////////////////////////////

      npsetname[Vin]        = new TString("Experimental Syst       ");
      npsetstring[Vin][j++] = new TString("SysEG");
      npsetstring[Vin][j++] = new TString("SysEL");
      npsetstring[Vin][j++] = new TString("SysMUON");
      npsetstring[Vin][j++] = new TString("SysMET");
      npsetstring[Vin][j++] = new TString("SysJET");
      npsetstring[Vin][j++] = new TString("SysFATJET");
      npsetstring[Vin][j++] = new TString("SysFT_EFF_Eigen_");
      npsetstring[Vin][j++] = new TString("SysPRW_DATASF");
      npsetstring[Vin][j++] = new TString("ATLAS_LUMI");
      Vin++;
      j = 0;

      npsetname[Vin]      = new TString("Detector: lepton        ");
      npsetstring[Vin][0] = new TString("SysEG");
      npsetstring[Vin][1] = new TString("SysEL");
      npsetstring[Vin][2] = new TString("SysMUON");
      Vin++;

      npsetname[Vin]      = new TString("Detector: MET           ");
      npsetstring[Vin][0] = new TString("SysMET");
      Vin++;

      npsetname[Vin]      = new TString("Detector: JET           ");
      npsetstring[Vin][0] = new TString("SysJET");
      Vin++;

      npsetname[Vin]      = new TString("Detector: FATJET           ");
      npsetstring[Vin][0] = new TString("SysFATJET");
      npsetstring[Vin][1] = new TString("SysMJJMR");
      Vin++;

      npsetname[Vin]      = new TString("Detector: FTAG (b-jet)  ");
      npsetstring[Vin][0] = new TString("SysFT_EFF_Eigen_B");
      Vin++;

      npsetname[Vin]      = new TString("Detector: FTAG (c-jet)  ");
      npsetstring[Vin][0] = new TString("SysFT_EFF_Eigen_C");
      Vin++;

      npsetname[Vin]      = new TString("Detector: FTAG (l-jet)  ");
      npsetstring[Vin][0] = new TString("SysFT_EFF_Eigen_Light");
      Vin++;

      npsetname[Vin]      = new TString("Detector: FTAG (extrap) ");
      npsetstring[Vin][0] = new TString("SysFT_EFF_extrap");
      Vin++;

      npsetname[Vin]      = new TString("Detector: PU            ");
      npsetstring[Vin][0] = new TString("SysPRW_DATASF");
      Vin++;

      npsetname[Vin]      = new TString("Lumi                    ");
      npsetstring[Vin][0] = new TString("ATLAS_LUMI");
      Vin++;

    } else if( mode == 14 ) { // short sys+stat breakdown onlyl; DataStat includes floating norms; data stat only
                              // doesn't
      int Vin           = 3;
      npsetname[1]      = new TString("DataStat                ");
      npsetstring[1][0] = new TString("not@ATLAS_norm");
      npsetsubtract[1]  = false;
      npsetexclude[1]   = false;

      npsetname[Vin]     = new TString("Data stat only          ");
      npsetexclude[Vin]  = true;
      npsetsubtract[Vin] = false;
      Vin++;

      npsetname[Vin]      = new TString("Floating normalizations ");
      npsetstring[Vin][0] = new TString("ATLAS_norm");
      Vin++;

    }
    ////  super short - mu plot only ////
    else if( mode == 15 ) {
      int Vin           = 3;
      npsetname[1]      = new TString("DataStat                ");
      npsetstring[1][0] = new TString("ATLAS_norm");
      npsetstring[1][1] = new TString("gamma_MCStat"); // top-emu CR data stat. uncertainties (resolved VHbb)
      npsetsubtract[1]  = false;
      npsetexclude[1]   = true;

    }
    //*****************************************
    //              VH(cc)
    //*****************************************
    else if( mode == 16 ) {
      int Vin           = 3;
      npsetname[1]      = new TString("DataStat                ");
      npsetstring[1][0] = new TString("not@ATLAS_norm");
      npsetsubtract[1]  = false;
      npsetexclude[1]   = false;

      npsetname[Vin]     = new TString("Data stat only          ");
      npsetexclude[Vin]  = true;
      npsetsubtract[Vin] = false;
      Vin++;

      npsetname[Vin]      = new TString("Floating normalizations ");
      npsetstring[Vin][0] = new TString("ATLAS_norm");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: VHcc           ");
      npsetstring[Vin][0] = new TString("Hcc");
      npsetstring[Vin][1] = new TString("Higgs");
      npsetstring[Vin][2] = new TString("VHNLOEWK");
      Vin++;

      int j                 = 0;
      npsetname[Vin]        = new TString("Modelling: Background   ");
      npsetstring[Vin][j++] = new TString("SysMJ");
      npsetstring[Vin][j++] = new TString("SysMU");
      npsetstring[Vin][j++] = new TString("stop");
      npsetstring[Vin][j++] = new TString("Stop");
      npsetstring[Vin][j++] = new TString("SysdRCRextrap");
      npsetstring[Vin][j++] = new TString("SysZ");
      npsetstring[Vin][j++] = new TString("SysW");
      npsetstring[Vin][j++] = new TString("SysTop");
      npsetstring[Vin][j++] = new TString("SysTTbar");
      npsetstring[Vin][j++] = new TString("SysPtVAcc");
      npsetstring[Vin][j++] = new TString("SysNJetAcc");
      npsetstring[Vin][j++] = new TString("Hbb");
      npsetstring[Vin][j++] = new TString("Higgs");
      Vin++;
      j = 0;

      npsetname[Vin]      = new TString("Multi Jet               ");
      npsetstring[Vin][0] = new TString("SysMJ");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: Top        ");
      npsetstring[Vin][0] = new TString("SysTTbar");
      npsetstring[Vin][1] = new TString("SysMUR_BMin150_Ttbar");
      npsetstring[Vin][2] = new TString("SysMUR_BMin75_Ttbar");
      npsetstring[Vin][3] = new TString("SysMUF_Ttbar");
      npsetstring[Vin][4] = new TString("stop");
      npsetstring[Vin][5] = new TString("Stop");
      npsetstring[Vin][6] = new TString("SysTop");
      npsetstring[Vin][7] = new TString("SysNJetAcc_Top");
      Vin++;

      npsetname[Vin]       = new TString("Modelling: W+jets       ");
      npsetstring[Vin][0]  = new TString("SysWhf");
      npsetstring[Vin][1]  = new TString("SysWmf");
      npsetstring[Vin][2]  = new TString("SysWl");
      npsetstring[Vin][3]  = new TString("SysNJetAcc_Whf");
      npsetstring[Vin][4]  = new TString("SysNJetAcc_Wmf");
      npsetstring[Vin][5]  = new TString("SysNJetAcc_Wl");
      npsetstring[Vin][6]  = new TString("SysNJetAcc_Wtau");
      npsetstring[Vin][7]  = new TString("SysWb");
      npsetstring[Vin][8]  = new TString("SysWhtau");
      npsetstring[Vin][9]  = new TString("SysWltau");
      npsetstring[Vin][10] = new TString("SysMUR_BMin150_W");
      npsetstring[Vin][11] = new TString("SysMUF_W");
      npsetstring[Vin][12] = new TString("SysdRCRextrap");
      Vin++;

      npsetname[Vin]       = new TString("Modelling: Z+jets       ");
      npsetstring[Vin][0]  = new TString("SysZhf");
      npsetstring[Vin][1]  = new TString("SysZmf");
      npsetstring[Vin][2]  = new TString("SysZl");
      npsetstring[Vin][3]  = new TString("SysPtVAccLow_Zhf");
      npsetstring[Vin][4]  = new TString("SysPtVAccLow_Zmf");
      npsetstring[Vin][5]  = new TString("SysPtVAccLow_Zl");
      npsetstring[Vin][6]  = new TString("SysNJetAcc_Zhf");
      npsetstring[Vin][7]  = new TString("SysNJetAcc_Zmf");
      npsetstring[Vin][8]  = new TString("SysNJetAcc_Zl");
      npsetstring[Vin][9]  = new TString("SysZb");
      npsetstring[Vin][10] = new TString("SysMUR_BMin75_Z");
      npsetstring[Vin][11] = new TString("SysMUR_BMin150_Z");
      npsetstring[Vin][12] = new TString("SysMUF_Z");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: Diboson      ");
      npsetstring[Vin][0] = new TString("WW");
      npsetstring[Vin][1] = new TString("WZ");
      npsetstring[Vin][2] = new TString("ZZ");
      npsetstring[Vin][3] = new TString("Diboson");
      npsetstring[Vin][4] = new TString("WlepZhad");
      npsetstring[Vin][5] = new TString("WhadZlep");
      Vin++;

      npsetname[Vin]      = new TString("Modelling: Hbb                 ");
      npsetstring[Vin][0] = new TString("Hbb");
      npsetstring[Vin][1] = new TString("Higgs");
      npsetstring[Vin][2] = new TString("VHNLOEWK");
      Vin++;

      npsetname[Vin]      = new TString("MC stat                 ");
      npsetstring[Vin][0] = new TString("gamma");
      Vin++;

      ///////////////////////////////////////////////////////////////////////////////////////

      npsetname[Vin]        = new TString("Experimental Syst (excl FTAG)       ");
      npsetstring[Vin][j++] = new TString("SysEG");
      npsetstring[Vin][j++] = new TString("SysEL");
      npsetstring[Vin][j++] = new TString("SysMUON");
      npsetstring[Vin][j++] = new TString("SysTAUS");
      npsetstring[Vin][j++] = new TString("SysMET");
      npsetstring[Vin][j++] = new TString("SysJET");
      npsetstring[Vin][j++] = new TString("SysPRW_DATASF");
      npsetstring[Vin][j++] = new TString("ATLAS_LUMI");
      Vin++;
      j = 0;

      npsetname[Vin]        = new TString("Flavour tagging       ");
      npsetstring[Vin][j++] = new TString("SysFT_EFF");
      npsetstring[Vin][j++] = new TString("SysTT_dR");
      npsetstring[Vin][j++] = new TString("SysDT2");
      Vin++;
      j = 0;

      npsetname[Vin]      = new TString("Detector: lepton        ");
      npsetstring[Vin][0] = new TString("SysEG");
      npsetstring[Vin][1] = new TString("SysEL");
      npsetstring[Vin][2] = new TString("SysMUON");
      npsetstring[Vin][3] = new TString("SysTAUS");
      Vin++;

      npsetname[Vin]      = new TString("Detector: MET           ");
      npsetstring[Vin][0] = new TString("SysMET");
      Vin++;

      npsetname[Vin]      = new TString("Detector: JET           ");
      npsetstring[Vin][0] = new TString("SysJET");
      Vin++;

      npsetname[Vin]      = new TString("Detector: JER           ");
      npsetstring[Vin][0] = new TString("SysJET_CR_JET_JER");
      Vin++;

      npsetname[Vin]      = new TString("Detector: FTAG (b-jet)  ");
      npsetstring[Vin][0] = new TString("SysFT_EFF_Eigen_B");
      Vin++;

      npsetname[Vin]      = new TString("Detector: FTAG (c-jet)  ");
      npsetstring[Vin][0] = new TString("SysFT_EFF_Eigen_C");
      Vin++;

      npsetname[Vin]      = new TString("Detector: FTAG (l-jet)  ");
      npsetstring[Vin][0] = new TString("SysFT_EFF_Eigen_Light");
      Vin++;

      npsetname[Vin]      = new TString("Detector: FTAG (extrap) ");
      npsetstring[Vin][0] = new TString("SysFT_EFF_extrap");
      npsetstring[Vin][1] = new TString("SysFT_EFF_Eigen_T");
      Vin++;

      npsetname[Vin]      = new TString("TT dR                 ");
      npsetstring[Vin][0] = new TString("SysTT_dR");
      Vin++;

      npsetname[Vin]      = new TString("TT non-closure                 ");
      npsetstring[Vin][0] = new TString("SysDT2");
      Vin++;

      npsetname[Vin]      = new TString("Detector: PU/Lumi            ");
      npsetstring[Vin][0] = new TString("SysPRW_DATASF");
      npsetstring[Vin][1] = new TString("ATLAS_LUMI");
      Vin++;

    }

    //*********************************************************************************
    //*********************************************************************************
    //              Mode 20---Combined Run1+Run2 breakdown
    //            (can be run on Run1, Run2, or combined ok)
    //*********************************************************************************
    //*********************************************************************************

    else if( mode == 20 ) {
      int i = 2, j = 0;

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Floating normalizations");
      npsetstring[i][j++] = new TString("norm");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("All normalizations");
      npsetstring[i][j++] = new TString("norm");
      npsetstring[i][j++] = new TString("Norm");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("All but normalizations");
      npsetstring[i][j++] = new TString("norm"); // W,Z,ttbar (also multijet in Run 1)
      npsetstring[i][j++] = new TString("Norm");
      npsetexclude[i]     = true;

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Jets, MET");
      npsetstring[i][j++] = new TString("SysJET");
      npsetstring[i][j++] = new TString("SysMET");
      npsetstring[i][j++] = new TString("SysJet"); // Run1
      npsetstring[i][j++] = new TString("JVF");    // Run1
      npsetstring[i][j++] = new TString("SysFATJET");
      npsetstring[i][j++] = new TString("SysJER");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Jets");
      npsetstring[i][j++] = new TString("SysJET");
      npsetstring[i][j++] = new TString("SysJet"); // Run1
      npsetstring[i][j++] = new TString("JVF");    // Run1
      npsetstring[i][j++] = new TString("SysFATJET");
      npsetstring[i][j++] = new TString("SysJER");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("MET");
      npsetstring[i][j++] = new TString("SysMET");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag");
      npsetstring[i][j++] = new TString("SysFT");
      npsetstring[i][j++] = new TString("BTag");
      npsetstring[i][j++] = new TString("TruthTagDR");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag b");
      npsetstring[i][j++] = new TString("SysFT_EFF_Eigen_B");
      npsetstring[i][j++] = new TString("BTagB");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag c");
      npsetstring[i][j++] = new TString("SysFT_EFF_Eigen_C");
      npsetstring[i][j++] = new TString("BTagC");
      npsetstring[i][j++] = new TString("SysFT_EFF_extrapolation_from_charm");
      npsetstring[i][j++] = new TString("TruthTagDR");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag light");
      npsetstring[i][j++] = new TString("SysFT_EFF_Eigen_Light");
      npsetstring[i][j++] = new TString("BTagL");
      npsetstring[i][j++] = new TString("SysFT_EFF_extrapolation_1");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Leptons");
      npsetstring[i][j++] = new TString("SysEG");
      npsetstring[i][j++] = new TString("SysEL");
      npsetstring[i][j++] = new TString("SysMUON");
      npsetstring[i][j++] = new TString("Elec");
      npsetstring[i][j++] = new TString("Muon");
      npsetstring[i][j++] = new TString("LepVeto");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Luminosity");
      npsetstring[i][j++] = new TString("LUMI");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Diboson");
      npsetstring[i][j++] = new TString("SysVV"); // to keep out Run1 "VHVV" systs; which are, incidentally, jets
      npsetstring[i][j++] = new TString("WW");
      npsetstring[i][j++] = new TString("ZZ");
      npsetstring[i][j++] = new TString("WZ");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Zjets");
      npsetstring[i][j++] = new TString("ZDPhi");
      npsetstring[i][j++] = new TString("ZcDPhi"); // 7 TeV
      npsetstring[i][j++] = new TString("ZbDPhi"); // 7 TeV
      npsetstring[i][j++] = new TString("ZMbb");
      npsetstring[i][j++] = new TString("ZPt");
      npsetstring[i][j++] = new TString("Zcl");
      npsetstring[i][j++] = new TString("sZbb"); // for Zbb systs other than floating normalization, which always look
                                                 // like "*SysZbb*" (as opposed to "*norm_Z*")
      npsetstring[i][j++] = new TString("Zl");
      npsetstring[i][j++] = new TString("Zbc");
      npsetstring[i][j++] = new TString("Zbl");
      npsetstring[i][j++] = new TString("Zhf"); // Run1 only
      npsetstring[i][j++] = new TString("Zcc");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Zjets flt. norm.");
      npsetstring[i][j++] = new TString("norm_Z");

      i++;
      j            = 0;
      npsetname[i] = new TString("Model Wjets");
      /*Run 1 W+jets from mode 3
        "WPtV" (fine with "WPt");"WDPhi","WMbb" (same); "WbbRatio","WlNorm","WclNorm" (covered by "sWbb", "Wl", "Wcl");
        "WhfNorm" (new "Whf")
      */
      npsetstring[i][j++] = new TString("WJet"); // 7 TeV
      npsetstring[i][j++] = new TString("WDPhi");
      npsetstring[i][j++] = new TString("WMbb");
      npsetstring[i][j++] = new TString("WbbMbb");
      npsetstring[i][j++] = new TString("WPt");
      npsetstring[i][j++] = new TString("sWbb"); // for Wbb systs other than floating normalization, which always look
                                                 // like "*SysWbb*" (as opposed to "*norm_W*")
      npsetstring[i][j++] = new TString("Wbc");
      npsetstring[i][j++] = new TString("Wbl");
      npsetstring[i][j++] = new TString("Whf"); // Run1 only
      npsetstring[i][j++] = new TString("Wcc");
      npsetstring[i][j++] = new TString("WclNorm");
      npsetstring[i][j++] = new TString("Wl");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Wjets flt. norm.");
      npsetstring[i][j++] = new TString("norm_W");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model ttbar");
      npsetstring[i][j++] = new TString("TtBar");
      npsetstring[i][j++] = new TString("Ttbar");
      npsetstring[i][j++] = new TString("ttBarHigh");
      npsetstring[i][j++] = new TString("TopPt");
      npsetstring[i][j++] = new TString("TTbarPTV");
      npsetstring[i][j++] = new TString("TTbarMBB");
      npsetstring[i][j++] = new TString("TopMBB"); // 7 TeV
      npsetstring[i][j++] = new TString("sttbar");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("ttbar flt. norm.");
      npsetstring[i][j++] = new TString("norm_ttbar");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Single Top");
      npsetstring[i][j++] = new TString("stop");
      npsetstring[i][j++] = new TString("Stop");
      npsetstring[i][j++] = new TString("SysWt"); // 7 TeV

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Multi Jet");
      npsetstring[i][j++] = new TString("MJ");
      npsetstring[i][j++] = new TString("Multijet");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Signal Systematics");
      npsetstring[i][j++] = new TString("Theory");
      npsetstring[i][j++] = new TString("SysVH");
      npsetstring[i][j++] = new TString("BR");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("MC stat");
      npsetstring[i][j++] = new TString("gamma");

      //*********************************************************************************
      //*********************************************************************************
      //              Mode 21---just b-tagging (Run1 and/or Run2)
      //*********************************************************************************
      //*********************************************************************************
    } else if( mode == 21 ) {
      int i = 2, j = 0;
      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag");
      npsetstring[i][j++] = new TString("SysFT");
      npsetstring[i][j++] = new TString("BTag");
      npsetstring[i][j++] = new TString("TruthTagDR");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag b");
      npsetstring[i][j++] = new TString("SysFT_EFF_Eigen_B");
      npsetstring[i][j++] = new TString("BTagB");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag c");
      npsetstring[i][j++] = new TString("SysFT_EFF_Eigen_C");
      npsetstring[i][j++] = new TString("BTagC");
      npsetstring[i][j++] = new TString("SysFT_EFF_extrapolation_from_charm");
      npsetstring[i][j++] = new TString("TruthTagDR");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag light");
      npsetstring[i][j++] = new TString("SysFT_EFF_Eigen_Light");
      npsetstring[i][j++] = new TString("BTagL");
      npsetstring[i][j++] = new TString("SysFT_EFF_extrapolation_1");

      //*********************************************************************************
      //*********************************************************************************
      //              Mode 22---just Jets and total BTag (Run1 and/or Run2)
      //*********************************************************************************
      //*********************************************************************************
    } else if( mode == 22 ) {
      int i = 2, j = 0;
      i++;
      j                   = 0;
      npsetname[i]        = new TString("Jets");
      npsetstring[i][j++] = new TString("SysJET");
      npsetstring[i][j++] = new TString("SysJet"); // Run1
      npsetstring[i][j++] = new TString("JVF");    // Run1
      npsetstring[i][j++] = new TString("SysFATJET");
      npsetstring[i][j++] = new TString("SysJER");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag");
      npsetstring[i][j++] = new TString("SysFT");
      npsetstring[i][j++] = new TString("BTag");
      npsetstring[i][j++] = new TString("TruthTagDR");

      //*********************************************************************************
      //*********************************************************************************
      //              Mode 23---Run1 and/or Run2 modeling
      //*********************************************************************************
      //*********************************************************************************
    } else if( mode == 23 ) {
      int i = 2, j = 0;
      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Zjets, combined");
      npsetstring[i][j++] = new TString("ZDPhi");
      npsetstring[i][j++] = new TString("ZcDPhi"); // 7 TeV
      npsetstring[i][j++] = new TString("ZbDPhi"); // 7 TeV
      npsetstring[i][j++] = new TString("ZMbb");
      npsetstring[i][j++] = new TString("ZPt");
      npsetstring[i][j++] = new TString("Zcl");
      npsetstring[i][j++] = new TString("sZbb"); // for Zbb systs other than floating normalization, which always look
                                                 // like "*SysZbb*" (as opposed to "*norm_Z*")
      npsetstring[i][j++] = new TString("Zl");
      npsetstring[i][j++] = new TString("Zbc");
      npsetstring[i][j++] = new TString("Zbl");
      npsetstring[i][j++] = new TString("Zhf"); // Run1 only
      npsetstring[i][j++] = new TString("Zcc");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Zjets flt. norm.");
      npsetstring[i][j++] = new TString("norm_Z");

      i++;
      j            = 0;
      npsetname[i] = new TString("Model Wjets");
      /*Run 1 W+jets from mode 3
        "WPtV" (fine with "WPt");"WDPhi","WMbb" (same); "WbbRatio","WlNorm","WclNorm" (covered by "sWbb", "Wl", "Wcl");
        "WhfNorm" (new "Whf")
      */
      npsetstring[i][j++] = new TString("WJet"); // 7 TeV
      npsetstring[i][j++] = new TString("WDPhi");
      npsetstring[i][j++] = new TString("WMbb");
      npsetstring[i][j++] = new TString("WbbMbb");
      npsetstring[i][j++] = new TString("WPt");
      npsetstring[i][j++] = new TString("sWbb"); // for Wbb systs other than floating normalization, which always look
                                                 // like "*SysWbb*" (as opposed to "*norm_W*")
      npsetstring[i][j++] = new TString("Wbc");
      npsetstring[i][j++] = new TString("Wbl");
      npsetstring[i][j++] = new TString("Whf"); // Run1 only
      npsetstring[i][j++] = new TString("Wcc");
      npsetstring[i][j++] = new TString("WclNorm");
      npsetstring[i][j++] = new TString("Wl");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Wjets flt. norm.");
      npsetstring[i][j++] = new TString("norm_W");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model ttbar");
      npsetstring[i][j++] = new TString("TtBar");
      npsetstring[i][j++] = new TString("Ttbar");
      npsetstring[i][j++] = new TString("ttBarHigh");
      npsetstring[i][j++] = new TString("TopPt");
      npsetstring[i][j++] = new TString("TTbarPTV");
      npsetstring[i][j++] = new TString("TTbarMBB");
      npsetstring[i][j++] = new TString("TopMBB"); // 7 TeV
      npsetstring[i][j++] = new TString("sttbar");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("ttbar flt. norm.");
      npsetstring[i][j++] = new TString("norm_ttbar");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Single Top");
      npsetstring[i][j++] = new TString("stop");
      npsetstring[i][j++] = new TString("Stop");
      npsetstring[i][j++] = new TString("SysWt"); // 7 TeV

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Diboson");
      npsetstring[i][j++] = new TString("SysVV"); // to keep out Run1 "VHVV" systs; which are, incidentally, jets
      npsetstring[i][j++] = new TString("WW");
      npsetstring[i][j++] = new TString("ZZ");
      npsetstring[i][j++] = new TString("WZ");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Multi Jet");
      npsetstring[i][j++] = new TString("MJ");
      npsetstring[i][j++] = new TString("Multijet");

      //*********************************************************************************
      //*********************************************************************************
      //              Mode 24---Run1, Run2, and combined breakdowns (SLOW)
      //*********************************************************************************
      //*********************************************************************************
    } else if( mode == 24 ) {
      int i = 2, j = 0;

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Floating normalizations");
      npsetstring[i][j++] = new TString("norm");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("All normalizations");
      npsetstring[i][j++] = new TString("norm");
      npsetstring[i][j++] = new TString("Norm");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("All but normalizations");
      npsetstring[i][j++] = new TString("norm"); // W,Z,ttbar (also multijet in Run 1)
      npsetstring[i][j++] = new TString("Norm");
      npsetexclude[i]     = true;

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Jets, MET, combined");
      npsetstring[i][j++] = new TString("SysJET");
      npsetstring[i][j++] = new TString("SysMET");
      npsetstring[i][j++] = new TString("SysJet"); // Run1
      npsetstring[i][j++] = new TString("JVF");    // Run1
      npsetstring[i][j++] = new TString("SysFATJET");
      npsetstring[i][j++] = new TString("SysJER");
      i++;
      j                   = 0;
      npsetname[i]        = new TString("MET, combined");
      npsetstring[i][j++] = new TString("SysMET");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Jets, combined");
      npsetstring[i][j++] = new TString("SysJET");
      npsetstring[i][j++] = new TString("SysJet"); // Run1
      npsetstring[i][j++] = new TString("JVF");    // Run1
      npsetstring[i][j++] = new TString("SysFATJET");
      npsetstring[i][j++] = new TString("SysJER");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Jets, Run1");
      npsetstring[i][j++] = new TString("SysJet"); // Run1
      npsetstring[i][j++] = new TString("JVF");    // Run1
      npsetands[i]        = new TString("_78TeV"); // Run1

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Jets, Run2");
      npsetstring[i][j++] = new TString("SysJET");
      npsetstring[i][j++] = new TString("SysFATJET");
      npsetstring[i][j++] = new TString("SysJER");
      npsetands[i]        = new TString("_13TeV"); // Run2

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag, combined");
      npsetstring[i][j++] = new TString("SysFT");
      npsetstring[i][j++] = new TString("BTag");
      npsetstring[i][j++] = new TString("TruthTagDR");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag b, combined");
      npsetstring[i][j++] = new TString("SysFT_EFF_Eigen_B");
      npsetstring[i][j++] = new TString("BTagB");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag b, Run1");
      npsetstring[i][j++] = new TString("BTagB");
      npsetands[i]        = new TString("_78TeV"); // Run1

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag b, Run2");
      npsetstring[i][j++] = new TString("SysFT_EFF_Eigen_B");
      npsetands[i]        = new TString("_13TeV"); // Run2

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag c");
      npsetstring[i][j++] = new TString("SysFT_EFF_Eigen_C");
      npsetstring[i][j++] = new TString("BTagC");
      npsetstring[i][j++] = new TString("SysFT_EFF_extrapolation_from_charm");
      npsetstring[i][j++] = new TString("TruthTagDR");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag c, Run1");
      npsetstring[i][j++] = new TString("BTagC");
      npsetstring[i][j++] = new TString("TruthTagDR");
      npsetands[i]        = new TString("_78TeV"); // Run1

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag c, Run2");
      npsetstring[i][j++] = new TString("SysFT_EFF_Eigen_C");
      npsetstring[i][j++] = new TString("SysFT_EFF_extrapolation_from_charm");
      npsetands[i]        = new TString("_13TeV"); // Run2

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag light");
      npsetstring[i][j++] = new TString("SysFT_EFF_Eigen_Light");
      npsetstring[i][j++] = new TString("BTagL");
      npsetstring[i][j++] = new TString("SysFT_EFF_extrapolation_1");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag light, Run1");
      npsetstring[i][j++] = new TString("BTagL");
      npsetands[i]        = new TString("_78TeV"); // Run1

      i++;
      j                   = 0;
      npsetname[i]        = new TString("BTag light, Run2");
      npsetstring[i][j++] = new TString("SysFT_EFF_Eigen_Light");
      npsetstring[i][j++] = new TString("SysFT_EFF_extrapolation_1");
      npsetands[i]        = new TString("_13TeV"); // Run2

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Zjets, combined");
      npsetstring[i][j++] = new TString("ZDPhi");
      npsetstring[i][j++] = new TString("ZcDPhi"); // 7 TeV
      npsetstring[i][j++] = new TString("ZbDPhi"); // 7 TeV
      npsetstring[i][j++] = new TString("ZMbb");
      npsetstring[i][j++] = new TString("ZPt");
      npsetstring[i][j++] = new TString("Zcl");
      npsetstring[i][j++] = new TString("sZbb"); // for Zbb systs other than floating normalization, which always look
                                                 // like "*SysZbb*" (as opposed to "*norm_Z*")
      npsetstring[i][j++] = new TString("Zl");
      npsetstring[i][j++] = new TString("Zbc");
      npsetstring[i][j++] = new TString("Zbl");
      npsetstring[i][j++] = new TString("Zhf"); // Run1 only
      npsetstring[i][j++] = new TString("Zcc");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Zjets, Run1");
      npsetstring[i][j++] = new TString("ZDPhi");
      npsetstring[i][j++] = new TString("ZcDPhi"); // 7 TeV
      npsetstring[i][j++] = new TString("ZbDPhi"); // 7 TeV
      npsetstring[i][j++] = new TString("ZMbb");
      npsetstring[i][j++] = new TString("ZPt");
      npsetstring[i][j++] = new TString("Zcl");
      npsetstring[i][j++] = new TString("sZbb"); // for Zbb systs other than floating normalization, which always look
                                                 // like "*SysZbb*" (as opposed to "*norm_Z*")
      npsetstring[i][j++] = new TString("Zl");
      npsetstring[i][j++] = new TString("Zbc");
      npsetstring[i][j++] = new TString("Zbl");
      npsetstring[i][j++] = new TString("Zhf"); // Run1 only
      npsetstring[i][j++] = new TString("Zcc");
      npsetands[i]        = new TString("_78TeV"); // Run1

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Zjets, Run2");
      npsetstring[i][j++] = new TString("ZDPhi");
      npsetstring[i][j++] = new TString("ZMbb");
      npsetstring[i][j++] = new TString("ZPt");
      npsetstring[i][j++] = new TString("Zcl");
      npsetstring[i][j++] = new TString("sZbb"); // for Zbb systs other than floating normalization, which always look
                                                 // like "*SysZbb*" (as opposed to "*norm_Z*")
      npsetstring[i][j++] = new TString("Zl");
      npsetstring[i][j++] = new TString("Zbc");
      npsetstring[i][j++] = new TString("Zbl");
      npsetstring[i][j++] = new TString("Zcc");
      npsetands[i]        = new TString("_13TeV"); // Run2

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Zjets flt. norm., combined");
      npsetstring[i][j++] = new TString("norm_Z");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Zjets flt. norm., Run1");
      npsetstring[i][j++] = new TString("norm_Z");
      npsetands[i]        = new TString("_78TeV"); // Run1

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Zjets flt. norm., Run2");
      npsetstring[i][j++] = new TString("norm_Z");
      npsetands[i]        = new TString("_13TeV"); // Run2

      i++;
      j            = 0;
      npsetname[i] = new TString("Model Wjets, combined");
      /*Run 1 W+jets from mode 3
        "WPtV" (fine with "WPt");"WDPhi","WMbb" (same); "WbbRatio","WlNorm","WclNorm" (covered by "sWbb", "Wl", "Wcl");
        "WhfNorm" (new "Whf")
      */
      npsetstring[i][j++] = new TString("WJet"); // 7 TeV
      npsetstring[i][j++] = new TString("WDPhi");
      npsetstring[i][j++] = new TString("WMbb");
      npsetstring[i][j++] = new TString("WbbMbb");
      npsetstring[i][j++] = new TString("WPt");
      npsetstring[i][j++] = new TString("sWbb"); // for Wbb systs other than floating normalization, which always look
                                                 // like "*SysWbb*" (as opposed to "*norm_W*")
      npsetstring[i][j++] = new TString("Wbc");
      npsetstring[i][j++] = new TString("Wbl");
      npsetstring[i][j++] = new TString("Whf"); // Run1 only
      npsetstring[i][j++] = new TString("Wcc");
      npsetstring[i][j++] = new TString("WclNorm");
      npsetstring[i][j++] = new TString("Wl");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Wjets, Run1");
      npsetstring[i][j++] = new TString("WJet"); // 7 TeV
      npsetstring[i][j++] = new TString("WDPhi");
      npsetstring[i][j++] = new TString("WMbb");
      npsetstring[i][j++] = new TString("WbbMbb");
      npsetstring[i][j++] = new TString("WPt");
      npsetstring[i][j++] = new TString("sWbb"); // for Wbb systs other than floating normalization, which always look
                                                 // like "*SysWbb*" (as opposed to "*norm_W*")
      npsetstring[i][j++] = new TString("Wbc");
      npsetstring[i][j++] = new TString("Wbl");
      npsetstring[i][j++] = new TString("Whf"); // Run1 only
      npsetstring[i][j++] = new TString("Wcc");
      npsetstring[i][j++] = new TString("WclNorm");
      npsetstring[i][j++] = new TString("Wl");
      npsetands[i]        = new TString("_78TeV"); // Run1

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Wjets, Run2");
      npsetstring[i][j++] = new TString("WDPhi");
      npsetstring[i][j++] = new TString("WMbb");
      npsetstring[i][j++] = new TString("WbbMbb");
      npsetstring[i][j++] = new TString("WPt");
      npsetstring[i][j++] = new TString("sWbb"); // for Wbb systs other than floating normalization, which always look
                                                 // like "*SysWbb*" (as opposed to "*norm_W*")
      npsetstring[i][j++] = new TString("Wbc");
      npsetstring[i][j++] = new TString("Wbl");
      npsetstring[i][j++] = new TString("Wcc");
      npsetstring[i][j++] = new TString("WclNorm");
      npsetstring[i][j++] = new TString("Wl");
      npsetands[i]        = new TString("_13TeV"); // Run2

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Wjets flt. norm., combined");
      npsetstring[i][j++] = new TString("norm_W");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Wjets flt. norm., Run1");
      npsetstring[i][j++] = new TString("norm_W");
      npsetands[i]        = new TString("_78TeV"); // Run1

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Wjets flt. norm., Run2");
      npsetstring[i][j++] = new TString("norm_W");
      npsetands[i]        = new TString("_13TeV"); // Run2

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model ttbar, combined");
      npsetstring[i][j++] = new TString("TtBar");
      npsetstring[i][j++] = new TString("Ttbar");
      npsetstring[i][j++] = new TString("ttBarHigh");
      npsetstring[i][j++] = new TString("TopPt");
      npsetstring[i][j++] = new TString("TTbarPTV");
      npsetstring[i][j++] = new TString("TTbarMBB");
      npsetstring[i][j++] = new TString("TopMBB"); // 7 TeV
      npsetstring[i][j++] = new TString("sttbar");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model ttbar, Run1");
      npsetstring[i][j++] = new TString("TtBar");
      npsetstring[i][j++] = new TString("Ttbar");
      npsetstring[i][j++] = new TString("ttBarHigh");
      npsetstring[i][j++] = new TString("TopPt");
      npsetstring[i][j++] = new TString("TTbarPTV");
      npsetstring[i][j++] = new TString("TTbarMBB");
      npsetstring[i][j++] = new TString("TopMBB"); // 7 TeV
      npsetstring[i][j++] = new TString("sttbar");
      npsetands[i]        = new TString("_78TeV"); // Run1

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model ttbar, Run2");
      npsetstring[i][j++] = new TString("TtBar");
      npsetstring[i][j++] = new TString("Ttbar");
      npsetstring[i][j++] = new TString("ttBarHigh");
      npsetstring[i][j++] = new TString("TopPt");
      npsetstring[i][j++] = new TString("TTbarPTV");
      npsetstring[i][j++] = new TString("TTbarMBB");
      npsetstring[i][j++] = new TString("sttbar");
      npsetands[i]        = new TString("_13TeV"); // Run2

      i++;
      j                   = 0;
      npsetname[i]        = new TString("ttbar flt. norm., combined");
      npsetstring[i][j++] = new TString("norm_ttbar");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("ttbar flt. norm., Run1");
      npsetstring[i][j++] = new TString("norm_ttbar");
      npsetands[i]        = new TString("_78TeV"); // Run1

      i++;
      j                   = 0;
      npsetname[i]        = new TString("ttbar flt. norm., Run2");
      npsetstring[i][j++] = new TString("norm_ttbar");
      npsetands[i]        = new TString("_13TeV"); // Run2

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Single Top, combined");
      npsetstring[i][j++] = new TString("stop");
      npsetstring[i][j++] = new TString("Stop");
      npsetstring[i][j++] = new TString("SysWt"); // 7 TeV

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Single Top, Run1");
      npsetstring[i][j++] = new TString("stop");
      npsetstring[i][j++] = new TString("Stop");
      npsetstring[i][j++] = new TString("SysWt");  // 7 TeV
      npsetands[i]        = new TString("_78TeV"); // Run2

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Single Top, Run2");
      npsetstring[i][j++] = new TString("stop");
      npsetstring[i][j++] = new TString("Stop");
      npsetands[i]        = new TString("_13TeV"); // Run2

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Diboson, combined");
      npsetstring[i][j++] = new TString("SysVV"); // to keep out Run1 "VHVV" systs; which are, incidentally, jets
      npsetstring[i][j++] = new TString("WW");
      npsetstring[i][j++] = new TString("ZZ");
      npsetstring[i][j++] = new TString("WZ");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Diboson, Run1");
      npsetstring[i][j++] = new TString("SysVV"); // to keep out Run1 "VHVV" systs; which are, incidentally, jets
      npsetstring[i][j++] = new TString("WW");
      npsetstring[i][j++] = new TString("ZZ");
      npsetstring[i][j++] = new TString("WZ");
      npsetands[i]        = new TString("_78TeV"); // Run1

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Diboson, Run2");
      npsetstring[i][j++] = new TString("SysVV"); // to keep out Run1 "VHVV" systs; which are, incidentally, jets
      npsetstring[i][j++] = new TString("WW");
      npsetstring[i][j++] = new TString("ZZ");
      npsetstring[i][j++] = new TString("WZ");
      npsetands[i]        = new TString("_13TeV"); // Run2

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Multi Jet, combined");
      npsetstring[i][j++] = new TString("MJ");
      npsetstring[i][j++] = new TString("Multijet");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Multi Jet, Run1");
      npsetstring[i][j++] = new TString("MJ");
      npsetstring[i][j++] = new TString("Multijet");
      npsetands[i]        = new TString("_78TeV"); // Run2

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Model Multi Jet, Run2");
      npsetstring[i][j++] = new TString("MJ");
      npsetstring[i][j++] = new TString("Multijet");
      npsetands[i]        = new TString("_13TeV"); // Run2

      //*********************************************************************************
      //*********************************************************************************
      //              Mode 25---all but signal systematics
      //*********************************************************************************
      //*********************************************************************************
    } else if( mode == 25 ) {
      int i = 2, j = 0;

      i++;
      j                   = 0;
      npsetname[i]        = new TString("Signal Systematics");
      npsetstring[i][j++] = new TString("Theory");
      npsetstring[i][j++] = new TString("SysVH");
      npsetstring[i][j++] = new TString("BR");

      i++;
      j                   = 0;
      npsetname[i]        = new TString("all but signal systematics");
      npsetstring[i][j++] = new TString("Theory");
      npsetstring[i][j++] = new TString("SysVH");
      npsetstring[i][j++] = new TString("BR");
      npsetexclude[i]     = true;
      //*********************************************************************************
      //*********************************************************************************
      //                Mode 26---MonoHbb full run2
      //*********************************************************************************
      //*********************************************************************************
    } else if( mode == 26 ) {

      npsetname[3]      = new TString("Floating normalizations");
      npsetstring[3][0] = new TString("norm");

      npsetname[4]      = new TString("All normalizations");
      npsetstring[4][0] = new TString("norm");
      npsetstring[4][1] = new TString("Norm");

      npsetname[5]      = new TString("All but normalizations");
      npsetstring[5][0] = new TString("norm");
      npsetstring[5][1] = new TString("Norm");
      npsetexclude[5]   = true;

      npsetname[6]       = new TString("JER/JES");
      npsetstring[6][0]  = new TString("SysJET_EffectiveNP");
      npsetstring[6][1]  = new TString("SysJET_JER");
      npsetstring[6][2]  = new TString("SysJET_EtaIntercalibration");
      npsetstring[6][3]  = new TString("SysJET_Flavor");
      npsetstring[6][4]  = new TString("SysJET_CombMass");
      npsetstring[6][5]  = new TString("SysJET_LargeR");
      npsetstring[6][6]  = new TString("SysJET_MassRes");
      npsetstring[6][7]  = new TString("SysJET_Pileup");
      npsetstring[6][8]  = new TString("SysJET_PunchThrough");
      npsetstring[6][9]  = new TString("SysJET_RelativeNonClosure_MC16");
      npsetstring[6][10] = new TString("SysJET_BJES_Response");
      npsetstring[6][11] = new TString("SysJET_SingleParticle_HighPt");

      npsetname[7]      = new TString("BTag");
      npsetstring[7][0] = new TString("SysFT");

      npsetname[8]      = new TString("MET/PRW");
      npsetstring[8][0] = new TString("SysMET_SoftTrk");
      npsetstring[8][1] = new TString("SysPRW");
      npsetstring[8][1] = new TString("JvtEfficiency");

      npsetname[9]      = new TString("Other experimental syst");
      npsetstring[9][0] = new TString("LUMI");
      npsetstring[9][1] = new TString("SysEG");
      npsetstring[9][2] = new TString("SysEL");
      npsetstring[9][3] = new TString("SysMUON");
      npsetstring[9][4] = new TString("SysTAUS");
      npsetstring[9][5] = new TString("SysMETTrig");

      npsetname[10]      = new TString("Z normalization");
      npsetstring[10][0] = new TString("norm_Zhf");

      npsetname[11]      = new TString("W normalization");
      npsetstring[11][0] = new TString("norm_Whf");

      npsetname[12]      = new TString("ttbar normalization");
      npsetstring[12][0] = new TString("norm_ttbar");

      npsetname[13]      = new TString("Z theory syst");
      npsetstring[13][0] = new TString("SysZ_");
      npsetstring[13][1] = new TString("Syslepton_Z");
      npsetstring[13][2] = new TString("Sysbtag_Z");

      npsetname[14]      = new TString("W theory syst");
      npsetstring[14][0] = new TString("SysW_");
      npsetstring[14][1] = new TString("Syslepton_W");
      npsetstring[14][2] = new TString("Sysbtag_W");

      npsetname[15]      = new TString("ttbar theory syst");
      npsetstring[15][0] = new TString("Systtbar_");
      npsetstring[15][1] = new TString("Syslepton_ttbar");
      npsetstring[15][2] = new TString("Sysbtag_ttbar");

      npsetname[16]      = new TString("Other theory syst");
      npsetstring[16][0] = new TString("VHbb");
      npsetstring[16][1] = new TString("VV");
      npsetstring[16][2] = new TString("Diboson");
      npsetstring[16][3] = new TString("stop");
      npsetstring[16][4] = new TString("stop");

      npsetname[17]      = new TString("Signal Systematics");
      npsetstring[17][0] = new TString("Sig");
      npsetstring[17][1] = new TString("zp2hdm");
      npsetstring[17][2] = new TString("2hdma");

      npsetname[18]      = new TString("MC stat");
      npsetstring[18][0] = new TString("gamma");
    }

    //*********************************************************************************
    //*********************************************************************************
    //                           End of mode-specific settings
    //*********************************************************************************
    //*********************************************************************************

    // This must come **after** setting npnstr
    for( int iset = 0; iset < npsets_max; iset++ ) {
      npnstr[iset] = 0;
      for( int istr = 0; istr < nstrmax; istr++ ) {
        if( npsetstring[iset][istr]->CompareTo("xxxxx") )
          npnstr[iset]++;
      }
      if( npsetname[iset]->CompareTo("xxxxx") )
        npsets++;
    }
    if( mode == -1 )
      npsets = 1; // HACK MODE, JUST DO TOTAL, a baseline
  }
};
