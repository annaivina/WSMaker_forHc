#include "systematic.hpp"

#include <iostream>

#include <TString.h>

#include "containerhelpers.hpp"
#include "properties.hpp"
#include "sample.hpp"

bool Systematic::operator<(const Systematic& other) const
{
  SysOrdering ordering;
  return ordering(std::make_pair(type, name), std::make_pair(other.type, other.name));
}

bool Systematic::operator==(const Systematic& other) { return ((other.type == type) && (other.name.EqualTo(name))); }

std::pair<TString, Systematic::Side> Systematic::interpretSysName(const TString& name)
{
  Side    side = Side::up;
  TString shortname(name);
  if( name.EndsWith("__1up") ) {
    side      = Side::up;
    shortname = name(0, name.Length() - 5);
  } else if( name.EndsWith("__1down") ) {
    side      = Side::down;
    shortname = name(0, name.Length() - 7);
  }
  // Hacks for now
  else if( name.EndsWith("_ScaleUp") ) {
    side      = Side::up;
    shortname = name(0, name.Length() - 2);
  } else if( name.EndsWith("_ScaleDown") ) {
    side      = Side::down;
    shortname = name(0, name.Length() - 4);
  } else {
    std::cout << "WARNING: Systematic::interpretSysName: " << name
              << " has no __1up/__1down in name - Assuming it's an up variation\n";
  }

  return std::make_pair(shortname, side);
}

void Systematic::merge(const Systematic& other)
{
  if( other.type != type || other.name != name ) {
    std::cerr << "ERROR:  Systematic::merge" << std::endl;
    std::cerr << "Attempt to merge systematic " << name << " " << static_cast<int>(type) << std::endl;
    std::cerr << "With an incompatible " << other.name << " " << static_cast<int>(other.type) << std::endl;
    throw;
  }
  if( other.var_up != 1 ) {
    if( var_up != 1 ) {
      std::cerr << "WARNING:  Systematic::merge" << std::endl;
      std::cerr << "Merge of systematic " << name << " " << static_cast<int>(type)
                << " will overwrite var_up = " << var_up << " with var_up = " << other.var_up << std::endl;
    }
    var_up = other.var_up;
  }
  if( other.var_do != 1 ) {
    if( var_do != 1 ) {
      std::cerr << "WARNING:  Systematic::merge" << std::endl;
      std::cerr << "Merge of systematic " << name << " " << static_cast<int>(type)
                << " will overwrite var_do = " << var_do << " with var_do = " << other.var_do << std::endl;
    }
    var_do = other.var_do;
  }
  if( other.shape_up != nullptr ) {
    if( shape_up != nullptr ) {
      std::cerr << "WARNING:  Systematic::merge" << std::endl;
      std::cerr << "Merge of systematic " << name << " " << static_cast<int>(type)
                << " will overwrite shape_up = " << shape_up << " with shape_up = " << other.shape_up << std::endl;
    }
    shape_up            = other.shape_up;
    shape_up_unsmoothed = other.shape_up_unsmoothed;
  }
  if( other.shape_do != nullptr ) {
    if( shape_do != nullptr ) {
      std::cerr << "WARNING:  Systematic::merge" << std::endl;
      std::cerr << "Merge of systematic " << name << " " << static_cast<int>(type)
                << " will overwrite shape_do = " << shape_do << " with shape_do = " << other.shape_do << std::endl;
    }
    shape_do            = other.shape_do;
    shape_do_unsmoothed = other.shape_do_unsmoothed;
  }
  if( other.init != 0 ) {
    if( init != 0 ) {
      std::cerr << "WARNING:  Systematic::merge" << std::endl;
      std::cerr << "Merge of systematic " << name << " " << static_cast<int>(type) << " will overwrite init = " << init
                << " with init = " << other.init << std::endl;
    }
    init = other.init;
  }
  isConst    = other.isConst;
  smooth     = other.smooth;
  symmetrise = other.symmetrise;
}

