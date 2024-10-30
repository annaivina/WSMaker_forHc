#!/usr/bin/env python
""" A small script to check the difference between two sets of histograms

Author: Changqiao LI
Date:   2018-04-13
Email:  changqiao.li@cern.ch

Description:
    Once the new inputs is coming, you can run this script to check the yields difference between new and old.
    And it can also be used to check if the expected updates are in place or not by plotting the shape comparison,
    and this will call CompareShape.py

"""


import argparse
import logging
import time
import ctypes
from ROOT import *
import CompareShape as CS
from fnmatch import fnmatch


# settings
eos_dir = '/eos/atlas/atlascerngroupdisk/phys-higgs/HSG5/Run2/ICHEP2016/'
input_ref  = eos_dir + 'LAL/LimitHistograms.VH.vvbb.13TeV.LAL.v30.root' #0lep
input_test = eos_dir + 'LAL/BUG_LimitHistograms.VH.vvbb.13TeV.LAL.v30.root' #0lep
lep = 'L0'

exp_diff = [
  '*_2tag?jet_150ptv_SR_mva28_SysVVMbbME',
]


# basic structure for inputs
Processes = [
'data',
## W+jets
#'Wbb','Wbc','Wbl','Wcc','Wcl','Wl',
## Z+jets
#'Zbb','Zbc','Zbl','Zcc','Zcl','Zl',
## signal
## 1 lepton
#'qqWlvH125',
##0 lepton:
'qqZvvH125','ggZvvH125',
##2 lepton:
#'qqZllH125','ggZllH125',
## top
#'ttbar','stopWt','stops','stopt',
## diboson
'WW','WZ','ZZ',
]

Vars = {
'L0':['mva28'],
'L1':['mva'],
'L2':['mva'],
#'mva28', # 0 lep
#'mBB',
}

Regions = {
'L0':[
  '2tag2jet_150ptv_SR',
  '2tag3jet_150ptv_SR',
],

'L1':[
  '2tag2jet_150ptv_WhfCR',
  '2tag3jet_150ptv_WhfCR',
  '2tag2jet_150ptv_WhfSR',
  '2tag3jet_150ptv_WhfSR',
],

'L2':[
  '2tag2jet_0_75ptv_SR',
  '2tag2jet_75_150ptv_SR',
  '2tag2jet_150ptv_SR',
  '2tag3jet_0_75ptv_SR',
  '2tag3jet_75_150ptv_SR',
  '2tag3jet_150ptv_SR',
## 2lep CR, please check mBBMVA instead of mva
#'2tag2jet_0_75ptv_topemucr',
#'2tag2jet_75_150ptv_topemucr',
#'2tag2jet_150ptv_topemucr',
#'2tag3jet_0_75ptv_topemucr',
#'2tag3jet_75_150ptv_topemucr',
#'2tag3jet_150ptv_topemucr',
],
}

