#include "sampleincategory.hpp"

#include <algorithm>
#include <cmath>
#include <iostream>
#include <memory>
#include <numeric>
#include <set>

#include <TString.h>

#include "binning.hpp"
#include "category.hpp"
#include "configuration.hpp"
#include "outputhandler.hpp"
#include "sample.hpp"
#include "systematic.hpp"
#include "utility.hpp"

// this is maybe a bit convoluted, but it really smooth things around ...
// some arbitrary choices are needed here
TH1* makeBand(TH1* Hup, TH1* Hdo, TH1* Hnom)
{
  TH1* band = (TH1*)Hup->Clone();
  band->Reset();
  // band->Clear();
  for( int bin = 0; bin <= Hup->GetNbinsX(); bin++ ) {
    float vUp  = Hup->GetBinContent(bin);
    float vDo  = Hdo->GetBinContent(bin);
    float fVal = 0;
    float vNom = Hnom->GetBinContent(bin);
    if( vNom == 0 ) {
      band->SetBinContent(bin, fVal);
      continue;
    }
    float nextUp = Hup->GetBinContent(bin + 1);
    float nextDo = Hdo->GetBinContent(bin + 1);
    // float prevUp=Hup->GetBinContent(bin-1);
    // float prevDo=Hdo->GetBinContent(bin-1);

    if( vUp == 0 || vDo == 0 ) {
      // hopefully this should almost never happen
      fVal = (vUp - vDo);
    } else if( vUp * vDo < 0 ) {
      // opposite sign variations: so this is easy [should I flip simple 1-bin mismatch although they are coherent?
      fVal = (vUp - vDo);
    } else {
      // same sign variation
      // CONSERVATIVE HERE: instead of shrinking the variatoin to the difference, we blow it up
      // fVal=vUp/fabs(vUp)*(fabs(vUp)+fabs(vDo));
      // not so conservative anymore
      fVal = (vUp - vDo);
      // float avg=fabs(vUp)+fabs(vDo);
      // special for the first bin:
      if( bin == 1 ) {
        // promote the variation which goes in the same direction as next bin (conservative when smoothing will be
        // applied)
        if( vUp * nextUp > 0 && vDo * nextDo < 0 ) {
          // same sign as up variation
          fVal = fabs(fVal) * vUp / fabs(vUp); // find a smarter C++ way
        } else if( vUp * nextUp < 0 && vDo * nextDo > 0 ) {
          // same sign as low variation
          fVal = fabs(fVal) * vDo / fabs(vDo); // find a smarter C++ way
        } else {
          // not much can be done in the case both agrees or disagree
        }
      }
      // else {
      //  	// only flip sign if adjacent bins are in opposite direction
      //  	if ( nextUp*prevUp>0 && vUp*nextUp<0 ) {
      //  	  // flip the sign
      //  	  fVal=-1*fabs(fVal)*vUp/fabs(vUp); //find a smarter C++ way
      //  	}
      //  	if ( nextDo*prevDo>0 && vDo*nextDo<0 ) {
      //  	  // flip the sign
      //  	  fVal=-1*fabs(fVal)*vDo/fabs(vDo); //find a smarter C++ way
      //  	}
      //  }
    }

    band->SetBinContent(bin, fVal);
  }
  return band;
}

SampleInCategory::SampleInCategory(Category& cat, Sample& s, TH1* hist, TH2* smoothedCorrHist) :
    m_cat(cat),
    m_sample(s),
    m_nomHist(hist),
    m_systs(),
    m_systsStatus(),
    m_originalNomHist((TH1*)hist->Clone((hist->GetName() + std::string("_orig")).c_str())),
    m_smoothedNomCorrHist(smoothedCorrHist ? (TH2*)smoothedCorrHist->Clone() : nullptr),
    m_MCStatSys(nullptr)
{}