void Systematic::print() const
{
  std::cout << "Print systematic:" << std::endl
            << "  - name : " << name << std::endl
            << "  - type : " << static_cast<int>(type) << std::endl;
  if( type == Type::norm || type == Type::flt ) {
    std::cout << "  - var_up : " << var_up << std::endl << "  - var_do : " << var_do << std::endl;
  }
  if( type == Type::flt ) {
    std::cout << "  - init : " << init << std::endl;
    std::cout << "  - isConst : " << isConst << std::endl;
  }
  if( type == Type::shape ) {
    std::cout << "  - has shape_up : " << (shape_up != nullptr) << std::endl
              << "  - has shape_do : " << (shape_do != nullptr) << std::endl;
  }
  if( type == Type::MCstat ) {
    std::cout << "  - has mc_stat_error_absolute_sample : " << (mc_stat_error_absolute_sample != nullptr) << std::endl
              << "  - has mc_stat_error_fractional_shared : " << (mc_stat_error_fractional_shared != nullptr)
              << std::endl;
  }
}

ComplexFunctions::CategoryFunction operator&&(ComplexFunctions::CategoryFunction& a,
                                              ComplexFunctions::CategoryFunction& b)
{
  ComplexFunctions::CategoryFunction res = [a, b](const PropertiesSet& p) { return a(p) && b(p); };
  return res;
}

ComplexFunctions::CategoryFunction operator&&(const PropertiesSet& a, const ComplexFunctions::CategoryFunction& b)
{
  ComplexFunctions::CategoryFunction res = [a, b](const PropertiesSet& p) { return p.match(a) && b(p); };
  return res;
}

ComplexFunctions::CategoryFunction operator&&(const ComplexFunctions::CategoryFunction& a, const PropertiesSet& b)
{
  ComplexFunctions::CategoryFunction res = [a, b](const PropertiesSet& p) { return a(p) && p.match(b); };
  return res;
}

// those are mostly useful for histo systs

SysConfig::SysConfig(Treat t, Smooth sm, Symmetrise sym, std::vector<TString>&& s, std::vector<PropertiesSet>&& c,
                     std::vector<Property>&& d, std::vector<PropertiesSet>&& cd, std::vector<TString>&& sd,
                     DecorrFunction&& fun, float sf) :
    treat(t),
    smooth(sm),
    symmetrise(sym),
    scaleFactor(sf),
    sampleNames(std::move(s)),
    categories(std::move(c)),
    decorrelations(std::move(d)),
    cplxDecorrelations(std::move(cd)),
    sampleDecorrelations(std::move(sd)),
    freeDecorrelation(std::move(fun)),
    decorrEverywhere(false),
    userSmoothing(nullptr)
{}

SysConfig::SysConfig(Treat t, Smooth sm, Symmetrise sym, const TString& s, std::vector<PropertiesSet>&& c,
                     std::vector<Property>&& d, std::vector<PropertiesSet>&& cd, std::vector<TString>&& sd,
                     DecorrFunction&& fun, float sf) :
    treat(t),
    smooth(sm),
    symmetrise(sym),
    scaleFactor(sf),
    sampleNames(),
    categories(std::move(c)),
    decorrelations(std::move(d)),
    cplxDecorrelations(std::move(cd)),
    sampleDecorrelations(std::move(sd)),
    freeDecorrelation(std::move(fun)),
    decorrEverywhere(false),
    userSmoothing(nullptr)
{
  if( !s.IsNull() ) {
    sampleNames.push_back(s);
  }
}

SysConfig::SysConfig(Treat t, const SmoothingFunction& smFun, Symmetrise sym, std::vector<TString>&& s,
                     std::vector<PropertiesSet>&& c, std::vector<Property>&& d, std::vector<PropertiesSet>&& cd,
                     std::vector<TString>&& sd, DecorrFunction&& fun, float sf) :
    treat(t),
    smooth(Smooth::smoothUserDefined),
    symmetrise(sym),
    scaleFactor(sf),
    sampleNames(std::move(s)),
    categories(std::move(c)),
    decorrelations(std::move(d)),
    cplxDecorrelations(std::move(cd)),
    sampleDecorrelations(std::move(sd)),
    freeDecorrelation(std::move(fun)),
    decorrEverywhere(false),
    userSmoothing(smFun)
{}

