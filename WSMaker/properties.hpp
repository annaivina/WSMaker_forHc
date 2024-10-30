#ifndef properties_hpp
#define properties_hpp

#include <cstddef>
#include <initializer_list>
#include <unordered_map>
#include <variant>

#include <TString.h>

/**
 * @file properties.hpp
 * @brief Description of the @c Properties and @c PropertiesSet
 *
 * @c Property and @c PropertiesSet are the basic blocks to describe the
 * analyses categories. Using this logic allows to easily refer to several
 * regions at once using common properties, e.g all 1-lepton 2-jet regions.
 * This is used super intensively to assign systematics to specific regions,
 * to work out the decorrelations of systematics based on the categories they
 * are in.
 */

/**
 * @brief Class/namespace to list the properties that describe the analysis regions
 *
 * Regions of the analysis are described by set of properties.
 * This class simply holds all the existing properties and their names.
 * Properties are typically the number of jets, of leptons, of tagged jets,
 * the pTV bin, the data-taking year, etc...
 * It should be extended if needed
 *
 */
class Properties {
 public:
  /// The list of existing properties
  enum class Property : std::int8_t {
    year,      ///< Analysis year
    nLep,      ///< Number of leptons
    ntau, ///< Number of taus GDG
    inctau, //incl number for taus
    spec,      ///< Special things. topemucr, topcr...
    nJet,      ///< Number of jets
    nFatJet,   ///< Number of fat jets
    nTag,      ///< Number of b-tags
    nAddTag,   ///< Number of b-tags in additional jets
    tagType,   /**< Type of b-tag "" for inclusive, @ ll, @c mm, @c tt,
                 or @c xx @c == @c mm @c + @c tt */
    bin,       /**< @c pTV bin. 0: 0-90 for CUT or 0-120 for MVA, 1:90-120 or 100-120
                 for 0 lepton, 2: 120-160 for CUT or >120 for MVA,
                 3: 160-200, 4: >200 */
    binMin,    ///< min of @c pTV bin.
    binMax,    ///< max of @c pTV bin.
    lepFlav,   ///< 0: mu, 1: e
    lepSign,   ///< 0: neg, 1: pos
    type,      ///< 0: CUT, 1: MVA
    dist,      ///< Distribution (mjj, mva, ...)
    highVhf,   ///< low/high cut on Vhf BDT
    descr,     ///< description of the region
    incTag,    ///< Is inclusive in number of tags
    incJet,    ///< Is inclusive in number of jets
    incFat,    ///< Is inclusive in number of fat jets
    incAddTag, ///< Is inclusive in number of additional b-tagged track jets
    nPh,       ///< Number of photons
    LTT        ///< Flag for Lepton+Tau trigger for TauLH analysis
  };

  /// Map holding the names (as @c TString) of the properties
  static const std::unordered_map<Property, TString> names;

  /// Reverse map to get properties from their names
  static const std::unordered_map<TString, Property> props_from_names;
};

using Property = Properties::Property;

// necessary to use std::unordered_*<Property>
namespace std {
  /// Define hash<Property> so we can use properties in unordered containers
  template <> struct hash<Property> {
    std::size_t operator()(Property const& s) const { return std::hash<int>()(static_cast<int>(s)); }
  };
} // namespace std

using int_prop_map    = std::unordered_map<Property, int>;
using string_prop_map = std::unordered_map<Property, TString>;
using prop_map        = std::unordered_map<Property, std::variant<int, TString>>;
using prop_value      = std::variant<int, TString>;

/**
 * @brief A set of properties
 *
 * A couple of maps of properties associated with their values, either @c int or @c TString.
 * A @c PropertiesSet is typically associated with each analysis region (@c Category) to
 * describe it uniquely.
 * A @c PropertiesSet can hold a limited set of properties, which can be then tested for
 * matches with the categories. This is the basic mechanism used with @c SysConfig to
 * assign systematics only in certain regions, and decorrelate systematics in some regions.
 *
 */
struct PropertiesSet {

  /// Map if properties
  prop_map properties;

  /**
   * @brief Constructor from map
   *
   * Basic constructor from existing maps *that are moved*
   * Use-case is "declarative" construction of @c PropertiesSet as in
   * @c SystematicHandler. Example:
   *
   *     { {nTag, 2}, {nJet, 3}, {dist, "mva"}, {spec, "topcr"} }
   *
   * @param props A map of @c Property associated with @c int or @c TString values
   */
  PropertiesSet(prop_map&& props) : properties(std::move(props)) {}