// merge constructor
SampleInCategory::SampleInCategory(Category& cat, Sample& s, const std::vector<SampleInCategory*>& sicToMerge) :
    m_cat(cat),
    m_sample(s),
    m_nomHist(nullptr),
    m_systs(),
    m_systsStatus(),
    m_originalNomHist(nullptr),
    m_smoothedNomCorrHist(nullptr),
    m_MCStatSys(nullptr)
{
  // 1. sum the nominal histograms
  for( const auto p : sicToMerge ) {
    if( m_nomHist == nullptr ) {
      m_nomHist.reset((TH1*)(p->getNomHist()->Clone(m_sample.name())));
    } else {
      m_nomHist->Add(p->getNomHist());
    }
  }

  m_originalNomHist.reset((TH1*)m_nomHist->Clone((m_nomHist->GetName() + std::string("_orig")).c_str()));

  // 2. compute binning for systs (needed ?)
  computeBinningForSysts();

  // 3. systematics.
  for( auto sic_it = sicToMerge.begin(); sic_it != sicToMerge.end(); ++sic_it ) {
    SampleInCategory& sic = *(*sic_it);
    for( SysIterator sys = sic.m_systs.begin(); sys != sic.m_systs.end(); ++sys ) {
      const SysKey&  key     = sys->first;
      const TString& sysname = key.second;
      // case of floating norm: we have to check that all merged samples have it !
      if( key.first == SysType::flt ) {
        if( std::any_of(sic_it + 1, sicToMerge.end(),
                        [&key](const SampleInCategory* s) { return !(s->hasSyst(key.first, key.second)); }) ) {
          std::cerr << "SampleInCategory::SampleInCategory: Not all merged SiC have a "
                    << "NormFactor named " << sysname << std::endl;
          throw;
        }
        m_systs.emplace(key, sys->second);
        m_systsStatus.emplace(key, SysStatus::Used);
        for( auto sic2_it = sic_it + 1; sic2_it != sicToMerge.end(); ++sic2_it ) {
          (*sic2_it)->deleteSyst(key);
        }
      } else {
        // we cannot delete systs of sic on-the-fly. Well, we could, but that would
        // be troublesome. So, instead, just do a lookup to avoid double-putting a systematic.
        // The case that is then avoided is when a syst has both norm and shape components
        // in sic, where we would find it twice.
        if( hasSyst(SysType::norm, sysname) || hasSyst(SysType::shape, sysname) ) {
          continue;
        }
        // compute the shifted up/do summed histograms for this syst
        TH1* hup = nullptr;
        TH1* hdo = nullptr;

        std::shared_ptr<TH1> hup_unsmoothed;
        std::shared_ptr<TH1> hdo_unsmoothed;
        const bool           needToMergeUnsmoothed =
            std::any_of(sicToMerge.begin(), sicToMerge.end(), [&sysname](const SampleInCategory* s) {
              std::map<SysKey, Systematic, SysOrdering>::const_iterator foundItem =
                  s->m_systs.find(std::make_pair(SysType::shape, sysname));
              if( foundItem != s->m_systs.end() ) {
                return foundItem->second.shape_do_unsmoothed || foundItem->second.shape_up_unsmoothed;
              }
              return false;
            });

        for( auto psic2 : sicToMerge ) {
          SampleInCategory& sic2 = *psic2;
          TH1*              tmp  = sic2.getFullSystShape(sysname, Systematic::Side::up);
          if( hup == nullptr ) {
            hup = tmp;
            hup->SetName(m_nomHist->GetName());
          } else {
            hup->Add(tmp);
            delete tmp;
          }
          tmp = sic2.getFullSystShape(sysname, Systematic::Side::down);
          if( hdo == nullptr ) {
            hdo = tmp;
            hdo->SetName(m_nomHist->GetName());
          } else {
            hdo->Add(tmp);
            delete tmp;
          }

          if( needToMergeUnsmoothed ) {
            std::shared_ptr<TH1>                                      src_up;
            std::shared_ptr<TH1>                                      src_do;
            std::map<SysKey, Systematic, SysOrdering>::const_iterator foundShapeSys =
                sic2.m_systs.find(std::make_pair(SysType::shape, sysname));
            if( foundShapeSys != sic2.m_systs.end() ) {
              // This sample does have a shape sys
              src_up = foundShapeSys->second.shape_up_unsmoothed;
              src_do = foundShapeSys->second.shape_do_unsmoothed;
            }
            if( src_up == nullptr ) {
              src_up.reset(static_cast<TH1*>(sic2.getNomHist()->Clone()));
              src_up->SetDirectory(0);
            }
            if( src_do == nullptr ) {
              src_do.reset(static_cast<TH1*>(sic2.getNomHist()->Clone()));
              src_do->SetDirectory(0);
            }
            // scale with norm to get proper bkg composition
            // will be split into norm and shape syst later
            std::map<SysKey, Systematic, SysOrdering>::const_iterator foundNormSys =
                sic2.m_systs.find(std::make_pair(SysType::norm, sysname));
            if( foundNormSys != sic2.m_systs.end() ) {
              src_up->Scale(foundNormSys->second.var_up);
              src_do->Scale(foundNormSys->second.var_do);
            }

            // add, steal or clone a sys histo
            if( hup_unsmoothed ) {
              hup_unsmoothed->Add(src_up.get());
            } else {
              hup_unsmoothed = src_up;
              hup_unsmoothed->SetName((m_nomHist->GetName() + std::string("_up_unsmoothed")).c_str());
            }

            if( hdo_unsmoothed ) {
              hdo_unsmoothed->Add(src_do.get());
            } else {
              hdo_unsmoothed = src_do;
              hdo_unsmoothed->SetName((m_nomHist->GetName() + std::string("_do_unsmoothed")).c_str());
            }
          }

          // delete this syst from the other SiC to avoid retrying the addition.
          if( &sic != &sic2 ) { // compare pointers
            sic2.deleteSyst(std::make_pair(SysType::norm, sysname));
            sic2.deleteSyst(std::make_pair(SysType::shape, sysname));
          }
        }
        // then create the appropriate Systematics
        addSyst(sysname, Systematic::Side::up, STreat::shape, hup, sys->second.smooth, sys->second.symmetrise,
                hup_unsmoothed);
        addSyst(sysname, Systematic::Side::down, STreat::shape, hdo, sys->second.smooth, sys->second.symmetrise,
                hdo_unsmoothed);
      }
    }
  }

  // 4. MC stat uncertainties

  // do we need a MC stat unc?
  // if nobody has MCstat, fine
  if( std::none_of(sicToMerge.begin(), sicToMerge.end(),
                   [](const SampleInCategory* s) { return (bool)s->getMCStatSys(); }) ) {
    // then nothing to do
  } else {
    // does any has MC stat (and the same ?)

    auto sic_it = sicToMerge.begin();
    if( !(*sic_it)->getMCStatSys() || std::any_of(sic_it + 1, sicToMerge.end(), [&sic_it](const SampleInCategory* s) {
          if( !s->getMCStatSys() )
            return true;
          return s->getMCStatSys()->name != (*sic_it)->getMCStatSys()->name;
        }) ) {
      std::cerr << "SampleInCategory::SampleInCategory: Sample with different stat uncertainty name or without valid "
                   "MC stat sys exists."
                << std::endl;
      throw;
    }

    TH1*    stat_err   = nullptr;
    TString mcstatname = (*sic_it)->getMCStatSys()->name;
    for( auto psic : sicToMerge ) {
      SampleInCategory& sic = *psic;
      Utils::sumOfSquares(stat_err, sic.getMCStatSys()->mc_stat_error_absolute_sample.get());
    }
    Utils::squareRootOfHist(stat_err);

    Systematic* psys = new Systematic(SysType::MCstat, mcstatname);
    psys->mc_stat_error_absolute_sample.reset(stat_err);
    psys->mc_stat_error_fractional_shared = (*sic_it)->getMCStatSys()->mc_stat_error_fractional_shared;
    m_MCStatSys.reset(psys);

    // no need to worry about deleteSys
  }

  // 5. Remove old nominal histograms.
  for( auto& sic : sicToMerge ) {
    sic->m_nomHist.reset();
  }
}

