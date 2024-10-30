#include <TTree.h>
#include <TGraph.h>
#include <TF1.h>
#include <TCanvas.h>
#include <iostream>



 void plot() {

   // Open the ROOT file
    TFile *file = TFile::Open("outputs_data/Data/LikelihoodLandscape_out.root", "READ");

    // Get the tree
    TTree *tree = (TTree*)file->Get("NLLscan");

    // Set up a Canvas
    TCanvas *canvas = new TCanvas("canvas", "NLL vs Mu", 800, 600);

    // Assuming 'mu' is your parameter and 'NLL' is your negative log-likelihood
    // Create a Graph
    TGraph *graph = new TGraph();
    graph->SetNameTitle("graph", "NLL vs. Mu;Mu;NLL");

    // Assuming 'mu' and 'NLL' are your branch names
    Double_t mu, NLL;
    tree->SetBranchAddress("mu", &mu);
    tree->SetBranchAddress("NLL", &NLL);

    double minNLL,correspondingMu;

    // Loop over the tree entries and fill the graph
    Int_t nentries = (Int_t)tree->GetEntries();
    for (Int_t i = 0; i < nentries; i++) {
        tree->GetEntry(i);
        graph->SetPoint(i, mu, NLL);

        if (NLL < 100) {
            minNLL = NLL;
            correspondingMu = mu;
        }
    }

    // Print out the results
    std::cout << "Minimum NLL value is " << minNLL
              << " for mu = " << correspondingMu << std::endl;


    // Draw the graph
    graph->Draw("AP");
    graph->SetMarkerStyle(8);
    graph->SetMarkerColor(kRed);



  // Save the Canvas
  //  canvas->SaveAs("NLL_vs_mu_with_fit_eps001.png");

    // Clean up
    //delete graph;
    //delete canvas;
    //file->Close();
    //delete file;
}
