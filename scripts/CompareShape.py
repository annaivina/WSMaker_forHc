#!/usr/bin/env python
""" A small script to plot the comparison of a set of histograms

Author: Changqiao LI
Date:   2018-04-13
Email:  changqiao.li@cern.ch

Description:
    This script is a toolkit can be used to draw the comparison plot
    a set of histograms, for instance, like wew shape vs old shape. And it provides
    basic feature: legend of two histograms and the ratio of two.

"""

import operator
import array
import os
import ROOT

ROOT.gROOT.SetBatch(1)
save_dir = './plots'
runtag = ''
sf = 1.
status='Internal'

formats = [ 'png', 'pdf', 'eps']

#ROOT.gROOT.LoadMacro("macros/AtlasStyle.C")
#ROOT.gROOT.LoadMacro("macros/AtlasUtils.C")
ROOT.gROOT.LoadMacro("$WORKDIR/macros/AtlasStyle.C")
ROOT.gROOT.LoadMacro("$WORKDIR/macros/AtlasUtils.C")
ROOT.SetAtlasStyle()

def clone(hist):
  """ Create real clones that won't go away easily """
  #print type(hist)
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

def Out(hist, name):
  n = hist.GetNbinsX()
  print(f'{name:<16}', end=' ')
  for i in range(1,n+1):
    print('{:<5}'.format(f'{hist.GetBinContent(i):.1f}'), end=' ')
  print() 

def GetHists(sam,fmt,xbins,rootfile):
  print('to open: ',rootfile)
  f = ROOT.TFile(rootfile,'r')
  h = None
  temp = f.Get(fmt.format(sam))
  if temp == None: 
    print(f'not get {fmt.format(sam)}')
    exit(0)
  print(f'get {fmt.format(sam)}')
  if  sam.find('data')==-1:
    print('scale!')
    temp.Scale(sf)
  if h is None: 
    h = clone(temp)
  else: 
    h.Add(temp)
  if h == None:
    print('Nothing !!!!! \n',sams)
    exit(0)
  if len(xbins) > 0:
    h = h.Rebin(len(xbins)-1,'',array.array('d',xbins))
  h.SetMarkerSize(0)
  print('Integral: ',h.Integral())
  hist = clone(h)
  return hist

def ATLAS_LABEL(x, y, color, TEXT='', delx = 0.164):
   l = ROOT.TLatex()
   l.SetNDC()
   l.SetTextFont(72)
   l.SetTextColor(color)
   l.DrawLatex(x,y,"ATLAS")
   #l.DrawLatex(x,y,"ATLAS"+' '+TEXT)
   #delx = 0.164
   l.DrawLatex(x+delx,y,TEXT)
   #double delx = 0.115*696*gPad->GetWh()/(472*gPad->GetWw());
   #delx = 0.164

def myText(x, y, color, text,size = None):
   l = ROOT.TLatex() #l.SetTextAlign(12); l.SetTextSize(tsize); 
   if size != None: 
     l.SetTextSize(size)
   l.SetNDC()
   l.SetTextColor(color)
   l.DrawLatex(x,y,text)

def SetupPad(TopPad,BotPad):
  TopPad.SetBottomMargin(0.02)
  TopPad.SetTopMargin(0.05)
  TopPad.SetRightMargin(0.08)

  BotPad.SetTopMargin(0.03)
  BotPad.SetBottomMargin(0.3)
  BotPad.SetRightMargin(0.08)

def SetupTopFrame(hist):
  hist.GetYaxis().SetTitleOffset(1.6)
  hist.SetLabelOffset(0.05)

  hist.GetYaxis().SetTitleSize(0.04)
  hist.GetXaxis().SetTitleSize(0.04)

  hist.GetXaxis().SetLabelSize(0.03)
  hist.GetYaxis().SetLabelSize(0.03)

def SetupTopFrameAdv(hist,xtitle,ytitle,maximum):
  hist_frame = clone(hist)
  SetupTopFrame(hist_frame)
  hist_frame.GetXaxis().SetTitle(xtitle)
  hist_frame.GetYaxis().SetTitle(ytitle)
  hist_frame.SetMaximum(maximum*1.5)
  return hist_frame

def SetupBotFrame(hist,y_max=1.3,y_min=0.9,ls_x=0.06,ls_y=0.06):

  hist.SetMarkerSize(0)
  hist.GetYaxis().SetTitle("ratio")
  hist.GetYaxis().SetTitleOffset(0.6)
  hist.GetYaxis().SetTitleSize(0.1)

  hist.GetXaxis().SetTitleSize(0.08)
  hist.GetXaxis().SetLabelOffset(0.01)

  hist.GetXaxis().SetLabelSize(ls_x)
  hist.GetYaxis().SetLabelSize(ls_y)

  hist.SetMaximum(y_max)
  hist.SetMinimum(y_min)