SampleInCategory::~SampleInCategory() {}

bool SampleInCategory::hasSyst(SysType type, const TString& name) const
{
  return m_systs.count(std::make_pair(type, name));
}

const Systematic& SampleInCategory::getSyst(SysType type, const TString& name) const
{
  return m_systs.at(std::make_pair(type, name));
}

void SampleInCategory::addSyst(const TString& sysname, Systematic::Side side, STreat treat, TH1* hsys,
                               SysConfig::Smooth smooth, SysConfig::Symmetrise symmetrise,
                               std::shared_ptr<TH1> hsys_unsmoothed, float scaleFactor)
{

  // look at norm effect
  float varNorm = hsys->Integral();
  float nomNorm = m_nomHist->Integral();
  float var     = varNorm / nomNorm;

  if( std::isnan(var) ) {
    std::cerr << "ERROR::SampleInCategory::addSyst" << std::endl;
    std::cerr << "Syst " << sysname << " in " << name() << " comes with empty histogram(s): varNorm = " << varNorm
              << ", nomNorm = " << nomNorm << std::endl;
    return; // do not add the systematic
  }

  if( treat != STreat::shapeonly && (var < 0.01 || var > 1.99)) {
    if ( !(Configuration::analysisType() == AnalysisType::VHqqRun2 && sysname.Contains("WtDR"))){
      std::cerr << "ERROR::SampleInCategory::addSyst" << std::endl;
      std::cerr << "Variation for syst " << sysname << " too drastic: " << name() << " = " << var << std::endl;
      return; // FIXME it is return because of some low stat samples. Should make it more clever.
      // throw
    }
  }

  // Scale the histograms if requested
  if( scaleFactor != 1.0 ) {
    // Scale the smoothed and unsmoothed histograms
    scaleHistoSys(hsys, scaleFactor);
    if( hsys_unsmoothed != nullptr )
      scaleHistoSys(hsys_unsmoothed.get(), scaleFactor);
    // Recalculate the variation after scaling
    varNorm = hsys->Integral();
    var     = varNorm / nomNorm;
  }

  // we do care about norm
  if( treat == STreat::norm || treat == STreat::shape ) {
    Systematic sys(SysType::norm, sysname);
    switch( side ) {
      case Systematic::Side::up:
        sys.var_up = var;
        break;
      case Systematic::Side::down:
        sys.var_do = var;
        break;
    }
    sys.smooth     = smooth;
    sys.symmetrise = symmetrise;
    addSyst(std::move(sys));
  }

  // now look at shape effect
  if( treat == STreat::shapeonly || treat == STreat::shape ) {
    // not sure I can really do it right now ..
    hsys->Scale(1. / var);
    if( hsys_unsmoothed ) {
      hsys_unsmoothed->Scale(nomNorm / hsys_unsmoothed->Integral());
    }
    // Now create a Systematic object and add it to the SampleInCategory
    Systematic sys(SysType::shape, sysname);
    switch( side ) {
      case Systematic::Side::up:
        sys.shape_up.reset(hsys);
        sys.shape_up_unsmoothed = hsys_unsmoothed;
        break;
      case Systematic::Side::down:
        sys.shape_do.reset(hsys);
        sys.shape_do_unsmoothed = hsys_unsmoothed;
        break;
    }
    sys.smooth     = smooth;
    sys.symmetrise = symmetrise;
    // We take over memory management from root here
    hsys->SetDirectory(0);
    addSyst(std::move(sys));
  }
}

void SampleInCategory::addMCStatSyst(const TString& sysname)
{

  TH1* err   = (TH1*)m_nomHist->Clone(sysname);
  int  nbins = m_nomHist->GetNbinsX();
  for( int bin = 0; bin <= nbins + 1; ++bin ) {
    err->SetBinContent(bin, m_nomHist->GetBinError(bin));
  }
  Systematic* psys = new Systematic(SysType::MCstat, sysname);
  psys->mc_stat_error_absolute_sample.reset(err);
  m_MCStatSys.reset(psys);
}

void SampleInCategory::averageShape(Systematic& sys)
{
  TH1* hup = sys.shape_up.get();
  TH1* hdo = sys.shape_do.get();
  // only average if both up and down variation are present
  // else the systematic gets pruned anyhow
  if( hup && hdo ) {
    hup->Add(m_nomHist.get(), -1);
    hdo->Add(m_nomHist.get(), -1);
    TH1* band = makeBand(hup, hdo, m_nomHist.get());
    band->Scale(0.5);                // this is now the new 'band'
    hup->Add(m_nomHist.get(), band); // this TH1::Add replaces contents of the original histo.
    hdo->Add(m_nomHist.get(), band, 1., -1);
    hup->Scale(m_nomHist->Integral(0, -1) / hup->Integral(0, -1));
    hdo->Scale(m_nomHist->Integral(0, -1) / hdo->Integral(0, -1));
    delete band;
  }
}

void SampleInCategory::averageNorm(Systematic& sys)
{
  float half_diff = (sys.var_up - sys.var_do) / 2; // this is properly signed !
  sys.var_up      = 1 + half_diff;
  sys.var_do      = 1 - half_diff;
}

void SampleInCategory::symmetriseOneSidedNorm(Systematic& sys)
{
  // Handle 1-sided systematics
  if( sys.var_up == 1 && sys.var_do != 1 ) { // only down variation present
    sys.var_up = 2 - sys.var_do;
  } else if( sys.var_up != 1 && sys.var_do == 1 ) { // only up variation present
    sys.var_do = 2 - sys.var_up;
  } else if( sys.var_up != 1 && sys.var_do != 1 ) { // to change in a crash case once VHbb inputs corrected
    std::cout << "Error::SymOneSidedNorm: one sided sys (" << sys.name << ") has 2 variations (norm up=" << sys.var_up
              << ",do=" << sys.var_do << ")  -> check your inputs" << std::endl;
    sys.var_do = 2 - sys.var_up;
  }
}

