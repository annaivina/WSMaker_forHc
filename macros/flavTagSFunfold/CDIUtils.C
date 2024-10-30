/*
 * Code to interface with the CDI file and extract information on the SFs from it.
 *
 * Author: Philipp Windischhofer
 * Date:   November 2019
 * Email:  philipp.windischhofer@cern.ch
 *
 */

/*
 * Returns the cut value on the tagger output for a certain tagger, jet collection and working point.
 * Arguments:
 *     CDI_path ... full path to the CDI file
 *     tagger ... name of the tagger
 *     jet_collection ... name of the jet collection (using the naming convention in the CDI)
 *     WP ... name of the working point (Note: for this to make sense, the WP has to be of the form 'FixedCutBEff_..',
 * where the last two characters label the b-efficiency) Returns: the cut value demanded by this WP
 */
double GetTaggerWeightCutValue(const std::string& CDI_path, const std::string& tagger,
                               const std::string& jet_collection, const std::string& WP)
{
  // no b-tagging tool seems to be able to allow to access the cut value directly -> just extract it manually from the
  // CDI
  TFile*           CDI_obj    = new TFile(CDI_path.c_str(), "READ");
  std::string      path       = tagger + "/" + jet_collection + "/" + WP + "/cutvalue";
  TVectorT<float>* cutval_CDI = (TVectorT<float>*)CDI_obj->Get(path.c_str());
  double           cutval     = (*cutval_CDI)[0];

  delete CDI_obj;
  return cutval;
}

/*
 * Returns the MV2 SF for a given jet flavour and WP as a function of the jet p_T, for all systematic variations that
 * are available in this CDI. Arguments: CDI_path ... full path to the CDI file tagger ... name of the tagger WP ...
 * name of the working point (can either be 'FixedCutBEff_..' or 'Continuous') jet_collection ... name of the jet
 * collection (using the naming convention in the CDI) efficiency_map ... identifier of the efficiency map to be
 * accessed (usually 'default') jet_flavour ... flavour of the jet using the PDG MC numbering scheme jet_eta ... eta of
 * the jet (this is important since the SFs are sometimes binned in eta) pT_GeV_min ... minimum jet p_T pT_GeV_max ...
 * maximum jet p_T pT_GeV_stepsize ... increment to be used in the p_T sweep MV2_score ... MV2 score of the jet (this is
 * only important when WP = 'Continuous')
 */
