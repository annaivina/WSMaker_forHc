#ifndef containerhelpers_hpp
#define containerhelpers_hpp

#include <functional>
#include <string>
#include <unordered_map>
#include <vector>

#include <TString.h>

/**
 * @file containerhelpers.hpp
 * @brief Helpers for unordered containers
 */

namespace std {
  /**
   * @brief Implementation of @c std::hash for @c TString
   *
   * Simply use @c std::string hash on the internal @c char* of @c TString
   *
   * Allows to have unordered contaniers of @c TString
   */
  template <> struct hash<TString> {
    std::size_t operator()(TString const& s) const { return std::hash<std::string>()(s.Data()); }
  };
} // namespace std

namespace Utils {
  /**
   * @brief Compute the inverse of a map
   *
   * Transform map<key, value> into map<value, key>.
   * Nothing is done to prevent collisions, so when several keys have the same value,
   * only one will be kept, with no predictable ordering
   *
   * @param m_in Input map<key, value>
   * @return Output map<value, key>
   *
   */
  template <typename T, typename U> std::unordered_map<U, T> reverseMap(const std::unordered_map<T, U>& m_in);

  template <typename T, typename U> std::unordered_map<U, T> reverseMap(const std::unordered_map<T, U>& m_in)
  {
    std::unordered_map<U, T> m_out;
    for( auto& it : m_in ) {
      m_out.emplace(it.second, it.first);
    }
    return m_out;
  }

  /**
   * @brief Append the contents of a vector to another
   *
   * @param v_in Vector which will be expanded
   * @param v_to_append Vector from which the elements are copied
   */
  template <typename T> void appendToVec(std::vector<T>& v_in, const std::vector<T>& v_to_append)
  {
    v_in.insert(v_in.end(), v_to_append.begin(), v_to_append.end());
  }
} // namespace Utils

#endif
