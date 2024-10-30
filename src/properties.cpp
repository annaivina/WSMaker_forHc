#include "properties.hpp"

#include <algorithm>
#include <iostream>
#include <iterator>
#include <sstream>
#include <utility>
#include <variant>

#include <TString.h>

#include "containerhelpers.hpp"
#include "utility.hpp"

const std::unordered_map<Property, TString>
    Properties::names({{Property::year, "Y"},          {Property::nLep, "L"},
                       {Property::nJet, "J"},          {Property::nFatJet, "Fat"},
                       {Property::nTag, "T"},          {Property::tagType, "TType"},
                       {Property::bin, "B"},           {Property::lepFlav, "Flv"},
                       {Property::lepSign, "Sgn"},     {Property::type, "isMVA"},
                       {Property::dist, "dist"},       {Property::spec, "Spc"},
                       {Property::highVhf, "Vhf"},     {Property::binMin, "BMin"},
                       {Property::binMax, "BMax"},     {Property::descr, "D"},
                       {Property::incTag, "incTag"},   {Property::incJet, "incJet"},
                       {Property::incFat, "incFat"},   {Property::incAddTag, "incAddTag"},
                       {Property::nAddTag, "nAddTag"}, {Property::nPh, "Ph"},
		       {Property::ntau, "ntau"},       {Property::inctau, "inctau"}, //GDG
                       {Property::LTT, "LTT"}});

const std::unordered_map<TString, Property>
    Properties::props_from_names(Utils::reverseMap<Property, TString>(Properties::names));

PropertiesSet::PropertiesSet(TString psetString) : properties()
{
  // clean a little bit our input
  psetString.Remove(TString::kBoth, '_');

  // tokenize
  auto tokens = Utils::splitString(psetString, '_');

  // Now the fancy part. Given some property names can be substrings of others, we need to be greedy
  // and start by attempting to match everything, then decreasing our ambitions
  for( const auto& t : tokens ) {
    size_t subStringLen = t.Length();
    for( ; subStringLen > 0; --subStringLen ) {
      // look for this substring in the list of Property names
      auto found = Properties::props_from_names.find(t(0, subStringLen));

      if( found != Properties::props_from_names.end() ) {
        // if we found something, then we have something matched to a property.
        // now let's validate the content
        TString stringValue = t(subStringLen, t.Length() - subStringLen);
        // is it an int ?
        if( stringValue.IsDigit() ) {
          properties[found->second] = stringValue.Atoi();
        } else { // use it as a string
          properties[found->second] = stringValue;
        }
        // we are happy, now no need to continue this inner loop
        break;
      }
    }
    // shout when no matching property was found. The string is probably ill-formed
    if( subStringLen == 0 ) {
      std::cout << "ERROR:   PropertiesSet::PropertiesSet(TString)\n";
      std::cout << "The token " << t << " could not be matched with any valid Property !\n";
      std::cout << "Please check your string " << psetString << std::endl;
      throw;
    }
  }
}

bool PropertiesSet::hasProperty(const Property p) const { return properties.count(p); }

int PropertiesSet::getIntProp(const Property p) const
{
  const auto& pos = properties.find(p);
  if( pos != properties.end() && std::holds_alternative<int>(pos->second) ) {
    return std::get<int>(pos->second);
  }
  return -1;
}

TString PropertiesSet::getStringProp(const Property p) const
{
  const auto& pos = properties.find(p);
  if( pos != properties.end() && std::holds_alternative<TString>(pos->second) ) {
    return std::get<TString>(pos->second);
  }
  return "";
}

int PropertiesSet::requestIntProp(const Property p) const { return std::get<int>(properties.at(p)); }

TString PropertiesSet::requestStringProp(const Property p) const { return std::get<TString>(properties.at(p)); }

void PropertiesSet::setIntProp(Property p, int i) { properties[p] = i; }

void PropertiesSet::setStringProp(Property p, const TString& s) { properties[p] = s; }

void PropertiesSet::setProp(Property p, const prop_value v) { properties[p] = v; }

bool PropertiesSet::match(const PropertiesSet& pset) const
{
  // check if all defined props are present and have same value
  bool res = std::all_of(std::begin(pset.properties), std::end(pset.properties),
                         [this](const std::pair<Property, prop_value>& p) {
                           return this->hasProperty(p.first) && (this->properties).at(p.first) == p.second;
                         });

  return res;
}

void PropertiesSet::merge(const PropertiesSet& other)
{
  for( const auto& p : other.properties )
    properties[p.first] = p.second;
}

void PropertiesSet::print() const
{
  std::cout << "\nPrinting properties:\n" << std::endl;
  for( const auto& p : properties ) {
    std::cout << "    - " << Properties::names.at(p.first) << " = ";
    std::visit([](auto&& arg) { std::cout << arg << '\n'; }, p.second);
  }
  std::cout << std::endl;
}

struct PropPrinter {
  std::stringstream& m_ss;
  PropPrinter(std::stringstream& ss) : m_ss(ss) {}
  void operator()(int i) { m_ss << i; }
  void operator()(TString s)
  {
    s.ReplaceAll("_", "");
    m_ss << s;
  }
};

TString PropertiesSet::getPropertyTag(const Property p) const
{
  const auto& pos = properties.find(p);
  if( pos == properties.end() ) {
    std::cout << "ERROR:   PropertiesSet::printProperty\n";
    std::cout << "Property " << Properties::names.at(p) << " does not exist here" << std::endl;
    throw;
  }
  std::stringstream ss;
  ss << "_" << Properties::names.at(pos->first);
  std::visit(PropPrinter(ss), pos->second);

  return ss.str().c_str();
}

TString PropertiesSet::getPropertiesTag() const
{
  std::stringstream ss;
  for( const auto& p : properties ) {
    ss << "_" << Properties::names.at(p.first);
    std::visit(PropPrinter(ss), p.second);
  }
  return ss.str().c_str();
}

PropertiesSet PropertiesSet::copyExcept(const Property p, prop_value i) const
{
  PropertiesSet pset(*this);
  pset[p] = i;
  return pset;
}