SysConfig::SysConfig(Treat t, Smooth sm, const SymFunction& symFun, std::vector<TString>&& s,
                     std::vector<PropertiesSet>&& c, std::vector<Property>&& d, std::vector<PropertiesSet>&& cd,
                     std::vector<TString>&& sd, DecorrFunction&& fun, float sf) :
    treat(t),
    smooth(sm),
    symmetrise(Symmetrise::symmetriseUserDefined),
    scaleFactor(sf),
    sampleNames(std::move(s)),
    categories(std::move(c)),
    decorrelations(std::move(d)),
    cplxDecorrelations(std::move(cd)),
    sampleDecorrelations(std::move(sd)),
    freeDecorrelation(std::move(fun)),
    decorrEverywhere(false),
    userSmoothing(nullptr),
    userSym(symFun)
{}

SysConfig::SysConfig(Treat t, const SmoothingFunction& smFun, const SymFunction& symFun, std::vector<TString>&& s,
                     std::vector<PropertiesSet>&& c, std::vector<Property>&& d, std::vector<PropertiesSet>&& cd,
                     std::vector<TString>&& sd, DecorrFunction&& fun, float sf) :
    treat(t),
    smooth(Smooth::smoothUserDefined),
    symmetrise(Symmetrise::symmetriseUserDefined),
    scaleFactor(sf),
    sampleNames(std::move(s)),
    categories(std::move(c)),
    decorrelations(std::move(d)),
    cplxDecorrelations(std::move(cd)),
    sampleDecorrelations(std::move(sd)),
    freeDecorrelation(std::move(fun)),
    decorrEverywhere(false),
    userSmoothing(smFun),
    userSym(symFun)
{}

SysConfig::SysConfig(Treat t, const SmoothingFunction& smFun, Symmetrise sym, const TString& s,
                     std::vector<PropertiesSet>&& c, std::vector<Property>&& d, std::vector<PropertiesSet>&& cd,
                     std::vector<TString>&& sd, DecorrFunction&& fun, float sf) :
    treat(t),
    smooth(Smooth::smoothUserDefined),
    symmetrise(sym),
    scaleFactor(sf),
    sampleNames(),
    categories(std::move(c)),
    decorrelations(std::move(d)),
    cplxDecorrelations(std::move(cd)),
    sampleDecorrelations(std::move(sd)),
    freeDecorrelation(std::move(fun)),
    decorrEverywhere(false),
    userSmoothing(smFun)
{
  if( !s.IsNull() ) {
    sampleNames.push_back(s);
  }
}

// shorthand to decorrelate years
SysConfig::SysConfig(Treat t, Smooth sm, Symmetrise sym, bool corr_years, std::vector<TString>&& s,
                     std::vector<PropertiesSet>&& c, std::vector<TString>&& sd, DecorrFunction&& fun, float sf) :
    treat(t),
    smooth(sm),
    symmetrise(sym),
    scaleFactor(sf),
    sampleNames(std::move(s)),
    categories(std::move(c)),
    decorrelations(),
    cplxDecorrelations(),
    sampleDecorrelations(std::move(sd)),
    freeDecorrelation(std::move(fun)),
    decorrEverywhere(false)
{
  if( !corr_years )
    decorrelations.push_back(Property::year);
}

// those are mostly useful for user-defined systs

SysConfig::SysConfig(std::vector<TString>&& s, std::vector<PropertiesSet>&& c, std::vector<Property>&& d,
                     std::vector<PropertiesSet>&& cd, std::vector<TString>&& sd, DecorrFunction&& fun, float sf) :
    treat(Treat::skip),
    smooth(Smooth::noSmooth),
    symmetrise(Symmetrise::noSym),
    scaleFactor(sf),
    sampleNames(std::move(s)),
    categories(std::move(c)),
    decorrelations(std::move(d)),
    cplxDecorrelations(std::move(cd)),
    sampleDecorrelations(std::move(sd)),
    freeDecorrelation(std::move(fun)),
    decorrEverywhere(false),
    userSmoothing(nullptr)
{}

SysConfig::SysConfig(const TString& s, std::vector<PropertiesSet>&& c, std::vector<Property>&& d,
                     std::vector<PropertiesSet>&& cd, std::vector<TString>&& sd, DecorrFunction&& fun, float sf) :
    treat(Treat::skip),
    smooth(Smooth::noSmooth),
    symmetrise(Symmetrise::noSym),
    scaleFactor(sf),
    sampleNames({s}),
    categories(std::move(c)),
    decorrelations(std::move(d)),
    cplxDecorrelations(std::move(cd)),
    sampleDecorrelations(std::move(sd)),
    freeDecorrelation(std::move(fun)),
    decorrEverywhere(false),
    userSmoothing(nullptr)
{}