Systs = [
#{'Name':'blablabla','OneSide':False,'Region':[],'Process':[]},
# two side general sys
{'Name':'SysEG_RESOLUTION_ALL','OneSide':False},
#{'Name':'SysEG_SCALE_ALL','OneSide':False},
#{'Name':'SysEL_EFF_ID_TOTAL_1NPCOR_PLUS_UNCOR','OneSide':False},
#{'Name':'SysEL_EFF_Iso_TOTAL_1NPCOR_PLUS_UNCOR','OneSide':False},
#{'Name':'SysEL_EFF_Reco_TOTAL_1NPCOR_PLUS_UNCOR','OneSide':False},
#{'Name':'SysEL_EFF_Trigger_TOTAL_1NPCOR_PLUS_UNCOR','OneSide':False},
#{'Name':'SysFT_EFF_Eigen_B_0_AntiKt4EMPFlowJets','OneSide':False},
#{'Name':'SysFT_EFF_Eigen_B_1_AntiKt4EMPFlowJets','OneSide':False},
#{'Name':'SysFT_EFF_Eigen_B_2_AntiKt4EMPFlowJets','OneSide':False},
#{'Name':'SysFT_EFF_Eigen_C_0_AntiKt4EMPFlowJets','OneSide':False},
#{'Name':'SysFT_EFF_Eigen_C_1_AntiKt4EMPFlowJets','OneSide':False},
#{'Name':'SysFT_EFF_Eigen_C_2_AntiKt4EMPFlowJets','OneSide':False},
#{'Name':'SysFT_EFF_Eigen_C_3_AntiKt4EMPFlowJets','OneSide':False},
#{'Name':'SysFT_EFF_Eigen_Light_0_AntiKt4EMPFlowJets','OneSide':False},
#{'Name':'SysFT_EFF_Eigen_Light_1_AntiKt4EMPFlowJets','OneSide':False},
#{'Name':'SysFT_EFF_Eigen_Light_2_AntiKt4EMPFlowJets','OneSide':False},
#{'Name':'SysFT_EFF_Eigen_Light_3_AntiKt4EMPFlowJets','OneSide':False},
#{'Name':'SysFT_EFF_Eigen_Light_4_AntiKt4EMPFlowJets','OneSide':False},
#{'Name':'SysFT_EFF_extrapolation_AntiKt4EMPFlowJets','OneSide':False},
#{'Name':'SysFT_EFF_extrapolation_from_charm_AntiKt4EMPFlowJets','OneSide':False},
#{'Name':'SysJET_23NP_JET_BJES_Response','OneSide':False},
#{'Name':'SysJET_23NP_JET_EffectiveNP_1','OneSide':False},
#{'Name':'SysJET_23NP_JET_EffectiveNP_2','OneSide':False},
#{'Name':'SysJET_23NP_JET_EffectiveNP_3','OneSide':False},
#{'Name':'SysJET_23NP_JET_EffectiveNP_4','OneSide':False},
#{'Name':'SysJET_23NP_JET_EffectiveNP_5','OneSide':False},
#{'Name':'SysJET_23NP_JET_EffectiveNP_6','OneSide':False},
#{'Name':'SysJET_23NP_JET_EffectiveNP_7','OneSide':False},
#{'Name':'SysJET_23NP_JET_EffectiveNP_8restTerm','OneSide':False},
#{'Name':'SysJET_23NP_JET_EtaIntercalibration_Modelling','OneSide':False},
#{'Name':'SysJET_23NP_JET_EtaIntercalibration_NonClosure_highE','OneSide':False},
#{'Name':'SysJET_23NP_JET_EtaIntercalibration_NonClosure_negEta','OneSide':False},
#{'Name':'SysJET_23NP_JET_EtaIntercalibration_NonClosure_posEta','OneSide':False},
#{'Name':'SysJET_23NP_JET_EtaIntercalibration_TotalStat','OneSide':False},
#{'Name':'SysJET_23NP_JET_Flavor_Composition','OneSide':False},
#{'Name':'SysJET_23NP_JET_Flavor_Response','OneSide':False},
#{'Name':'SysJET_23NP_JET_Pileup_OffsetMu','OneSide':False},
#{'Name':'SysJET_23NP_JET_Pileup_OffsetNPV','OneSide':False},
#{'Name':'SysJET_23NP_JET_Pileup_PtTerm','OneSide':False},
#{'Name':'SysJET_23NP_JET_Pileup_RhoTopology','OneSide':False},
#{'Name':'SysJET_23NP_JET_PunchThrough_MC16','OneSide':False},
#{'Name':'SysJET_23NP_JET_SingleParticle_HighPt','OneSide':False},
#{'Name':'SysJET_JvtEfficiency','OneSide':False},
##{'Name':'SysJET_SR1_JET_GroupedNP_1','OneSide':False}, # the reduced set of NPs for JES which we don't use
##{'Name':'SysJET_SR1_JET_GroupedNP_2','OneSide':False},
##{'Name':'SysJET_SR1_JET_GroupedNP_3','OneSide':False},
#{'Name':'SysMET_JetTrk_Scale','OneSide':False},
#{'Name':'SysMET_SoftTrk_Scale','OneSide':False},
#{'Name':'SysMETTrigStat','OneSide':False},
#{'Name':'SysMETTrigTop','OneSide':False},
#{'Name':'SysMUON_EFF_STAT','OneSide':False},
#{'Name':'SysMUON_EFF_STAT_LOWPT','OneSide':False},
#{'Name':'SysMUON_EFF_SYS','OneSide':False},
#{'Name':'SysMUON_EFF_SYS_LOWPT','OneSide':False},
#{'Name':'SysMUON_EFF_TrigStatUncertainty','OneSide':False},
#{'Name':'SysMUON_EFF_TrigSystUncertainty','OneSide':False},
#{'Name':'SysMUON_ID','OneSide':False},
#{'Name':'SysMUON_ISO_STAT','OneSide':False},
#{'Name':'SysMUON_ISO_SYS','OneSide':False},
#{'Name':'SysMUON_MS','OneSide':False},
#{'Name':'SysMUON_SAGITTA_RESBIAS','OneSide':False},
#{'Name':'SysMUON_SAGITTA_RHO','OneSide':False},
#{'Name':'SysMUON_SCALE','OneSide':False},
#{'Name':'SysMUON_TTVA_STAT','OneSide':False},
#{'Name':'SysMUON_TTVA_SYS','OneSide':False},
#{'Name':'SysPRW_DATASF','OneSide':False},
#
## one side booked here
#{'Name':'SysJET_JER_SINGLE_NP','OneSide':True},
#{'Name':'SysMET_SoftTrk_ResoPara','OneSide':True},
#{'Name':'SysMET_SoftTrk_ResoPerp','OneSide':True},
#
## some special syst. Only check for the process in 'Process'
#{'Name':'SysTTbarMBB','OneSide':False,'Process':['ttbar']},
#{'Name':'SysTTbarPTV','OneSide':False,'Process':['ttbar']},
#{'Name':'SysTTbarPTVMBB','OneSide':False,'Process':['ttbar']},
#
#{'Name':'SysStopWtMBB','OneSide':False,'Process':['stopWt']},
#{'Name':'SysStopWtPTV','OneSide':False,'Process':['stopWt']},
#
#{'Name':'SysWMbb','OneSide':False,'Process':['Wbb','Wbc','Wbl','Wcc','Wcl']},
#{'Name':'SysWPtV','OneSide':False,'Process':['Wbb','Wbc','Wbl','Wcc','Wcl']},
#{'Name':'SysWPtVMbb','OneSide':False,'Process':['Wbb','Wbc','Wbl','Wcc','Wcl']},
#
#{'Name':'SysZMbb','OneSide':False,'Process':['Zbb','Zbc','Zbl','Zcc','Zcl']},
#{'Name':'SysZPtV','OneSide':False,'Process':['Zbb','Zbc','Zbl','Zcc','Zcl']},
#{'Name':'SysZPtVMbb','OneSide':False,'Process':['Zbb','Zbc','Zbl','Zcc','Zcl']},
#
{'Name':'SysVVMbbME','OneSide':False,'Process':['WZ','ZZ']},
#{'Name':'SysVVMbbPSUE','OneSide':False,'Process':['WZ','ZZ']},
#{'Name':'SysVVPTVME','OneSide':False,'Process':['WZ','ZZ']},
#{'Name':'SysVVPTVPSUE','OneSide':False,'Process':['WZ','ZZ']},

]