TH2D FillSFHistogram(const std::string& CDI_path, const std::string& tagger, const std::string& WP,
                     const std::string& jet_collection, const std::string& efficiency_map, int jet_flavour,
                     double jet_eta, double pT_GeV_min, double pT_GeV_max, double pT_GeV_stepsize, double MV2_score)
{

  // set up the tool for retrieving SFs
  BTaggingEfficiencyTool* efftool = new BTaggingEfficiencyTool("BTaggingEfficiencyTool");
  efftool->setProperty("OutputLevel", MSG::INFO);
  efftool->setProperty("ScaleFactorFileName", CDI_path);
  efftool->setProperty("TaggerName", tagger);
  efftool->setProperty("OperatingPoint", WP);
  efftool->setProperty("JetAuthor", jet_collection);
  efftool->setProperty("SystematicsStrategy", "SFEigen");
  efftool->setProperty("EfficiencyBCalibrations", efficiency_map);
  efftool->setProperty("EfficiencyCCalibrations", efficiency_map);
  efftool->setProperty("EfficiencyTCalibrations", efficiency_map);
  efftool->setProperty("EfficiencyLightCalibrations", efficiency_map);
  StatusCode code = efftool->initialize();

  if( code != StatusCode::SUCCESS ) {
    std::cout << "Initialization of BTaggingEfficiencyTool failed!";
    throw;
  }

  // get the list of systematics affecting this tool
  CP::SystematicSet systs        = efftool->affectingSystematics();
  int               number_systs = systs.size();

  std::cout << "found the following " << number_systs << " systematics affecting the SF" << std::endl;
  for( auto cur_syst : systs ) {
    std::cout << cur_syst.name() << std::endl;
  }

  // prepare the pT binning to use
  std::vector<double> pT_bin_edges;
  for( double pT_GeV = pT_GeV_min; pT_GeV < pT_GeV_max; pT_GeV += pT_GeV_stepsize ) {
    pT_bin_edges.push_back(pT_GeV);
  }

  std::vector<double> pT_bin_centers;
  for( unsigned int ind = 0; ind < pT_bin_edges.size() - 1; ind++ ) {
    pT_bin_centers.push_back(0.5 * (pT_bin_edges[ind] + pT_bin_edges[ind + 1]));
  }

  // prepare the histogram holding the result
  TH2D         rethist("rethist", "rethist", pT_bin_edges.size() - 1, pT_bin_edges.data(), number_systs + 1, 0,
                       number_systs + 1);
  unsigned int bin_ind = 1;
  rethist.GetYaxis()->SetBinLabel(bin_ind, "Nominal");
  for( auto cur_syst : systs ) {
    bin_ind++;
    rethist.GetYaxis()->SetBinLabel(bin_ind, cur_syst.name().c_str());
  }

  // prepare the jet and BTagging containers
  xAOD::Jet* curJet = new xAOD::Jet;
  curJet->makePrivateStore();
  curJet->setAttribute("ConeTruthLabelID", jet_flavour);
  curJet->setAttribute("HadronConeExclTruthLabelID", jet_flavour);

  xAOD::BTagging* btag = new xAOD::BTagging;
  btag->makePrivateStore();
  btag->setVariable<double>(tagger, "discriminant",
                            MV2_score); // for DL1*, a different naming convention is used to store the tagger output

  // need to be a bit more elaborate here, since the Jet stores an ElementLink to the bTagging object
  xAOD::TStore                store;
  std::string                 btag_cont_name = "bTagging";
  xAOD::BTaggingContainer*    btag_cont      = new xAOD::BTaggingContainer();
  xAOD::BTaggingAuxContainer* btag_cont_aux  = new xAOD::BTaggingAuxContainer();
  store.record(btag_cont_aux, btag_cont_name + "Aux.");
  btag_cont->setStore(btag_cont_aux);
  store.record(btag_cont, btag_cont_name);
  btag_cont->push_back(btag);

  xAOD::TEvent* ev = new xAOD::TEvent();
  ev->record(btag_cont, btag_cont_name);

  ElementLink<xAOD::BTaggingContainer> linkBTagger(ev);
  linkBTagger.toContainedElement(*btag_cont, btag);
  curJet->setAttribute("btagging", linkBTagger);

  // extract the b-tagging SF as a function of jet pT
  for( double pT_GeV : pT_bin_centers ) {

    // JetFourMom is just a typedef for ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<double> >
    xAOD::JetFourMom_t jetp4(pT_GeV * 1e3, jet_eta, 0.0, 1000.0);
    curJet->setJetP4(jetp4);

    std::string systName     = "Nominal";
    int         pT_bin_ind   = rethist.GetXaxis()->FindBin(pT_GeV);
    int         syst_bin_ind = rethist.GetYaxis()->FindBin(systName.c_str());

    // get the nominal scale factor and store it
    float SF_nominal;
    efftool->getScaleFactor(*curJet, SF_nominal);
    rethist.SetBinContent(pT_bin_ind, syst_bin_ind, SF_nominal);

    // get all the systematically varied SFs and save them as well
    for( auto cur_syst : systs ) {
      syst_bin_ind = rethist.GetYaxis()->FindBin(cur_syst.name().c_str());

      CP::SystematicSet var;
      var.insert(cur_syst);
      efftool->applySystematicVariation(var);

      float SF_alternative;
      efftool->getScaleFactor(*curJet, SF_alternative);
      rethist.SetBinContent(pT_bin_ind, syst_bin_ind, SF_alternative);

      // reset the applied systematic
      var.clear();
      efftool->applySystematicVariation(var);
    }
  }

  // clean up
  delete efftool;

  return rethist;
}