void SampleInCategory::symmetriseOneSidedShape(Systematic& sys)
{
  TH1* hup = sys.shape_up.get();
  TH1* hdo = sys.shape_do.get();
  // If only up or down variation present then symmetrise
  if( hup == nullptr && hdo != nullptr ) {
    hdo = getFullSystShape(sys.name, Systematic::Side::down);
    hup = Utils::symmetrize(hdo, m_nomHist.get());
    hup->Scale(m_nomHist.get()->Integral() / hup->Integral());
    sys.shape_up.reset(hup);
    delete hdo;
  } else if( hup != nullptr && hdo == nullptr ) {
    hup = getFullSystShape(sys.name, Systematic::Side::up);
    hdo = Utils::symmetrize(hup, m_nomHist.get());
    hdo->Scale(m_nomHist.get()->Integral() / hdo->Integral());
    sys.shape_do.reset(hdo);
    delete hup;
  } else if( hup != nullptr && hdo != nullptr ) { // to change in a crash case once VHbb inputs corrected
    hup = getFullSystShape(sys.name, Systematic::Side::up);
    std::cout << "Error::SymOneSidedShape: one sided sys (" << sys.name << ") has 2 variations -> check your inputs"
              << std::endl;
    hdo = Utils::symmetrize(hup, m_nomHist.get());
    hdo->Scale(m_nomHist.get()->Integral() / hdo->Integral());
    sys.shape_do.reset(hdo);
    delete hup;
  }
}

void SampleInCategory::addSyst(const Systematic& sys)
{
  SysKey      key = std::make_pair(sys.type, sys.name);
  const auto& pos = m_systs.find(key);
  if( pos == m_systs.end() ) {
    m_systs.emplace(key, sys);
    const auto& posStatus = m_systsStatus.find(key);
    if( posStatus == m_systsStatus.end() ) {
      m_systsStatus.emplace(key, SysStatus::Used);
    } else {
      posStatus->second = SysStatus::Used;
    }
  } else {
    pos->second.merge(sys);
  }
}

void SampleInCategory::addSyst(Systematic&& sys)
{
  // TODO add some pretty logging
  SysKey      key = std::make_pair(sys.type, sys.name);
  const auto& pos = m_systs.find(key);
  if( pos == m_systs.end() ) {
    // TODO check definition of move to see if needed in that case
    m_systs.emplace(key, std::move(sys));
    const auto& posStatus = m_systsStatus.find(key);
    if( posStatus == m_systsStatus.end() ) {
      m_systsStatus.emplace(key, SysStatus::Used);
    } else {
      posStatus->second = SysStatus::Used;
    }
  } else {
    pos->second.merge(sys);
  }
}

TH1* SampleInCategory::getFullSystShape(const TString& name, Systematic::Side side) const
{
  TH1* hist = nullptr;
  if( hasSyst(SysType::shape, name) ) {
    switch( side ) {
      case Systematic::Side::up:
        if( getSyst(SysType::shape, name).shape_up != nullptr ) {
          hist = (TH1*)(getSyst(SysType::shape, name).shape_up->Clone());
        }
        break;
      case Systematic::Side::down:
        if( getSyst(SysType::shape, name).shape_do != nullptr ) {
          hist = (TH1*)(getSyst(SysType::shape, name).shape_do->Clone());
        }
        break;
    }
  }
  // if no shape syst, or shape syst does not exist on this side, just copy the nominal
  if( hist == nullptr ) {
    hist = (TH1*)(m_nomHist->Clone());
  }

  if( hasSyst(SysType::norm, name) ) {
    switch( side ) {
      case Systematic::Side::up:
        hist->Scale(getSyst(SysType::norm, name).var_up);
        break;
      case Systematic::Side::down:
        hist->Scale(getSyst(SysType::norm, name).var_do);
        break;
      default:
        throw;
    }
  }

  return hist;
}

void SampleInCategory::computeBinningForSysts()
{
  BinningTool& binning = BinningTool::getInstance();
  m_sysBins            = binning.getBinningForSysts(m_nomHist.get());
  // getBinningForSysts gives rebinning in reverse order.
  // smoothing function expects bins from left to right.
  std::sort(m_sysBins.begin(), m_sysBins.end());
  if( Configuration::debug() ) {
    std::cout << "INFO::SampleInCategory::computeBinningForSysts: Binning for SiC " << name() << ":" << std::endl;
    for( int b : m_sysBins ) {
      std::cout << b << " ";
    }
    std::cout << std::endl;
  }
}

void SampleInCategory::scaleHistoSys(TH1* hsys, float factor)
{
  for( int b = 0; b <= m_nomHist->GetNbinsX() + 1; b++ ) {
    float nom = m_nomHist->GetBinContent(b);
    float var = hsys->GetBinContent(b);
    if( nom != 0 ) {
      float scale = factor * (var / nom - 1) + 1;
      hsys->SetBinContent(b, scale * nom);
    }
  }
}

void SampleInCategory::smoothHistoRebin(TH1* hsys, SysConfig::Smooth sm)
{
  BinningTool&     binning = BinningTool::getInstance();
  std::vector<int> bins;

  // Get the binning that corresponds to a monotonic or parabolic distribution
  if( sm == SysConfig::Smooth::smoothRebinParabolic )
    bins = binning.getLocalExtremaBinning(m_nomHist.get(), hsys, 1);
  else if( sm == SysConfig::Smooth::smoothRebinMonotonic )
    bins = binning.getLocalExtremaBinning(m_nomHist.get(), hsys, 0);

  // Call the rebinning function
  binning.smoothHistoRebin(m_nomHist.get(), hsys, bins, false);
}

void SampleInCategory::smoothHistoKernel(TH1* hsys, SysConfig::Smooth sm)
{

  BinningTool& binning = BinningTool::getInstance();
  binning.smoothHistoKernel(m_nomHist.get(), hsys, m_sysBins, sm);
}