# Initialize results collector
Result = {
  'OK':[],
  'SMALL':[],
  'MEDIUM':[],
  'LARGE':[],
  'HUGE':[],
  'MIB':[],
  'MIR':[],
  'MIT':[],
}

def ShowResult(condition,detail=True):
  AllItems = Result[condition]
  num = len(AllItems)
  if   condition == 'OK':     print('For diff < 5%: ',num)
  elif condition == 'SMALL':  print('For 5% < diff < 10%: ',num)
  elif condition == 'MEDIUM': print('For 10% < diff < 50%: ',num)
  elif condition == 'LARGE':  print('For 50% < diff < 100%: ',num)
  elif condition == 'HUGE':   print('For 100% < diff: ',num)
  elif condition == 'MIB':    print('Missing in both reference and test inputs: ',num)
  elif condition == 'MIR':    print('Missing only in reference: ',num)
  elif condition == 'MIT':    print('Missing only in test: ',num)
  if detail:
    for res in AllItems:
      print(res)
  return num

def CompareSysNominal(file, showDetail = False):
  for reg in Regions[lep]:
    for pro in Processes:
      for var in Vars[lep]:
        name = pro+'_'+reg+'_'+var
        for Sys in Systs:
          SysName = Sys['Name']
          # check if the histograms in nominal and sys exist
          nom_exist = file.GetListOfKeys().Contains(name)
          sys_dir = file.GetDirectory('Systematics');
          sys_exist = sys_dir.GetListOfKeys().Contains(name+'_'+SysName+'__1up')
          # in case the sys name contains AntiKt4EMPFlowJets but not the histo (e.g. 2leptons)
          if not nom_exist and not sys_exist and "AntiKt4EMPFlowJets" in SysName:
            SysName = SysName.replace("_AntiKt4EMPFlowJets", "");
            sys_exist = sys_dir.GetListOfKeys().Contains(name+'_'+SysName+'__1up')

          # retrieve the information for nominal and systematic histograms
          nom_entry  = -1.
          sys_entry = -1.
          #pass by reference
          nom_error  = ctypes.c_double(-1.)
          sys_error = ctypes.c_double(-1.)

          if nom_exist:
            nom_hist = file.Get(name)
            nbin = nom_hist.GetNbinsX()
            nom_entry = nom_hist.IntegralAndError(0, nbin, nom_error)

          if sys_exist:
            sys_hist = sys_dir.Get(name+'_'+SysName+'__1up')
            nbin = sys_hist.GetNbinsX()
            sys_entry = sys_hist.IntegralAndError(0, nbin, sys_error)

          # perfrom the comparison between nominal and systematic inputs
          info="Missing"
          if nom_exist and sys_exist:
            dif = 1.0
            if nom_entry > 0. :
              dif = (sys_entry - nom_entry) * 100 / nom_entry
            absdif = abs(dif)
            if (absdif < 5.):
              comment = "OK"
            elif (absdif <= 10.):
              comment = "SMALL"
            elif (absdif <= 50.):
              comment = "MEDIUM"
            elif (absdif <= 100.):
              comment = "LARGE"
            elif (absdif > 100.):
              comment = "HUGE"
            info = f"{dif:+4.1f}%, {comment}"

          else:
            if nom_exist:
              if not sys_exist:
                info += ' in Nominal'
                comment = 'MIT'
            else :
              if sys_exist:
                info += ' in Sys'
                comment = 'MIR'
              else:
                info += ' in both'
                comment = 'MIB'

          result = f"{name:s}  for sys  {SysName:40s}: {nom_entry:9.2f} +- {nom_error:6.2f}, {sys_entry:9.2f} +- {sys_error:6.2f}; ({info})"
          if showDetail:
            result_reg = "{:10s}: {:9.2f} +- {:6.2f}, {:9.2f} +- {:6.2f}; ({})".format(name.split('_')[0], nom_entry, nom_error, sys_entry, sys_error, info)
            print(result_reg)
          Result[comment].append(result)
          logging.info(result)