def LineOne(ratio):
  xmin = ratio.GetXaxis().GetXmin()
  xmax = ratio.GetXaxis().GetXmax()
  print(f'The line starts from {xmin} to {xmax}', end=' ')
  L_One = TLine(xmin,1,xmax,1);
  L_One.SetLineStyle(2);
  L_One.SetLineColor(1);
  L_One.SetLineWidth(2);
  return L_One

#def DrawCutComp(alter,ratios,fmt,xbins,isLog,title,reg,xtitle,ytitle='Events'):
def DrawCutComp(alter,ratios,fmt,title,xtitle,ytitle='Events'):

  canvas = ROOT.TCanvas(title,title,800,800)
  p_u = ROOT.TPad("pu","pu",0,0.3,1,1)
  p_d = ROOT.TPad("pd","pd",0,0,1,0.3)
  SetupPad(p_u,p_d)
  p_u.Draw()
  p_d.Draw()
  p_d.SetBottomMargin(0.42)

  #leg = ROOT.TLegend( 0.2, 0.7, 0.6, 0.9 )
  leg = ROOT.TLegend( 0.6, 0.72, 0.9, 0.92 )
  leg.SetFillStyle(0)
  leg.SetBorderSize(0)

  AllHists = []
  maximum  = -999
  for sample in alter:
    hist = GetHists(sample['name'],fmt,[],sample['file'])
    hist.SetLineColor(sample['color'])
    leg.AddEntry(hist, sample['name']+'_'+sample['remark'], 'l')
    if 'sf' in list(sample.keys()):
      hist.Scale(sample['sf'])
    if maximum < hist.GetMaximum() : maximum = hist.GetMaximum()
    AllHists.append(hist)

  HistFrame=SetupTopFrameAdv(AllHists[0],'',ytitle,maximum)

  p_u.cd()
  HistFrame.Draw()
  for h in AllHists:
    h.Draw('same')
  leg.Draw()
  ATLAS_LABEL(0.20, 0.85, 1, '#font[42]{%s}'%status, 0.12)

  """ 
  add the ratio 
  
  """
  FirstRatio = True
  for item,r in enumerate(ratios):
    p_d.cd()
    hist_up = AllHists[r['up']]
    hist_do = AllHists[r['down']]
    ratio   = clone(HistFrame)
    ratio.Divide(hist_up,hist_do)
    ratio.SetLineColor(r['color'])
    if FirstRatio:
      SetupBotFrame( ratio, 1.5, 0.5, 0.08, 0.06)
      ratio.GetXaxis().SetLabelOffset(0.01)
      ratio.GetXaxis().LabelsOption("v")
      ratio.Draw();
      line_one = LineOne(ratio)
      line_one.Draw()
      FirstRatio=False
    else:
      ratio.Draw('same')
    p_u.cd()
    l=ROOT.TLatex()
    l.SetNDC()
    #l.SetTextFont(72)
    x_pos = 0.61
    y_pos = 0.65
    l.SetTextColor(r['color'])
    l.DrawLatex(x_pos,      y_pos-0.05*item, "Ratio=")
    l.SetTextColor(alter[r['up']]['color'])
    l.DrawLatex(x_pos+0.1,  y_pos-0.05*item, "Line /")
    l.SetTextColor(alter[r['down']]['color'])
    l.DrawLatex(x_pos+0.18, y_pos-0.05*item, " Line")

  #canvas.Print('{0:}/AlterAdv_{1:}.png'.format(save_dir,title))
  if not os.path.exists(save_dir):
        os.makedirs(save_dir)
  for f in formats:
    canvas.Print(f'{save_dir}/CutFlow_{title}.{f}')

def GetYTitle(var):
  return 'Events'

def GetXTitle(var):
  if   var == 'mBB': return 'm(BB) [GeV]'
  elif var == 'MET': return 'MET [GeV]'
  elif var == 'Njets': return '# of jets'
  else : return var

def GetXBins(var):
  if   var == 'mBB':   xbins = [x*20 for x in range(0,26)]
  elif var == 'MET':   xbins = [x*10 for x in range(0,51)]
  elif var == 'Njets': xbins = [x for x in range(1, 10)]
  elif var == 'Mll':   xbins = [x*10 for x in range(1, 16)]
  else : xbins = []
  return xbins