SysConfig& SysConfig::applyTo(const TString& s)
{
  sampleNames.push_back(s);
  return *this;
}

SysConfig& SysConfig::applyTo(const std::vector<TString>& vs)
{
  Utils::appendToVec(sampleNames, vs);
  return *this;
}

SysConfig& SysConfig::applyIn(const PropertiesSet& c)
{
  categories.push_back(c);
  return *this;
}

SysConfig& SysConfig::applyIn(const std::vector<PropertiesSet>& vc)
{
  Utils::appendToVec(categories, vc);
  return *this;
}

SysConfig& SysConfig::applyIn(const ComplexFunctions::CategoryFunction& func)
{
  cplxCategories.push_back(func);
  return *this;
}

SysConfig& SysConfig::applyIn(const ComplexFunctions::CategoryFunction&& func)
{
  cplxCategories.push_back(std::move(func));
  return *this;
}

SysConfig& SysConfig::applyIn(const std::vector<ComplexFunctions::CategoryFunction>& vfunc)
{
  Utils::appendToVec(cplxCategories, vfunc);
  return *this;
}

SysConfig& SysConfig::decorr(const Property& d)
{
  decorrelations.push_back(d);
  return *this;
}

SysConfig& SysConfig::decorr(const std::vector<Property>& d)
{
  Utils::appendToVec(decorrelations, d);
  return *this;
}

SysConfig& SysConfig::decorrIn(const PropertiesSet& cd)
{
  cplxDecorrelations.push_back(cd);
  return *this;
}

SysConfig& SysConfig::decorrIn(const std::vector<PropertiesSet>& cd)
{
  Utils::appendToVec(cplxDecorrelations, cd);
  return *this;
}

SysConfig& SysConfig::decorrTo(const TString& sd)
{
  sampleDecorrelations.push_back(sd);
  return *this;
}

SysConfig& SysConfig::decorrTo(const std::vector<TString>& sd)
{
  Utils::appendToVec(sampleDecorrelations, sd);
  return *this;
}

SysConfig& SysConfig::decorrFun(const DecorrFunction& fun)
{
  freeDecorrelation = fun;
  return *this;
}

SysConfig& SysConfig::normalize(const SysNormRegionsConfig& normConf)
{
  normalizeRegionsConfig.push_back(normConf);
  return *this;
}

SysConfig& SysConfig::normalize(const std::vector<SysNormRegionsConfig>& normConf)
{
  for( auto& n : normConf ) {
    normalizeRegionsConfig.push_back(n);
  }
  return *this;
}

SysConfig& SysConfig::scale(float sf)
{
  scaleFactor = sf;
  return *this;
}

TString SysConfig::getDecorrelationTag(const PropertiesSet& pset, const Sample& s) const
{
  TString res("");
  if( !decorrEverywhere ) {
    // simple decorrelation rules, if defined
    for( const auto& p : decorrelations ) {
      if( pset.hasProperty(p) ) {
        res += pset.getPropertyTag(p);
      }
    }
    // more complex decorrelation rules, if defined
    for( const auto& psetDecorr : cplxDecorrelations ) {
      if( pset.match(psetDecorr) ) {
        res += psetDecorr.getPropertiesTag();
      }
    }
    // free decorrelation rules, if defined
    if( freeDecorrelation != nullptr ) {
      res += freeDecorrelation(pset, s);
    }
  } else {
    res += pset.getPropertiesTag();
  }
  for( const auto& sd : sampleDecorrelations ) {
    if( s.hasKW(sd) ) {
      res += "_" + sd;
    }
  }

  return res;
}

SysConfig::Smooth SysConfig::getSmoothingAlg(const PropertiesSet& pset, const Sample& s) const
{
  if( smooth != Smooth::smoothUserDefined ) {
    return smooth;
  }
  return userSmoothing(pset, s);
}