void SampleInCategory::deleteSyst(const SysKey& key, SysStatus reason)
{
  auto it = m_systs.find(key);
  if( it != m_systs.end() ) {
    m_systs.erase(it);
    m_systsStatus.at(key) = reason;
  }
}

void SampleInCategory::removeSysts(std::function<bool(const Systematic&)>& pred, SysStatus reason)
{
  for( auto it = m_systs.begin(); it != m_systs.end(); ) {
    Systematic& sys = it->second;
    if( pred(sys) ) {
      m_systsStatus.at(it->first) = reason;
      it                          = m_systs.erase(it);
    } else {
      ++it;
    }
  }
}

void SampleInCategory::pruneSmallShapeSysts(float thresh)
{
  for( auto& sysobj : m_systs ) {
    if( sysobj.first.first != SysType::shape ) {
      continue;
    }
    Systematic& sys = sysobj.second;
    deleteIfNoShape(sys.shape_up, thresh);
    deleteIfNoShape(sys.shape_do, thresh);
  }

  // collect and remove shape systs that don't have any surviving histogram
  std::function<bool(const Systematic&)> f = [](const Systematic& sys) {
    return ((sys.type == SysType::shape) && ((sys.shape_up == nullptr) && (sys.shape_do == nullptr)));
  };
  removeSysts(f, SysStatus::PruneSmall);
}

// keep it that way (a very small function that calls another one
// to allow easier future developments with different algorithms
bool SampleInCategory::deleteIfNoShape(std::shared_ptr<TH1>& h, float thresh)
{
  if( h && !hasEnoughShape(h.get(), thresh) ) {
    h.reset();
    return true;
  }
  return false;
}

bool SampleInCategory::hasEnoughShape(TH1* h, float thresh)
{
  int nrBins        = h->GetNbinsX();
  int nBinThreshold = 1;
  if( Configuration::analysisType() == AnalysisType::AZh )
    nBinThreshold = 2;
  int count = 0;

  for( int ibin = 1; ibin < nrBins + 1; ibin++ ) {
    float varBin = h->GetBinContent(ibin);
    float nomBin = m_nomHist->GetBinContent(ibin);
    if( varBin == 0 || nomBin == 0 )
      continue;
    if( (nomBin <= pow(10, -9) && varBin > 10 * pow(10, -9)) || (fabs(varBin / nomBin - 1) > thresh) ) {
      count++;
    }
  }
  if( count > nBinThreshold )
    return true;
  else
    return false;
}

void SampleInCategory::pruneOneSideShapeSysts()
{
  std::function<bool(const Systematic&)> f = [](const Systematic& sys) {
    return ((sys.type == SysType::shape) && ((sys.shape_up == nullptr) || (sys.shape_do == nullptr)));
  };
  removeSysts(f, SysStatus::PruneOneSide);
}

void SampleInCategory::pruneSmallNormSysts(float thresh)
{
  std::function<bool(const Systematic&)> f = [thresh](const Systematic& sys) {
    return ((sys.type == SysType::norm) && (!sys.name.Contains("LUMI")) &&
            ((std::fabs(sys.var_up - 1) < thresh) || (std::fabs(sys.var_do - 1) < thresh)));
  };
  removeSysts(f, SysStatus::PruneSmall);
}

void SampleInCategory::pruneSameSignSysts()
{
  std::function<bool(const Systematic&)> f = [](const Systematic& sys) {
    return ((sys.type == SysType::norm) && ((sys.var_up - 1) * (sys.var_do - 1) >= 0));
  };
  removeSysts(f, SysStatus::PruneOneSide);
}

void SampleInCategory::pruneSpecialTests()
{

  // The following things are specific to VHbb Run2 analysis
  if( (Configuration::analysisType() == AnalysisType::VHbbRun2) ||
      (Configuration::analysisType() == AnalysisType::VHqqRun2) ) {
    // remove all systs except MJ systs on multijet samples
    if( m_sample.type() == SType::DataDriven && m_sample.name().Contains("multijet") ) {
      std::function<bool(const Systematic&)> f = [](const Systematic& sys) {
        return (!sys.name.Contains("MJ") && sys.type != SysType::flt);
      };
      removeSysts(f, SysStatus::PruneOther);
    }
    // remove all systs except Top systs on data-driven ttbar bkg samples
    if( m_sample.type() == SType::DataDriven && m_sample.name().Contains("emuCR") ) {
      std::function<bool(const Systematic&)> f = [](const Systematic& sys) { return (!sys.name.Contains("Top")); };
      removeSysts(f, SysStatus::PruneOther);
    }
  }
}

void SampleInCategory::removeLumiWhenFloat()
{
  if( m_sample.type() != SType::Bkg ) {
    return;
  }
  bool isFloated = std::any_of(m_systs.begin(), m_systs.end(), [](const std::pair<SysKey, Systematic>& syspair) {
    return (syspair.first.first == SysType::flt) && (syspair.second.isConst == false);
  });
  if( !isFloated ) {
    return;
  }

  std::function<bool(const Systematic&)> f = [](const Systematic& sys) { return (sys.name.Contains("ATLAS_LUMI")); };
  removeSysts(f, SysStatus::PruneOther);
}

void SampleInCategory::symmetriseAverageSysts()
{
  // Loop over all user systematics for the sample
  for( auto& sysObject : m_systs ) {
    Systematic& sys = sysObject.second;
    switch( sys.symmetrise ) {
      case SysConfig::Symmetrise::symmetriseAverage:
        // Norm systematics
        if( sys.type == Systematic::Type::norm ) {
          averageNorm(sys);
        }
        // Shape systematics
        else if( sys.type == Systematic::Type::shape ) {
          averageShape(sys);
        }
        break;
      case SysConfig::Symmetrise::symmetriseOneSided:
        // Norm systematics
        if( sys.type == Systematic::Type::norm ) {
          symmetriseOneSidedNorm(sys);
        }
        // Shape systematics
        else if( sys.type == Systematic::Type::shape ) {
          symmetriseOneSidedShape(sys);
        }
        break;
      case SysConfig::Symmetrise::noSym:
        break;
      case SysConfig::Symmetrise::symmetriseUserDefined:
        std::cerr << "ERROR::SampleInCategory::symmetriseAverageSysts\n"
                  << "Your SymFunction returned Symmetrise::symmetriseUserDefined\n"
                  << "Please use one of the symmetrisation types available to the user" << std::endl;
        throw;
    }
  }
}