def DrawCompAPI(alter, sample, var, isLog, Prefix, reg):
  Ratios  = [ {'up':1, 'down':0, 'color':ROOT.kBlack}, ]
  fmt = ('{{0:}}_{0:}_'+var).format(reg)
  xbins  = GetXBins(var)
  xtitle = GetXTitle(var)
  ytitle = GetYTitle(var)
  title  = Prefix+'_{0:}_'+var
  save_dir_local = save_dir+Prefix+'/'
  DrawComp(alter, Ratios, fmt, xbins, isLog, title, reg, xtitle, ytitle, save_dir_local)

def DrawCompWithHist(alter,isLog,title,xtitle,ytitle='Events',SaveDir=save_dir):
  canvas = ROOT.TCanvas(title,title,800,800)

  # setup the legend
  leg = ROOT.TLegend( 0.5, 0.74, 0.9, 0.90 )
  leg.SetNColumns(2)
  leg.SetFillStyle(0)
  leg.SetBorderSize(0)

  AllHists = []
  maximum  = -999
  for sample in alter:
    hist = sample['hist']
    hist.SetLineColor(sample['color'])
    hist.SetMarkerColor(sample['color'])
    if 'LineStyle' in list(sample.keys()):
      style = sample['LineStyle']
      hist.SetLineStyle(style)
    leg.AddEntry(hist, sample['remark'], 'l')
    if 'sf' in list(sample.keys()):
      hist.Scale(sample['sf'])
    if maximum < hist.GetMaximum() : maximum = hist.GetMaximum()
    AllHists.append(hist)

  HistFrame=SetupTopFrameAdv(AllHists[0],xtitle,ytitle,maximum)
  HistFrame.SetLabelOffset(0.02)

  HistFrame.Draw()
  for h in AllHists:
    h.Draw('same')
  leg.Draw()
  ATLAS_LABEL(0.20, 0.85, 1, '#font[42]{%s}'%status, 0.16)
  l=ROOT.TLatex()
  l.SetNDC()
  l.SetTextFont(72)
  l.SetTextSize(0.03)
  l.DrawLatex(0.20,0.71,title)

  if 'data' not in sample['name']:
    l.DrawLatex(0.20,0.78,"#font[42]{#sqrt{s} = 13 TeV, %s fb^{-1}}"%'36.1')
    
  #canvas.Print('{0:}/AlterAdv_{1:}.png'.format(save_dir,title))
  if not os.path.exists(SaveDir):
        os.makedirs(SaveDir)
  for f in formats:
    canvas.Print(f'{SaveDir}/Shape_{title}.{f}')

def DrawComp(alter,ratios,fmt,xbins,isLog,title,reg,xtitle,ytitle='Events',SaveDir=save_dir):
  title = title.format(reg)
  canvas = ROOT.TCanvas(title,title,800,800)
  p_u = ROOT.TPad("pu","pu",0,0.3,1,1)
  p_d = ROOT.TPad("pd","pd",0,0,1,0.3)
  SetupPad(p_u,p_d)
  p_u.Draw()
  p_d.Draw()

  #leg = ROOT.TLegend( 0.2, 0.7, 0.6, 0.9 )
  #leg = ROOT.TLegend( 0.6, 0.80, 0.9, 0.92 )
  leg = ROOT.TLegend( 0.6, 0.78, 0.9, 0.90 )
  leg.SetFillStyle(0)
  leg.SetBorderSize(0)

  AllHists = []
  maximum  = -999
  for sample in alter:
    hist = GetHists(sample['name'],fmt,xbins,sample['file'])
    hist.SetLineColor(sample['color'])
    #leg.AddEntry(hist, sample['name']+'_'+sample['remark'], 'l')
    leg.AddEntry(hist, sample['remark'], 'l')
    if 'sf' in list(sample.keys()):
      hist.Scale(sample['sf'])
    if maximum < hist.GetMaximum() : maximum = hist.GetMaximum()
    AllHists.append(hist)

  HistFrame=SetupTopFrameAdv(AllHists[0],xtitle,ytitle,maximum)

  p_u.cd()
  HistFrame.Draw()
  for h in AllHists:
    h.Draw('same')
  leg.Draw()
  ATLAS_LABEL(0.20, 0.85, 1, '#font[42]{%s}'%status, 0.12)
  l=ROOT.TLatex()
  l.SetNDC()
  l.SetTextFont(72)
  l.SetTextSize(0.04)
  l.DrawLatex(0.20,0.71,reg.replace("_", " "))

  if 'data' not in sample['name']:
    l.DrawLatex(0.20,0.78,"#font[42]{#sqrt{s} = 13 TeV, %s fb^{-1}}"%'36.1')
    
  """ 
  add the ratio 
  
  """
  FirstRatio = True
  for item,r in enumerate(ratios):
    p_d.cd()
    hist_up = AllHists[r['up']]
    hist_do = AllHists[r['down']]
    ratio   = clone(HistFrame)
    ratio.Divide(hist_up,hist_do)
    ratio.SetLineColor(r['color'])
    if FirstRatio:
      SetupBotFrame( ratio, 2.0, 0.0)
      ratio.Draw();
      line_one = LineOne(ratio)
      line_one.Draw()
      FirstRatio=False
    else:
      ratio.Draw('same')
    p_u.cd()
    l=ROOT.TLatex()
    l.SetNDC()
    #l.SetTextFont(72)
    x_pos = 0.61
    y_pos = 0.72
    l.SetTextColor(r['color'])
    l.DrawLatex(x_pos,      y_pos-0.05*item, "Ratio=")
    l.SetTextColor(alter[r['up']]['color'])
    l.DrawLatex(x_pos+0.1,  y_pos-0.05*item, "Line /")
    l.SetTextColor(alter[r['down']]['color'])
    l.DrawLatex(x_pos+0.18, y_pos-0.05*item, " Line")

  #canvas.Print('{0:}/AlterAdv_{1:}.png'.format(save_dir,title))
  if not os.path.exists(SaveDir):
        os.makedirs(SaveDir)
  for f in formats:
    canvas.Print(f'{SaveDir}/AlterAdv_{title}.{f}')