  /**
   * @brief Constructor from initializer_list
   *
   * Basic constructor from an initilizer list
   * Use-case is "declarative" construction of containers of @c PropertiesSet as in
   * @c SystematicHandler. Example:
   *
   *  std::vector<PropertiesSet> propertiessets = {
   *     { {nTag, 2}, {nJet, 2}, {dist, "mva"}, {spec, "topcr"} },
   *     { {nTag, 2}, {nJet, 3}, {dist, "mva"}, {spec, "topcr"} }
   *  };
   *
   * @param props An initilizer_list of maps of @c Property associated with @c int or @c TString values
   */
  PropertiesSet(std::initializer_list<prop_map::value_type> props) : properties(props) {}

  /**
   * @brief Constructor from maps
   *
   * Basic constructor from existing maps *that are moved*
   * Use-case is "declarative" construction of @c PropertiesSet as in
   * @c SystematicHandler. Example:
   *
   *     { { {nTag, 2}, {nJet, 3} }, { {dist, "mva"}, {spec, "topcr"} } }
   *
   * @param intProps A map of @c Property associated with @c int values
   * @param stringProps A map of @c Property associated with @c TString values
   */
  [[deprecated("Please use the new interface PropertiesSet(prop_map&&) which takes int and TString "
               "indifferentially")]] PropertiesSet(int_prop_map&& intProps, string_prop_map&& stringProps) :
      properties()
  {
    for( auto& p : intProps ) {
      properties[p.first] = p.second;
    }
    for( auto& p : stringProps ) {
      properties[p.first] = p.second;
    }
  }

  /**
   * @brief Constructor for simple case of 1 integer or TString property
   *
   * In many cases e.g in @c SystematicHandler we need a simple PropertiesSet with
   * only 1 @c Property. The constructor is to simplify this common case. Example:
   *
   *     {nJet, 2}
   *
   * @param p	The @c Property
   * @param val	Its value
   */
  PropertiesSet(const Property p, const prop_value& val) : properties() { properties[p] = val; }

  /**
   * @brief Constructor that parses a string to create a @c pset
   *
   * The string is expected to be of the form
   * PNamePValue_PName2PValue2_..._PNameNPValueN
   *
   * It is parsed using @c props_from_names
   *
   * The constructor throws if an invalid token is detected
   *
   * @param psetString the string to be parsed to create the PropertiesSet
   */
  PropertiesSet(TString psetString);

  /// Default empty constructor
  PropertiesSet() = default;

  /// Default copy constructor
  PropertiesSet(const PropertiesSet&) = default;

  /// Default move constructor
  PropertiesSet(PropertiesSet&&) = default;

  /// Default destructor
  ~PropertiesSet() = default;

  PropertiesSet& operator=(const PropertiesSet&) = default;

  /**
   * @brief Copy the PropertiesSet with the exception of 1 property
   *
   * Copy @c this PropertiesSet into a new one, with the exception of 1 @c Property,
   * whose value is changed.
   * Typical use is to find the 3jet region corresponding to a given 2jet one.
   *
   * @param p	The @c Property that changes
   * @param i The new value of the property
   * @return The copy of the @c PropertiesSet
   */
  PropertiesSet copyExcept(const Property p, prop_value i) const;

  /**
   * @brief Check for existence of a @c Property
   *
   * Check if a given @c Property has been defined in the current @c PropertiesSet
   *
   * @param p	The @c Property to check
   * @return @c true if the @c Property has been defined. @c false otherwise.
   */
  bool hasProperty(const Property p) const;

  /// @name Accessors that returns a default value if property is not present
  /// @{

  /**
   * @brief Access an integer @c Property
   *
   * Get the value of an integer @c Property if it has been defined.
   * Returns -1 if the @c Property is not in the PropertiesSet or has been set as a
   * string @c Property
   *
   * @param p The @c Property to access
   * @return The value of @c p if @c p is in the @c PropertiesSet and has been set has an
   * integer @c Property. -1 otherwise.
   */
  int getIntProp(const Property p) const;

  /**
   * @brief Access a string @c Property
   *
   * Get the value of a string @c Property if it has been defined.
   * Returns -1 if the @c Property is not in the PropertiesSet or has been set as a
   * integer @c Property
   *
   * @param p The @c Property to access
   * @return The value of @c p if @c p is in the @c PropertiesSet and has been set has a
   * string @c Property. "" otherwise.
   */
  TString getStringProp(const Property p) const;

  /// Alias to @c getIntProp(p)
  inline int operator[](const Property p) const { return getIntProp(p); }