SysConfig::Symmetrise SysConfig::getSymAlg(const PropertiesSet& pset, const Sample& s) const
{
  if( symmetrise != Symmetrise::symmetriseUserDefined ) {
    return symmetrise;
  }
  return userSym(pset, s);
}

/// Full constructor
SysNormRegionsConfig::SysNormRegionsConfig(std::vector<TString>&& s, std::vector<PropertiesSet>&& rcat,
                                           std::vector<PropertiesSet>&& acat, std::vector<Property>&& d,
                                           std::vector<PropertiesSet>&& cd) :
    sampleNames(std::move(s)),
    referenceCategories(std::move(rcat)),
    applicationCategories(std::move(acat)),
    decorrelations(std::move(d)),
    cplxDecorrelations(std::move(cd)),
    decorrSamples(false)
{}

/// Full constructor for one single sample or keyword
SysNormRegionsConfig::SysNormRegionsConfig(const TString& s, std::vector<PropertiesSet>&& rcat,
                                           std::vector<PropertiesSet>&& acat, std::vector<Property>&& d,
                                           std::vector<PropertiesSet>&& cd) :
    sampleNames(),
    referenceCategories(std::move(rcat)),
    applicationCategories(std::move(acat)),
    decorrelations(std::move(d)),
    cplxDecorrelations(std::move(cd)),
    decorrSamples(false)
{
  if( !s.IsNull() ) {
    sampleNames.push_back(s);
  }
}

/// shortcut for one single sample and one single reference normalization region
SysNormRegionsConfig::SysNormRegionsConfig(const TString& s, PropertiesSet& rcat, std::vector<PropertiesSet>&& acat,
                                           std::vector<Property>&& d, std::vector<PropertiesSet>&& cd) :
    sampleNames(),
    referenceCategories(),
    applicationCategories(std::move(acat)),
    decorrelations(std::move(d)),
    cplxDecorrelations(std::move(cd)),
    decorrSamples(false)
{
  if( !s.IsNull() ) {
    sampleNames.push_back(s);
  }

  referenceCategories.push_back(rcat);
}

/// Full constructors with complex CategoryFunctions
SysNormRegionsConfig::SysNormRegionsConfig(std::vector<TString>&&                                  s,
                                           const std::vector<ComplexFunctions::CategoryFunction>&& rcat,
                                           const std::vector<ComplexFunctions::CategoryFunction>&& acat,
                                           std::vector<Property>&& d, std::vector<PropertiesSet>&& cd) :
    sampleNames(std::move(s)),
    cplxReferenceCategories(std::move(rcat)),
    cplxApplicationCategories(std::move(acat)),
    decorrelations(std::move(d)),
    cplxDecorrelations(std::move(cd)),
    decorrSamples(false)
{}

SysNormRegionsConfig::SysNormRegionsConfig(std::vector<TString>&&                                 s,
                                           const std::vector<ComplexFunctions::CategoryFunction>& rcat,
                                           const std::vector<ComplexFunctions::CategoryFunction>& acat,
                                           std::vector<Property>&& d, std::vector<PropertiesSet>&& cd) :
    sampleNames(std::move(s)),
    cplxReferenceCategories(),
    cplxApplicationCategories(),
    decorrelations(std::move(d)),
    cplxDecorrelations(std::move(cd)),
    decorrSamples(false)
{
  Utils::appendToVec(cplxReferenceCategories, rcat);
  Utils::appendToVec(cplxApplicationCategories, acat);
}

SysNormRegionsConfig::SysNormRegionsConfig(const TString&                                          s,
                                           const std::vector<ComplexFunctions::CategoryFunction>&& rcat,
                                           const std::vector<ComplexFunctions::CategoryFunction>&& acat,
                                           std::vector<Property>&& d, std::vector<PropertiesSet>&& cd) :
    sampleNames(),
    cplxReferenceCategories(std::move(rcat)),
    cplxApplicationCategories(std::move(acat)),
    decorrelations(std::move(d)),
    cplxDecorrelations(std::move(cd)),
    decorrSamples(false)
{
  if( !s.IsNull() ) {
    sampleNames.push_back(s);
  }
}