void SampleInCategory::smoothSysts()
{
  // Loop over all user systematics for the sample
  for( auto& sysObject : m_systs ) {
    Systematic& sys = sysObject.second;

    // Shape systematics
    if( sys.type == Systematic::Type::shape ) {
      // 1st: smooth it if needed
      if( sys.smooth != SysConfig::Smooth::noSmooth ) {
        if( Configuration::debug() ) {
          std::cout << "INFO::SampleInCategory::smoothHisto::Smoothing of " << sys.name << std::endl;
          std::cout << "In " << name() << std::endl << std::endl;
        }
        smoothSysHisto(sys.shape_up.get(), sys.shape_do.get(), sys.smooth);
      }
      // 2nd: For shape systematics make sure that it has the same normalisation as original histo
      float nom = m_nomHist->Integral();
      if( sys.shape_up != nullptr ) {
        float varUp = sys.shape_up.get()->Integral();
        sys.shape_up.get()->Scale(nom / varUp);
      }
      if( sys.shape_do != nullptr ) {
        float varDo = sys.shape_do.get()->Integral();
        sys.shape_do.get()->Scale(nom / varDo);
      }
    }
  }
}

void SampleInCategory::smoothSysHisto(TH1* h_up, TH1* h_do, const SysConfig::Smooth& smooth)
{
  // Decide which smoothing algorithm to use
  switch( smooth ) {
    case SysConfig::Smooth::smoothRatioUniformKernel:
    case SysConfig::Smooth::smoothDeltaUniformKernel:
      if( h_up != nullptr ) {
        if( h_up->GetNbinsX() > 1 )
          smoothHistoKernel(h_up, smooth);
      }
      if( h_do != nullptr ) {
        if( h_do->GetNbinsX() > 1 )
          smoothHistoKernel(h_do, smooth);
      }
      break;
    case SysConfig::Smooth::smoothRebinMonotonic:
    case SysConfig::Smooth::smoothRebinParabolic:
      if( h_up != nullptr )
        smoothHistoRebin(h_up, smooth);
      if( h_do != nullptr )
        smoothHistoRebin(h_do, smooth);
      break;
    default:
      std::cerr << "ERROR::SampleInCategory::smoothHisto\n"
                << "Unknown or unimplemented smoothing algorithm: "
                << static_cast<std::underlying_type<SysConfig::Smooth>::type>(smooth) << std::endl;
      throw;
  }
}

void SampleInCategory::printSystematics() const
{
  std::cout << std::endl
            << "INFO::SampleInCategory::printSystematics:" << std::endl
            << "  Printing systematics for sample " << m_sample.name() << std::endl
            << "    in category " << m_cat.name() << std::endl;
  for( const auto& sysobj : m_systs ) {
    sysobj.second.print();
  }
}

void SampleInCategory::writeNormAndXML(OutputHandler& out, bool statSys) const
{
  // std::cout << std::endl << "INFO::SampleInCategory::writeNormAndXML:" << std::endl
  //<< "  Writing systematics for sample " << m_sample.name() << std::endl
  //<< "    in category " << m_cat.name() << std::endl;
  if( m_sample.type() == SType::Data ) {
    out.addData(m_sample.name(), m_nomHist.get());
  } else {
    out.beginSample(m_sample.name(), m_nomHist.get());
    for( auto& syspair : m_systs ) {
      out.addSyst(syspair.second);
    }
    // StatSys activated only for bkg or MJ
    bool activate = (statSys && (m_sample.type() == SType::Bkg || m_sample.type() == SType::DataDriven));
    if( m_MCStatSys ) {
      activate = false;
      out.addSyst(*m_MCStatSys);
    }
    out.activateStatErr(activate);
    out.closeSample();
  }
}

TString SampleInCategory::name() const { return m_sample.name() + "_in_" + m_cat.name(); }

bool SampleInCategory::isSmoothed() { return (m_nomHist && m_smoothedNomCorrHist); }

float SampleInCategory::integral() const
{
  if( m_nomHist == nullptr ) {
    return 0;
  }
  return m_nomHist->Integral(0, m_nomHist->GetNbinsX() + 1);
}

void SampleInCategory::pruneSmallSysts_Yao(TH1* hsig, TH1* hbkg, bool isSensitiveRegion,
                                           const std::vector<int>& sensitiveBins)
{
  SType stype = m_sample.type();
  // pruning applies to backgrounds only
  if( !(stype == SType::DataDriven || stype == SType::Bkg) ) {
    return;
  }
  // pruning is for small bkgs. Threshold is 1% of total bkg.
  // If above that threshold, then do nothing.
  if( integral() > 0.01 * hbkg->Integral(0, hbkg->GetNbinsX() + 1) ) {
    return;
  }

  // ok, now we look at the systs in details.

  // if sensitive region, then threshold is 2% of signal in the sensitive bins
  if( isSensitiveRegion ) {
    std::function<bool(const Systematic&)> f = [&](const Systematic& sys) {
      bool isPreservedSyst = sys.name.Contains("LUMI");
      if( (Configuration::analysisType() == AnalysisType::VHbbRun2) ||
          (Configuration::analysisType() == AnalysisType::VHqqRun2) ) {
        isPreservedSyst = isPreservedSyst || sys.name.Contains("Light_0") || sys.name.Contains("ZclNorm") ||
                          sys.name.Contains("WclNorm") || sys.name.Contains("ZlNorm") || sys.name.Contains("WlNorm");
      }
      return this->isSysBelow(sensitiveBins, sys, hsig, 0.02) && (!isPreservedSyst);
    };
    removeSysts(f, SysStatus::PruneYao);
  }

  // else threshold is 5 per mille of total background
  else {
    // need to fill vector with all bin numbers
    std::vector<int> bins(hbkg->GetNbinsX());
    std::iota(bins.begin(), bins.end(), 1);
    std::function<bool(const Systematic&)> f = [&](const Systematic& sys) {
      bool isPreservedSyst = sys.name.Contains("LUMI");
      if( (Configuration::analysisType() == AnalysisType::VHbbRun2) ||
          (Configuration::analysisType() == AnalysisType::VHqqRun2) ) {
        isPreservedSyst = isPreservedSyst || sys.name.Contains("Light_0") || sys.name.Contains("ZclNorm") ||
                          sys.name.Contains("WclNorm") || sys.name.Contains("ZlNorm") || sys.name.Contains("WlNorm");
      }
      return this->isSysBelow(bins, sys, hbkg, 0.005) && (!isPreservedSyst);
    };
    removeSysts(f, SysStatus::PruneYao);
  }
}

