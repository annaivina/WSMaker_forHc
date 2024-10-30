#ifndef utility_hpp
#define utility_hpp

#include <vector>

#include <TString.h>

class TObjArray;
class TH1;

/**
 * @brief A few small general-purpose functions
 *
 * That don't depend on anything specific
 */
namespace Utils {

  /**
   * @brief Split a @c TString at occurrences of a separator
   *
   * @todo Could we use @c TString::Tokenize() to simplify it further ?
   *
   * @param orig The string to split
   * @param separator The separator character
   * @return A vector containing the substrings
   */
  std::vector<TString> splitString(TString orig, const char separator);

  /**
   * @brief Inverse of @c splitString.
   *
   * The call assemble(elems, separator) is equivalent to Python's separator.join(elems),
   * i.e. it assembles a list of strings into a single string, separating the individual
   * elements by the 'separator'.
   *
   * @param elems the list of strings to be assembled
   * @param separator the separator character to be used
   * @return a string containing the concatenated (i.e. "assembled") result
   */
  TString assemble(const std::vector<TString>& elems, char separator);

  /**
   * @brief take the "difference" between two vectors, i.e. return a new vector that contains
   * all elements of 'original' that are not contained in 'to_delete'. Note: `original` is not
   * modified in the process.
   *
   * @param original original vector
   * @param to_delete vector whose elements should not be present in the returned vector
   * @return the modified vector
   */
  template <typename T> std::vector<T> vector_difference(std::vector<T> original, const std::vector<T>& to_delete)
  {
    for( auto cur : to_delete ) {
      original.erase(std::remove(original.begin(), original.end(), cur), original.end());
    }
    return original;
  }

  /**
   * @brief Convert @c float to @c TString
   *
   * @todo Do we still need this function ?
   *
   * @param d	The @c float to convert
   * @return A @c TString representation of the @ float
   */
  TString ftos(float d);

  /**
   * @brief Get a specific @c TString item in a @c TObjArray
   *
   * Used to easily parse the results of @c TPRegexp matches
   *
   * @param res	The @c TObjArray of @c TString
   * @param i The index we want to look at
   * @return The @c TString at position @c i
   */
  TString group(TObjArray* res, int i); // get some group out of matching res

  /**
   * @brief Symmetrize an histogram wrt another
   *
   *     down = 2*nominal - up
   *
   * Used to symmetrize systematics for instance
   *
   * @param up	The histogram to symmetrize
   * @param nominal	The reference histogram
   * @return The symmetric of @c up wrt @c nominal
   */
  TH1* symmetrize(const TH1* up, const TH1* nominal);

  /**
   * @brief Square the src histogram, then add it into the sumsq histogram
   *
   * @param sumsq    Reference to the pointer of a quadratically summed histogram. This can be overwritten by the
   * pointer of a new object if nullptr is given.
   * @param src       Pointer of a histogram that is to be added.
   */
  void sumOfSquares(TH1*& sumsq, const TH1* src);

  /**
   * @brief Update the given histgram with its square root.
   *
   * @param hist       Pointer to a histogram which is taken the square root of.
   */
  void squareRootOfHist(TH1* hist);

  /**
   * @brief Calculate relative errors per bin that are summed up in quadrature
   *
   * Calculate relative error histograms to create inputs for ShapeSys type systematics.
   * * First, it sums up the nominal histograms and absolute errors that are in the given lists
   * * Second, it divides abolute errors by nominal yields to calculate relative error
   *
   * @param v_nom    Reference to the list of nominal histograms
   * @param v_syst   Reference to the list of histograms for absolute errors
   * @return         Resulting relative error histogram
   */
  TH1* GetSystRatioForQuadrature(const std::vector<const TH1*>& v_nom, const std::vector<const TH1*>& v_syst);

} // namespace Utils

#endif
