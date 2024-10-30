#include "systematiclistsbuilder.hpp"

#include <utility>

#include <TString.h>
#include <type_traits>

#include "properties.hpp"

SystematicListsBuilder::SystematicListsBuilder(
    const Configuration& conf, std::vector<std::pair<Systematic, SysConfig>>& userSysts,
    std::vector<std::pair<Systematic, SysConfig>>& pois, std::vector<Systematic32>& r32ratios,
    std::unordered_map<TString, SysConfig>& histoSysts, std::unordered_map<TString, TString>& renameHistoSysts,
    std::vector<TString>& constNormFacts, std::vector<SysConfig>& MCStatSysts) :
    m_config(conf),
    m_userSysts(userSysts),
    m_pois(pois),
    m_32ratios(r32ratios),
    m_histoSysts(histoSysts),
    m_renameHistoSysts(renameHistoSysts),
    m_constNormFacts(constNormFacts),
    m_MCStatSysts(MCStatSysts)
{}

// most generic one

void SystematicListsBuilder::applySys(Systematic&& sys, const SysConfig& conf)
{
  m_userSysts.emplace_back(std::make_pair(std::move(sys), conf));
}

// basic ones

void SystematicListsBuilder::normSys(const TString& name, float min, float max, const SysConfig& conf)
{
  m_userSysts.emplace_back(std::make_pair(Systematic(name, min, max), conf));
}

void SystematicListsBuilder::normSys(const TString& name, float size, const SysConfig& conf)
{
  m_userSysts.emplace_back(std::make_pair(Systematic(name, 1 - size, 1 + size), conf));
}

void SystematicListsBuilder::normFact(const TString& name, const SysConfig& conf, float init, float down, float up,
                                      bool isConst)
{
  TString sysname = "ATLAS_norm_" + name;
  m_userSysts.emplace_back(std::make_pair(Systematic(sysname, init, down, up, isConst), conf));
}

void SystematicListsBuilder::shapeFact(const TString& name, const SysConfig& conf)
{
  TString sysname = "ATLAS_shape_" + name;
  m_userSysts.emplace_back(std::make_pair(Systematic(sysname), conf));
}

void SystematicListsBuilder::addPOI(const TString& name, const SysConfig& conf, float init, float down, float up)
{
  m_pois.emplace_back(std::make_pair(Systematic(name, init, down, up, false), conf));
}

void SystematicListsBuilder::ratio32(const TString& name, float size, const SysConfig& conf)
{
  m_32ratios.emplace_back(Systematic32{name, size, conf});
}

void SystematicListsBuilder::sampleNormSys(const TString& name, float size)
{
  normSys("Sys" + name + "Norm", size, {name});
}

void SystematicListsBuilder::sampleNormSys(const TString& name, float min, float max)
{
  normSys("Sys" + name + "Norm", min, max, {name});
}

void SystematicListsBuilder::sampleNorm3JSys(const TString& name, float size)
{
  normSys("Sys" + name + "Norm", size, {name, {{Property::nJet, 3}}, {Property::nJet}});
}

SysConfig& SystematicListsBuilder::MCStatSys()
{
  SysConfig sys(SysConfig::Treat::shape, SysConfig::Smooth::noSmooth, SysConfig::Symmetrise::noSym);
  sys.decorrEverywhere = true;
  m_MCStatSysts.emplace_back(sys);
  return m_MCStatSysts.back();
}