bool SampleInCategory::isSysBelow(const std::vector<int>& bins, const Systematic& sys, TH1* ref, float thresh)
{
  if( sys.type == SysType::flt ) {
    return false;
  }
  if( sys.type == SysType::norm ) {
    return std::none_of(bins.begin(), bins.end(), [&](int b) {
      return (fabs(this->m_nomHist->GetBinContent(b) * (1 - sys.var_up)) > fabs(ref->GetBinContent(b)) * thresh) ||
             (fabs(this->m_nomHist->GetBinContent(b) * (1 - sys.var_do)) > fabs(ref->GetBinContent(b)) * thresh);
    });
  }
  // else shape
  bool shape_up_below = true;
  bool shape_do_below = true;
  if( sys.shape_up != nullptr ) {
    shape_up_below = std::none_of(bins.begin(), bins.end(), [&](int b) {
      return fabs(this->m_nomHist->GetBinContent(b) - sys.shape_up->GetBinContent(b)) >
             fabs(ref->GetBinContent(b)) * thresh;
    });
  }
  if( sys.shape_do != nullptr ) {
    shape_do_below = std::none_of(bins.begin(), bins.end(), [&](int b) {
      return fabs(this->m_nomHist->GetBinContent(b) - sys.shape_do->GetBinContent(b)) >
             fabs(ref->GetBinContent(b)) * thresh;
    });
  }
  return shape_up_below && shape_do_below;
}

void SampleInCategory::pruneSmallShapeSysts_Htautau(TH1* hbkg)
{
  float thresh = 0.1;

  SType stype = m_sample.type();
  // pruning applies to backgrounds only
  if( stype == SType::Data || stype == SType::Sig ) {
    return;
  }
  std::vector<int> bins(hbkg->GetNbinsX());
  std::iota(bins.begin(), bins.end(), 1);
  std::function<bool(const Systematic&)> f = [&](const Systematic& sys) {
    if( sys.type != SysType::shape ) {
      return false;
    }
    return std::none_of(bins.begin(), bins.end(), [&](int b) {
      return fabs(sys.shape_up->GetBinContent(b) - sys.shape_do->GetBinContent(b)) >
             fabs(hbkg->GetBinError(b)) * thresh;
    });
  };
  removeSysts(f, SysStatus::PruneOther);
}

void SampleInCategory::pruneSmallShapeSysts_chi2()
{
  float thresh = 0.99;

  SType stype = m_sample.type();
  // pruning applies to MC only
  if( stype == SType::Data || stype == SType::DataDriven ) {
    return;
  }
  std::function<bool(const Systematic&)> f = [&](const Systematic& sys) {
    if( sys.type != SysType::shape ) {
      return false;
    }
    if( sys.smooth == SysConfig::Smooth::noSmooth ) {
      return false;
    }
    return (this->m_nomHist->Chi2Test(sys.shape_up.get(), "WW") > thresh) &&
           (this->m_nomHist->Chi2Test(sys.shape_do.get(), "WW") > thresh);
  };
  removeSysts(f, SysStatus::PruneOther);
}

void SampleInCategory::pruneSmallShapeSysts_chi2_samesign()
{
  SType stype = m_sample.type();
  // pruning applies to MC only
  if( stype == SType::Data || stype == SType::DataDriven ) {
    return;
  }
  std::function<bool(const Systematic&)> f = [&](const Systematic& sys) {
    if( sys.type != SysType::shape ) {
      return false;
    }
    // this pruning only applies to smoothed systematics
    if( sys.smooth == SysConfig::Smooth::noSmooth ) {
      return false;
    }
    double chi2ref = std::max(this->m_nomHist->Chi2Test(sys.shape_up.get(), "WW"),
                              this->m_nomHist->Chi2Test(sys.shape_do.get(), "WW"));
    for( int i = 0; i < sys.shape_up->GetNbinsX() + 2; i++ ) {
      sys.shape_up->SetBinError(i, this->m_nomHist->GetBinError(i));
    }
    double chi2test = sys.shape_up->Chi2Test(sys.shape_do.get(), "WW");
    for( int i = 0; i < sys.shape_up->GetNbinsX() + 2; i++ ) {
      sys.shape_up->SetBinError(i, 0);
    }
    return chi2test > chi2ref;
  };
  removeSysts(f, SysStatus::PruneOther);
}

const std::set<TString> SampleInCategory::getConsideredSysts(const SysType type) const
{
  std::set<TString> res;
  for( auto& statPair : m_systsStatus ) {
    if( statPair.first.first == type ) {
      res.insert(statPair.first.second);
    }
  }
  return res;
}

const std::set<TString> SampleInCategory::getUsedSysts(const SysType type) const
{
  std::set<TString> res;
  for( auto& statPair : m_systsStatus ) {
    if( statPair.first.first == type && statPair.second == SysStatus::Used ) {
      res.insert(statPair.first.second);
    }
  }
  return res;
}