def Check(name, ref, test, showDetail = False):
  # check if the histogrames in reference and test exist
  ref_exist = ref.GetListOfKeys().Contains(name)
  test_exist = test.GetListOfKeys().Contains(name)
  # special case for 2 lepton channel
  if not ref_exist and not test_exist and "AntiKt4EMPFlowJets" in name:
    name = name.replace("_AntiKt4EMPFlowJets", "");
    ref_exist  = ref.GetListOfKeys().Contains(name)
    test_exist = test.GetListOfKeys().Contains(name)

  # retrieve the information for reference and test histograms
  ref_entry  = -1.
  ref_under  = -1.
  ref_over  = -1.
  test_entry = -1.
  test_under = -1.
  test_over = -1.
  #pass by reference
  ref_error  = ctypes.c_double(-1.)
  test_error = ctypes.c_double(-1.)

  if ref_exist:
    ref_hist = ref.Get(name)
    #ref_entry = ref_hist.Integral()
    nbin = ref_hist.GetNbinsX()
    ref_entry = ref_hist.IntegralAndError(0, nbin, ref_error)
    ref_under = 100.0*ref_hist.GetBinContent(0)/ref_entry
    ref_over = 100.0*ref_hist.GetBinContent(nbin+1)/ref_entry

  if test_exist:
    test_hist = test.Get(name)
    #test_entry = h2.Integral()
    nbin = test_hist.GetNbinsX()
    test_entry = test_hist.IntegralAndError(0, nbin, test_error)
    test_under = 100.0*test_hist.GetBinContent(0)/test_entry
    test_over = 100.0*test_hist.GetBinContent(nbin+1)/test_entry

  unexpUnder = False
  if (test_under > 0 or ref_under > 0 or test_over > 0 or ref_over > 0) and ('mva' in name or 'MVA' in name):
    unexpUnder = True

  # perfrom the comparison between reference and test inputs
  info="Missing"
  if ref_exist and test_exist:
    dif = 1.0
    if ref_entry > 0. :
      dif = (test_entry - ref_entry) * 100 / ref_entry
    absdif = abs(dif)
    if (absdif < 5.):
      comment = "OK"
    elif (absdif <= 10.):
      comment = "SMALL"
    elif (absdif <= 50.):
      comment = "MEDIUM"
    elif (absdif <= 100.):
      comment = "LARGE"
    elif (absdif > 100.):
      comment = "HUGE"
    info = f"{dif:+4.1f}%, {comment}"

  else:
    if ref_exist:
      if not test_exist:
        info += ' in test'
        comment = 'MIT'
    else :
      if test_exist:
        info += ' in reference'
        comment = 'MIR'
      else:
        info += ' in both'
        comment = 'MIB'

  #name.replace("_AntiKt4EMPFlowJets", "")
  result = f"{name:90s}: {ref_entry:9.2f} +- {ref_error.value:6.2f} (u:{ref_under:4.1f}%,o:{ref_over:4.1f}%), {test_entry:9.2f} +- {test_error.value:6.2f} (u:{test_under:4.1f}%,o:{test_over:4.1f}%); ({info})"
  if unexpUnder: result += "   <= \033[1;31m  MVA variable with underflow -- CHECK INPUTS  \033[0m"
  if showDetail:
    result_reg = "{:10s}: {:9.2f} +- {:6.2f} (u:{:4.1f}%,o:{:4.1f}%), {:9.2f} +- {:6.2f} (u:{:4.1f}%,o:{:4.1f}%); ({})".format(name.split('_')[0], ref_entry, ref_error.value, ref_under, ref_over, test_entry, test_error.value, test_under, test_over, info)
    if unexpUnder: result_reg += "   <= \033[1;31m  MVA variable with underflow -- CHECK INPUTS  \033[0m"
    print(result_reg)
  Result[comment].append(result)
  logging.info(result)

  if ref_exist and test_exist: return [ref_hist.Clone(),test_hist.Clone()]
  else: return None