  /// Alias to @c getStringProp(p)
  inline TString operator()(const Property p) const { return getStringProp(p); }

  /// @}

  /// @name Accessors that throw an exception if property is not present
  /// @{

  /**
   * @brief Access an integer @c Property
   *
   * Get the value of an integer @c Property if it has been defined.
   * Throw an exception if the @c Property is not in the PropertiesSet or has been set as a
   * string @c Property
   *
   * @param p The @c Property to access
   * @return The value of @c p if @c p is in the @c PropertiesSet and has been set has an
   * integer @c Property. Throws otherwise.
   */
  int requestIntProp(const Property p) const;

  /**
   * @brief Access a string @c Property
   *
   * Get the value of a string @c Property if it has been defined.
   * Throw an exception if the @c Property is not in the PropertiesSet or has been set as a
   * int @c Property
   *
   * @param p The @c Property to access
   * @return The value of @c p if @c p is in the @c PropertiesSet and has been set has a
   * string @c Property. Throws otherwise.
   */
  TString requestStringProp(const Property p) const;

  /// @}

  /// @name Setters
  /// @{

  /**
   * @brief Set the value of an integer @c Property
   *
   * @param p	The @c Property to set
   * @param i	The value of @c p
   */
  [[deprecated]] void setIntProp(Property p, int i);

  /**
   * @brief Set the value of a string @c Property
   *
   * @param p	The @c Property to set
   * @param s	The value of @c p
   */
  [[deprecated]] void setStringProp(Property p, const TString& s);

  /**
   * @brief Set the value of a @c Property
   *
   * @param p	The @c Property to set
   * @param v	The value of @c p
   */
  void setProp(Property p, const prop_value v);

  /**
   * @brief Shorthand to set the value of a @c Property
   *
   * @param p	The @c Property to set
   * @return A reference to the value of @c p
   */
  inline prop_value& operator[](const Property p) { return properties[p]; }

  /// @}

  /**
   * @brief Check if @c this matches a given @c PropertiesSet
   *
   * Matching of @c PropertiesSet to another is used heavily in @c SystematicHandler
   * both to restrict some systs to some regions, and to define the decorrelations.
   *
   * Matching means:
   * All properties defined in @c pset are present in @c this and have the same value.
   *
   * @param pset	The @c PropertiesSet to check the matching against
   * @return @c true if @c this matches @c pset. @c false otherwise.
   */
  bool match(const PropertiesSet& pset) const;

  /**
   * @brief Merge another @c PropertiesSet into @c this
   *
   * Merging means:
   * All properties defined in @c other are set in @c this with the same value.
   *
   * If a @c Property defined in @c other already exists in @c this, its value is
   * overwritten without any warning.
   *
   * @param other	The @c PropertiesSet to merge into @c this
   */
  void merge(const PropertiesSet& other);

  /**
   * @brief Shorthand to merging @c PropertiesSet
   *
   * Merging means:
   * All properties defined in @c other are set in @c this with the same value.
   *
   * If a @c Property defined in @c other already exists in @c this, its value is
   * overwritten without any warning.
   *
   * @param other	The @c PropertiesSet to merge into @c this
   */
  PropertiesSet& operator&&(const PropertiesSet& other)
  {
    merge(other);
    return *this;
  }

  /// Prints the contents of @c this to @c stdout
  void print() const;

  /**
   * @brief Get the string tag for a @c Property
   *
   * The tags are of the form:
   *
   *     _NameValue
   *
   * where @c Name is the name of @c p as defined in @c Properties::names, and
   * @c Value is the value associated to @c p in @c this.
   *
   * @param p	The @c Property to look at
   * @return The tag associated to @c p. Throws an exception if @c p does not exist in @c this.
   */
  TString getPropertyTag(const Property p) const;

  /**
   * @brief Get the tag associated to @c this
   *
   * The tag is of the form:
   *
   *     _P1V1_P2V2_P3V3...
   *
   * where the @c Pi are the properties defined in @c this, and the @c Vi are their values.
   *
   * @return The tag associated to @c this
   */
  TString getPropertiesTag() const;
};

/**
 * @brief Syntaxic sugar to construct a @c PropertiesSet
 *
 * Allows inline construction of @c PropertiesSet such as
 *
 *     Property::nJet==2, Property::descr=="WhfCR"
 *
 * @param p The @c Property to use
 * @param v Value of the @c Property
 * @return a @c PropertiesSet built only with this @c Property
 */
inline PropertiesSet operator==(const Property p, const prop_value& v) { return PropertiesSet{p, v}; }

#endif