SysNormRegionsConfig::SysNormRegionsConfig(const TString&                                         s,
                                           const std::vector<ComplexFunctions::CategoryFunction>& rcat,
                                           const std::vector<ComplexFunctions::CategoryFunction>& acat,
                                           std::vector<Property>&& d, std::vector<PropertiesSet>&& cd) :
    sampleNames(),
    cplxReferenceCategories(),
    cplxApplicationCategories(),
    decorrelations(std::move(d)),
    cplxDecorrelations(std::move(cd)),
    decorrSamples(false)
{
  if( !s.IsNull() ) {
    sampleNames.push_back(s);
  }
  Utils::appendToVec(cplxReferenceCategories, rcat);
  Utils::appendToVec(cplxApplicationCategories, acat);
}

SysNormRegionsConfig::SysNormRegionsConfig(std::vector<TString>&& s, const ComplexFunctions::CategoryFunction& rcat,
                                           const ComplexFunctions::CategoryFunction& acat, std::vector<Property>&& d,
                                           std::vector<PropertiesSet>&& cd) :
    sampleNames(std::move(s)),
    cplxReferenceCategories(),
    cplxApplicationCategories(),
    decorrelations(std::move(d)),
    cplxDecorrelations(std::move(cd)),
    decorrSamples(false)
{
  cplxReferenceCategories.push_back(rcat);
  cplxApplicationCategories.push_back(acat);
}

SysNormRegionsConfig::SysNormRegionsConfig(std::vector<TString>&& s, const ComplexFunctions::CategoryFunction&& rcat,
                                           const ComplexFunctions::CategoryFunction&& acat, std::vector<Property>&& d,
                                           std::vector<PropertiesSet>&& cd) :
    sampleNames(std::move(s)),
    cplxReferenceCategories(),
    cplxApplicationCategories(),
    decorrelations(std::move(d)),
    cplxDecorrelations(std::move(cd)),
    decorrSamples(false)
{
  cplxReferenceCategories.push_back(std::move(rcat));
  cplxApplicationCategories.push_back(std::move(acat));
}

/// @}

/// @}

// Also import getDecorrelationTag, very similar to SysConfig. Will be used in ComputeNormalizationFactors
// to properly classify the regions / samples in the groups desired by the user, and compute correctly
// the factors, then assign them to the correct regions / samples.

TString SysNormRegionsConfig::getDecorrelationTag(const PropertiesSet& pset, const Sample& s) const
{
  TString res("");
  if( decorrelations.size() != 0 ) {
    // simple decorrelation rules, if defined
    for( const auto& p : decorrelations ) {
      if( pset.hasProperty(p) ) {
        res += pset.getPropertyTag(p);
      }
    }
    // more complex decorrelation rules, if defined
    for( const auto& psetDecorr : cplxDecorrelations ) {
      if( pset.match(psetDecorr) ) {
        res += psetDecorr.getPropertiesTag();
      }
    }
  } else {
    res += pset.getPropertiesTag();
  }

  if( decorrSamples ) {
    res += "_" + s.name();
  }

  return res;
}

SysNormRegionsConfig& SysNormRegionsConfig::decorrelateSamples(bool ds)
{
  decorrSamples = ds;
  return *this;
}

SysNormRegionsConfig& SysNormRegionsConfig::decorr(const Property& d)
{
  decorrelations.push_back(d);
  return *this;
}

SysNormRegionsConfig& SysNormRegionsConfig::decorr(const std::vector<Property>& d)
{
  Utils::appendToVec(decorrelations, d);
  return *this;
}

SysNormRegionsConfig& SysNormRegionsConfig::decorrIn(const PropertiesSet& cd)
{
  cplxDecorrelations.push_back(cd);
  return *this;
}

NormIntegrals::NormIntegrals(float n, float u, float d) : nom(n), up(u), down(d) {}

NormIntegrals NormIntegrals::operator=(const NormIntegrals& other)
{
  if( this != &other ) { // self-assignment check expected
    nom  = other.nom;
    up   = other.up;
    down = other.down;
  }
  return *this;
}

NormIntegrals NormIntegrals::operator+(NormIntegrals& other)
{
  NormIntegrals ni;
  ni.nom  = nom + other.nom;
  ni.up   = up + other.up;
  ni.down = down + other.down;
  return ni;
}

void NormIntegrals::print() { std::cout << "nom: " << nom << " up " << up << " down " << down << std::endl; }