def CheckBinning(test):
  pass

def NBinsForVar(var):
  if var == 'mva28': return 100
  elif var == 'mva': return 100

def PlotShapeDiff(name, var, histNos, histUPs, histDOs=None):
  #print histUPs
  #print 'ShapeDiff in reference Name: %s, Entries: %d'%(name, histUPs[0].GetEntries())
  #print 'ShapeDiff in test Name: %s, Entries: %d'%(name, histUPs[1].GetEntries())
  NMerge = NBinsForVar(var)
  histNos[0].Rebin(NMerge)
  histNos[1].Rebin(NMerge)
  histUPs[0].Rebin(NMerge)
  histUPs[1].Rebin(NMerge)
  CL = [
    {'name':'ref-Nom',  'color':kBlack,'remark':'Nominal from ref',  'hist':histNos[0], 'LineStyle':1},
    {'name':'test-Nom', 'color':kBlack,'remark':'Nominal from test', 'hist':histNos[1], 'LineStyle':2},
    {'name':'ref-UP',   'color':kBlue, 'remark':'UP from ref',       'hist':histUPs[0], 'LineStyle':1},
    {'name':'test-UP',  'color':kBlue, 'remark':'UP from test',      'hist':histUPs[1], 'LineStyle':2},
  ]
  if histDOs is not None:
    histDOs[0].Rebin(NMerge)
    histDOs[1].Rebin(NMerge)
    #print 'ShapeDiff in reference Name: %s, Entries: %d'%(name, histDOs[0].GetEntries())
    #print 'ShapeDiff in test Name: %s, Entries: %d'%(name, histDOs[1].GetEntries())
    CL.append( {'name':'ref-DO',  'color':kRed, 'remark':'DOWN from ref',  'hist':histDOs[0], 'LineStyle':1 } )
    CL.append( {'name':'test-DO', 'color':kRed, 'remark':'DOWN from test', 'hist':histDOs[1], 'LineStyle':2 } )
    CS.DrawCompWithHist(CL, False, name, var, 'Events', './Shape/')

def CheckNominal(ref, test):
  for reg in Regions[lep]:
    print('nominal (underflow:, overflow:) for region:' + reg)
    for pro in Processes:
      for var in Vars[lep]:
        histoname = pro+'_'+reg+'_'+var
        Check(histoname, ref, test, True)