SysStatus SampleInCategory::getSystStatus(const SysKey& key) const
{
  auto it = m_systsStatus.find(key);
  if( it == m_systsStatus.end() ) {
    return SysStatus::NotConsidered;
  }
  return it->second;
}

float SampleInCategory::getMeanNormEffect(const SysKey& key) const
{
  if( key.first != SysType::norm ) {
    std::cerr << "ERROR::SampleInCategory::getMeanNormEffect" << std::endl;
    std::cerr << "Requested systematic " << key.second << " is not of type norm" << std::endl;
    throw;
  }

  auto it = m_systs.find(key);
  if( it == m_systs.end() ) {
    return 0;
  } else {
    auto& sys = it->second;
    float sgn = sys.var_up > 1 ? 1 : -1;
    return sgn * (fabs(sys.var_up - 1) + fabs(sys.var_do - 1)) / 2;
  }
}

double SampleInCategory::getChi2SmoothTest(const SysKey& key, Systematic::Side side) const
{
  auto foundIt = m_systsChi2Results.find(key);

  if( foundIt == m_systsChi2Results.end() ) {
    std::pair<float, float> chi2Result;
    chi2Result.first  = doChi2SmoothTest(key, Systematic::Side::up);
    chi2Result.second = doChi2SmoothTest(key, Systematic::Side::down);
    foundIt           = m_systsChi2Results.emplace(key, std::move(chi2Result)).first;
  }

  return side == Systematic::Side::up ? foundIt->second.first : foundIt->second.second;
}

double SampleInCategory::doChi2SmoothTest(const SysKey& key, Systematic::Side side, const std::string& opts,
                                          bool setErrorsOfSysSmoothedToZero) const
{
  auto it = m_systs.find(key);
  if( it == m_systs.end() )
    return -1.;

  const Systematic& sys    = it->second;
  const TH1*        smooth = side == Systematic::Side::up ? sys.shape_up.get() : sys.shape_do.get();
  const TH1*        orig = side == Systematic::Side::up ? sys.shape_up_unsmoothed.get() : sys.shape_do_unsmoothed.get();
  std::unique_ptr<TH1> clone;

  if( !smooth || !orig )
    return -1.;

  if( setErrorsOfSysSmoothedToZero ) {
    clone.reset((TH1*)smooth->Clone("cloneWithoutErrors"));
    for( int bin = 0; bin < sys.shape_up->GetNbinsX() + 2; ++bin ) {
      clone->SetBinError(bin, 0.);
    }

    smooth = clone.get();
  }

  return orig->Chi2Test(smooth, opts.c_str());
}

TH1* SampleInCategory::getShapeSyst(const SysKey& key, Systematic::Side side, bool getUnsmoothed) const
{
  if( key.first != SysType::shape ) {
    std::cerr << "ERROR::SampleInCategory::getShapeSyst" << std::endl;
    std::cerr << "Requested systematic " << key.second << " is not of type shape" << std::endl;
    throw;
  }
  auto it = m_systs.find(key);
  if( it == m_systs.end() ) {
    return nullptr;
  }
  auto& sys = it->second;
  if( side == Systematic::Side::up )
    return getUnsmoothed ? sys.shape_up_unsmoothed.get() : sys.shape_up.get();
  else
    return getUnsmoothed ? sys.shape_do_unsmoothed.get() : sys.shape_do.get();

  return nullptr;
}

void SampleInCategory::removeSameSignBinsSysts()
{
  std::set<TString> toTreat;
  for( const auto& sysobj : m_systs ) {
    if( sysobj.second.smooth != SysConfig::Smooth::noSmooth ) {
      toTreat.insert(sysobj.second.name);
    }
  }

  for( const auto& sysname : toTreat ) {
    TH1* hup = getFullSystShape(sysname, Systematic::Side::up);
    hup->Divide(m_nomHist.get()); // get the ratio
    TH1* hdo = getFullSystShape(sysname, Systematic::Side::down);
    hdo->Divide(m_nomHist.get()); // get the ratio
    // remove same-sign bins
    for( int i = 1; i < hup->GetNbinsX() + 1; i++ ) {
      if( (hup->GetBinContent(i) - 1) * (hdo->GetBinContent(i) - 1) >= 0 ) {
        hup->SetBinContent(i, 1);
        hdo->SetBinContent(i, 1);
      }
    }
    // then rebuild the syst
    hup->Multiply(m_nomHist.get());
    hdo->Multiply(m_nomHist.get());

    // save unsmoothed histos and smoothing/symmetrisation settings
    std::shared_ptr<TH1>  unsmoothedUp, unsmoothedDo;
    SysConfig::Smooth     smooth     = SysConfig::Smooth::noSmooth;
    SysConfig::Symmetrise symmetrise = SysConfig::Symmetrise::noSym;
    if( hasSyst(Systematic::Type::shape, sysname) ) {
      const Systematic& syst = getSyst(Systematic::Type::shape, sysname);
      smooth                 = syst.smooth;
      symmetrise             = syst.symmetrise;
      unsmoothedUp           = syst.shape_up_unsmoothed;
      unsmoothedDo           = syst.shape_do_unsmoothed;
    }
    // remove the existing syst
    deleteSyst(std::make_pair(SysType::norm, sysname));
    deleteSyst(std::make_pair(SysType::shape, sysname));
    // and add the new one
    addSyst(sysname, Systematic::Side::up, STreat::shape, hup, smooth, symmetrise, unsmoothedUp);
    addSyst(sysname, Systematic::Side::down, STreat::shape, hdo, smooth, symmetrise, unsmoothedDo);
  }
}

void SampleInCategory::clearSystHistos()
{
  for( auto it = m_systs.begin(); it != m_systs.end(); ) {
    Systematic& sys = it->second;
    if( sys.type == SysType::shape ) {
      it = m_systs.erase(it);
    } else {
      ++it;
    }
  }
}