def main():

  CL_data15 = [
    #{'name':'qqZvvH125',         'color':kBlue,    'remark':'CxAOD28', 'file':'input_CxAOD28.root'},
    #{'name':'qqZvvH125',         'color':kRed,     'remark':'CxAOD29', 'file':'input_CxAOD29.root'},
    {'name':'data',         'color':kBlue,    'remark':'CxAOD28-data15', 'file':'Lepton0/CxAOD28/hist-data15.root '},
    {'name':'data',         'color':kRed,     'remark':'CxAOD29-data15', 'file':'Lepton0/CxAOD29/hist-data15.root '},
  ]

  CL_data16 = [
    #{'name':'qqZvvH125',         'color':kBlue,    'remark':'CxAOD28', 'file':'input_CxAOD28.root'},
    #{'name':'qqZvvH125',         'color':kRed,     'remark':'CxAOD29', 'file':'input_CxAOD29.root'},
    {'name':'data',         'color':kBlue,    'remark':'CxAOD28-data16', 'file':'Lepton0/CxAOD28/hist-data16.root '},
    {'name':'data',         'color':kRed,     'remark':'CxAOD29-data16', 'file':'Lepton0/CxAOD29/hist-data16.root '},
  ]

  Ratios  = [
    {'up':1, 'down':0, 'color':kBlack},
  ]

  #for reg in ['0ptag0pjet_150ptv_SR']:

  #  fmt = '{{0:}}_{0:}_njets'.format(reg)
  #  xbins = [x for x in range(0,8)]
  #  DrawComp(CL_data15,  Ratios,  fmt,xbins,False,'data15_{0:}_njets', reg,  'number of jets','Events')
  #  DrawComp(CL_data16,  Ratios,  fmt,xbins,False,'data16_{0:}_njets', reg,  'number of jets','Events')
      
  for reg in ['0ptag2jet_150ptv_SR', '0ptag3jet_150ptv_SR', '0ptag4jet_150ptv_SR', '2tag2jet_150ptv_SR', '2tag3jet_150ptv_SR']:

    fmt = f'{{0:}}_{reg}_mBB'
    xbins = [x*20 for x in range(0,25)]
    DrawComp(CL_data15,  Ratios,  fmt,xbins,False,'data15_{0:}_mBB', reg,  'm(BB) GeV','Events')
    DrawComp(CL_data16,  Ratios,  fmt,xbins,False,'data16_{0:}_mBB', reg,  'm(BB) GeV','Events')

    fmt = f'{{0:}}_{reg}_MET'
    xbins = [x*20 for x in range(0,25)]
    DrawComp(CL_data15,  Ratios,  fmt,xbins,False,'data15_{0:}_MET', reg,  'MET GeV','Events')
    DrawComp(CL_data16,  Ratios,  fmt,xbins,False,'data16_{0:}_MET', reg,  'MET GeV','Events')

  fmt = 'CutFlow/Nominal/CutsSM'
  DrawCutComp(CL_data15, Ratios, fmt, 'CutFlow', 'Cut Order','Events')


if __name__ == '__main__':
  main()
