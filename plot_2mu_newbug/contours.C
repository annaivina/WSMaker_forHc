#ifdef __CLING__
#pragma cling optimize(0)
#endif
void contours()
{
//=========Macro generated from canvas: canv/canv
//=========  (Sun Sep 29 14:43:13 2024) by ROOT version 6.32.02
   TCanvas *canv = new TCanvas("canv", "canv",0,0,800,600);
   gStyle->SetOptStat(0);
   gStyle->SetOptTitle(0);
   canv->SetHighLightColor(2);
   canv->Range(-2.628174,-0.3027521,7.86255,1.589449);
   canv->SetFillColor(0);
   canv->SetBorderMode(0);
   canv->SetBorderSize(2);
   canv->SetTickx(1);
   canv->SetTicky(1);
   canv->SetLeftMargin(0.16);
   canv->SetRightMargin(0.05);
   canv->SetTopMargin(0.05);
   canv->SetBottomMargin(0.16);
   canv->SetFrameBorderMode(0);
   canv->SetFrameBorderMode(0);
   
   TMultiGraph *multigraph = new TMultiGraph();
   multigraph->SetName("");
   multigraph->SetTitle("");
   
   Double_t Graph_fx1[51] = { 1.753619, 1.56208, 1.445273, 1.249657, 0.937233, 0.9141114, 0.8804449, 0.937233, 0.9612767, 1.128212, 1.249657, 1.356749, 1.56208, 1.639186, 1.874504, 1.98864, 2.186928,
   2.421528, 2.499352, 2.811775, 2.97805, 3.124199, 3.436623, 3.749046, 3.819276, 4.06147, 4.373894, 4.686317, 4.946418, 4.998741, 5.228189, 5.224725, 5.099883,
   4.998741, 4.892432, 4.686317, 4.620974, 4.373894, 4.288101, 4.06147, 3.889118, 3.749046, 3.436623, 3.423118, 3.124199, 2.832759, 2.811775, 2.499352, 2.186928,
   1.874504, 1.753619 };
   Double_t Graph_fy1[51] = { 1.062477, 1.065178, 1.062477, 1.054905, 1.00745, 0.9999924, 0.9375076, 0.8932717, 0.8750229, 0.8125381, 0.7791503, 0.7500534, 0.7044248, 0.6875687, 0.6450881, 0.6250839, 0.5964353,
   0.5625992, 0.5528811, 0.5176638, 0.5001144, 0.4869865, 0.4627112, 0.440913, 0.4376297, 0.4283482, 0.422224, 0.4246789, 0.4376297, 0.4436117, 0.5001144, 0.5625992, 0.6250839,
   0.6554467, 0.6875687, 0.7350332, 0.7500534, 0.796581, 0.8125381, 0.8483695, 0.8750229, 0.8946211, 0.93587, 0.9375076, 0.9700044, 0.9999924, 1.001984, 1.026181, 1.046308,
   1.060588, 1.062477 };
   TGraph *graph = new TGraph(51,Graph_fx1,Graph_fy1);
   graph->SetName("Graph");
   graph->SetTitle("Graph");

   Int_t ci;      // for color index setting
   TColor *color; // for color definition with alpha
   ci = TColor::GetColor("#80ea7c");
   graph->SetFillColor(ci);
   graph->SetFillStyle(1000);

   ci = TColor::GetColor("#0000ff");
   graph->SetLineColor(ci);
   graph->SetLineStyle(7);
   graph->SetLineWidth(2);
   graph->SetMarkerStyle(20);
   graph->SetMarkerSize(1.2);
   
   TH1F *Graph_Graph1 = new TH1F("Graph_Graph1","Graph",100,0.4456705,5.662963);
   Graph_Graph1->SetMinimum(0.3579285);
   Graph_Graph1->SetMaximum(1.129474);
   Graph_Graph1->SetDirectory(nullptr);
   Graph_Graph1->SetStats(0);
   Graph_Graph1->SetLineWidth(2);
   Graph_Graph1->SetMarkerStyle(20);
   Graph_Graph1->SetMarkerSize(1.2);
   Graph_Graph1->GetXaxis()->SetLabelFont(42);
   Graph_Graph1->GetXaxis()->SetLabelSize(0.05);
   Graph_Graph1->GetXaxis()->SetTitleSize(0.05);
   Graph_Graph1->GetXaxis()->SetTitleOffset(1.4);
   Graph_Graph1->GetXaxis()->SetTitleFont(42);
   Graph_Graph1->GetYaxis()->SetLabelFont(42);
   Graph_Graph1->GetYaxis()->SetLabelSize(0.05);
   Graph_Graph1->GetYaxis()->SetTitleSize(0.05);
   Graph_Graph1->GetYaxis()->SetTitleOffset(1.4);
   Graph_Graph1->GetYaxis()->SetTitleFont(42);
   Graph_Graph1->GetZaxis()->SetLabelFont(42);
   Graph_Graph1->GetZaxis()->SetLabelSize(0.05);
   Graph_Graph1->GetZaxis()->SetTitleSize(0.05);
   Graph_Graph1->GetZaxis()->SetTitleOffset(1);
   Graph_Graph1->GetZaxis()->SetTitleFont(42);
   graph->SetHistogram(Graph_Graph1);
   
   multigraph->Add(graph,"");
   
   Double_t Graph_fx2[83] = { 1.874504, 1.56208, 1.249657, 0.937233, 0.6248093, 0.3123856, -3.814697e-05, -0.3124619, -0.3565163, -0.548249, -0.5729456, -0.5058523, -0.3834885, -0.3124619, -0.2119708, -0.01002805, -3.814697e-05,
   0.228459, 0.3123856, 0.4962246, 0.6248093, 0.7921897, 0.937233, 1.123059, 1.249657, 1.494607, 1.56208, 1.874504, 1.90989, 2.186928, 2.394866, 2.499352, 2.811775,
   2.960099, 3.124199, 3.436623, 3.656275, 3.749046, 4.06147, 4.373894, 4.641227, 4.686317, 4.998741, 5.311165, 5.623589, 5.936012, 6.248436, 6.454968, 6.56086,
   6.856086, 6.873283, 6.961301, 6.945498, 6.873283, 6.851546, 6.689842, 6.56086, 6.490027, 6.248436, 6.242293, 5.954969, 5.936012, 5.633221, 5.623589, 5.311165,
   5.275052, 4.998741, 4.880851, 4.686317, 4.451864, 4.373894, 4.06147, 3.976303, 3.749046, 3.447641, 3.436623, 3.124199, 2.833531, 2.811775, 2.499352, 2.186928,
   2.052454, 1.874504 };
   Double_t Graph_fy2[83] = { 1.261743, 1.278686, 1.292178, 1.301314, 1.304957, 1.301337, 1.287664, 1.256985, 1.249931, 1.187447, 1.124962, 1.062477, 0.9999924, 0.9749441, 0.9375076, 0.8750229, 0.8725162,
   0.8125381, 0.793434, 0.7500534, 0.723012, 0.6875687, 0.6603303, 0.6250839, 0.6037378, 0.5625992, 0.5524157, 0.5052322, 0.5001144, 0.4643951, 0.4376297, 0.4254764, 0.3908792,
   0.375145, 0.3594703, 0.3315079, 0.3126602, 0.3054496, 0.2844422, 0.2648426, 0.2501755, 0.2479409, 0.2366438, 0.2287967, 0.2252086, 0.2276523, 0.2374526, 0.2501755, 0.2613293,
   0.3126602, 0.3207787, 0.375145, 0.4376297, 0.4853252, 0.5001144, 0.5625992, 0.6022298, 0.6250839, 0.6859977, 0.6875687, 0.7500534, 0.7537212, 0.8125381, 0.8142286, 0.8687482,
   0.8750229, 0.9188894, 0.9375076, 0.9660888, 0.9999924, 1.010538, 1.051648, 1.062477, 1.089785, 1.124962, 1.126189, 1.158615, 1.187447, 1.189513, 1.216223, 1.240703,
   1.249931, 1.261743 };
   graph = new TGraph(83,Graph_fx2,Graph_fy2);
   graph->SetName("Graph");
   graph->SetTitle("Graph");

   ci = TColor::GetColor("#880200");
   graph->SetFillColor(ci);
   graph->SetFillStyle(1000);

   ci = TColor::GetColor("#0000ff");
   graph->SetLineColor(ci);
   graph->SetLineWidth(2);
   graph->SetMarkerStyle(20);
   graph->SetMarkerSize(1.2);
   
   TH1F *Graph_Graph2 = new TH1F("Graph_Graph2","Graph",100,-1.32637,7.714726);
   Graph_Graph2->SetMinimum(0.1172338);
   Graph_Graph2->SetMaximum(1.412932);
   Graph_Graph2->SetDirectory(nullptr);
   Graph_Graph2->SetStats(0);
   Graph_Graph2->SetLineWidth(2);
   Graph_Graph2->SetMarkerStyle(20);
   Graph_Graph2->SetMarkerSize(1.2);
   Graph_Graph2->GetXaxis()->SetLabelFont(42);
   Graph_Graph2->GetXaxis()->SetLabelSize(0.05);
   Graph_Graph2->GetXaxis()->SetTitleSize(0.05);
   Graph_Graph2->GetXaxis()->SetTitleOffset(1.4);
   Graph_Graph2->GetXaxis()->SetTitleFont(42);
   Graph_Graph2->GetYaxis()->SetLabelFont(42);
   Graph_Graph2->GetYaxis()->SetLabelSize(0.05);
   Graph_Graph2->GetYaxis()->SetTitleSize(0.05);
   Graph_Graph2->GetYaxis()->SetTitleOffset(1.4);
   Graph_Graph2->GetYaxis()->SetTitleFont(42);
   Graph_Graph2->GetZaxis()->SetLabelFont(42);
   Graph_Graph2->GetZaxis()->SetLabelSize(0.05);
   Graph_Graph2->GetZaxis()->SetTitleSize(0.05);
   Graph_Graph2->GetZaxis()->SetTitleOffset(1);
   Graph_Graph2->GetZaxis()->SetTitleFont(42);
   graph->SetHistogram(Graph_Graph2);
   
   multigraph->Add(graph,"");
   multigraph->Draw("al");
   multigraph->GetXaxis()->SetLimits(-0.949658, 7.338013);
   multigraph->GetXaxis()->SetTitle("#mu");
   multigraph->GetXaxis()->SetLabelFont(42);
   multigraph->GetXaxis()->SetLabelSize(0.05);
   multigraph->GetXaxis()->SetTitleSize(0.06);
   multigraph->GetXaxis()->SetTitleOffset(1.2);
   multigraph->GetXaxis()->SetTitleFont(42);
   multigraph->GetYaxis()->SetTitle("#mu_{Bkd}");
   multigraph->GetYaxis()->SetLabelFont(42);
   multigraph->GetYaxis()->SetLabelSize(0.05);
   multigraph->GetYaxis()->SetTitleSize(0.06);
   multigraph->GetYaxis()->SetTitleOffset(1.2);
   multigraph->GetYaxis()->SetTitleFont(42);
   multigraph->SetMinimum(0);
   multigraph->SetMaximum(1.494839);
   TMarker *marker = new TMarker(2.939037,0.7282237,34);

   ci = TColor::GetColor("#0000ff");
   marker->SetMarkerColor(ci);
   marker->SetMarkerStyle(34);
   marker->SetMarkerSize(1.5);
   marker->Draw();
   marker = new TMarker(1,1,30);

   ci = TColor::GetColor("#ff0000");
   marker->SetMarkerColor(ci);
   marker->SetMarkerStyle(30);
   marker->SetMarkerSize(1.7);
   marker->Draw();
   
   TLegend *leg = new TLegend(0.23,0.19,0.46,0.337,NULL,"brNDC");
   leg->SetBorderSize(0);
   leg->SetTextSize(0.045);
   leg->SetLineColor(1);
   leg->SetLineStyle(1);
   leg->SetLineWidth(1);
   leg->SetFillColor(0);
   leg->SetFillStyle(0);
   TLegendEntry *entry=leg->AddEntry("Graph","observed 68% CL.","l");

   ci = TColor::GetColor("#0000ff");
   entry->SetLineColor(ci);
   entry->SetLineStyle(7);
   entry->SetLineWidth(2);
   entry->SetMarkerColor(1);
   entry->SetMarkerStyle(21);
   entry->SetMarkerSize(1);
   entry->SetTextFont(42);
   entry=leg->AddEntry("Graph","observed 95% CL.","l");

   ci = TColor::GetColor("#0000ff");
   entry->SetLineColor(ci);
   entry->SetLineStyle(1);
   entry->SetLineWidth(2);
   entry->SetMarkerColor(1);
   entry->SetMarkerStyle(21);
   entry->SetMarkerSize(1);
   entry->SetTextFont(42);
   entry=leg->AddEntry("TMarker","observed best fit","p");
   entry->SetLineColor(1);
   entry->SetLineStyle(1);
   entry->SetLineWidth(1);

   ci = TColor::GetColor("#0000ff");
   entry->SetMarkerColor(ci);
   entry->SetMarkerStyle(34);
   entry->SetMarkerSize(1.5);
   entry->SetTextFont(42);
   entry=leg->AddEntry("TMarker","SM pred.","p");
   entry->SetLineColor(1);
   entry->SetLineStyle(1);
   entry->SetLineWidth(1);

   ci = TColor::GetColor("#ff0000");
   entry->SetMarkerColor(ci);
   entry->SetMarkerStyle(30);
   entry->SetMarkerSize(1.7);
   entry->SetTextFont(42);
   leg->Draw();
   TLatex *   tex = new TLatex(0.6,0.89,"ATLAS");
   tex->SetNDC();
   tex->SetTextAlign(13);
   tex->SetTextFont(72);
   tex->SetTextSize(0.045);
   tex->SetLineWidth(2);
   tex->Draw();
      tex = new TLatex(0.72,0.89,"Internal");
   tex->SetNDC();
   tex->SetTextAlign(13);
   tex->SetTextFont(42);
   tex->SetTextSize(0.045);
   tex->SetLineWidth(2);
   tex->Draw();
      tex = new TLatex(0.6,0.79,"#splitline{#sqrt{s} = 13 TeV, 140 fb^{-1}}{H+c, H#rightarrow#gamma#gamma}");
   tex->SetNDC();
   tex->SetTextAlign(12);
   tex->SetTextFont(42);
   tex->SetTextSize(0.045);
   tex->SetLineWidth(2);
   tex->Draw();
   canv->Modified();
   canv->SetSelected(canv);
}