def CheckSyst(ref, test):
  subdir_ref  = ref.GetDirectory('Systematics');
  subdir_test = test.GetDirectory('Systematics');
  for sys in Systs:
    SysName = sys['Name']
    OneSide = sys['OneSide']
    #print
    for reg in Regions[lep]:
      if 'Region' in sys and reg not in sys['Region']:
        continue
      for pro in Processes:
        if 'Process' in sys and pro not in sys['Process']:
          continue
        if pro == 'data':
          continue
        for var in Vars[lep]:
          histoname = pro+'_'+reg+'_'+var+'_'+SysName
          histUPs = Check(histoname+'__1up', subdir_ref, subdir_test)
          if not OneSide:
            histDOs = Check(histoname+'__1down', subdir_ref, subdir_test)

          # we are doing the shape comparison
          # check if this is what we want to perform the shape comparison
          DoShapeDiff = False
          for regex in exp_diff:
            DoShapeDiff |= fnmatch(histoname, regex)
          if DoShapeDiff:
            # get the nominal histos
            nominal = pro+'_'+reg+'_'+var
            ref_exist = ref.GetListOfKeys().Contains(nominal)
            test_exist = test.GetListOfKeys().Contains(nominal)

            if ref_exist:
              ref_hist = ref.Get(nominal)
            else:
              logging.critical('The nominal %s doesn\' t exist in reference'%nominal)

            if test_exist:
              test_hist = test.Get(nominal)
            else:
              logging.critical('The nominal %s doesn\' t exist in test'%nominal)

            histNos = [ ref_hist.Clone(), test_hist.Clone() ]
            if OneSide: PlotShapeDiff(histoname, var, histNos, histUPs)
            else: PlotShapeDiff(histoname, var, histNos, histUPs, histDOs)

def main():
  usage = "Usage: %prog [options]"
  parser = argparse.ArgumentParser(
    description='A script to compare VHbb inputs'
    )
  parser.add_argument( "-d", "--debug",   help="Print lots of debugging statements", action="store_true")
  parser.add_argument( "-v", "--verbose", help="increase output verbosity",          action="store_true")

  args = parser.parse_args()
  if args.verbose:
    logging.basicConfig( level=logging.INFO,  format='INFO:%(message)s' )

  if args.debug:
    logging.basicConfig( level=logging.DEBUG, format='DEBUG:%(message)s' )

  logging.debug('Only shown in debug mode')
  logging.info('Only shown in verbose mode')

  if input_test != '' and input_ref != '':
      print(f'reference input: {input_ref}')
      print(f'test      input: {input_test}')

      # start check the nominal
      start_time = time.time()
      tfile_ref = TFile(input_ref,  'READ');
      tfile_test = TFile(input_test, 'READ');
      CheckNominal(tfile_ref, tfile_test)
      print("--- %s seconds for nominal check---" % round(time.time() - start_time, 2))

      # start check the systematics, first we enter the subdir for systematics
      start_time = time.time()
      CheckSyst(tfile_ref, tfile_test)
      print("--- %s seconds for systematic check---" % round(time.time() - start_time, 2))
  elif input_test != '' and input_ref == '':
     print(f'Comparing nominal and syst for: {input_test}')
     start_time = time.time()
     tfile_test = TFile(input_test, 'READ');
     CompareSysNominal(tfile_test);
     print("--- %s seconds for nominal vs systematic check---" % round(time.time() - start_time, 2))
  elif input_test == '' and input_ref != '':
    print(f'Comparing nominal and syst for: {input_ref}')
    start_time = time.time()
    tfile_ref = TFile(input_ref, 'READ');
    CompareSysNominal(tfile_ref);
    print("--- %s seconds for nominal vs systematic check---" % round(time.time() - start_time, 2))

  total = 0
  #for condition in [ 'OK', 'SMALL', 'MEDIUM', 'LARGE', 'HUGE', 'MIB', 'MIR', 'MIT' ]
  total +=  ShowResult('OK')
  total +=  ShowResult('MIB')
  total +=  ShowResult('MIR')
  total +=  ShowResult('MIT')
  total +=  ShowResult('SMALL')
  total +=  ShowResult('MEDIUM')
  total +=  ShowResult('LARGE')
  total +=  ShowResult('HUGE')
  print('For all above, in total: ',total)

if __name__ == "__main__":
  start_time = time.time()
  main()
  print("--- %s seconds for this job---" % round(time.time() - start_time, 2))
