#!/bin/env python

# This module implements the ATLAS rounding rulesbased on
# https://cds.cern.ch/record/1668799/files/ATL-COM-GEN-2014-006.pdf
#
# Note: because it uses round (and in general floats), it is affected
# by the limitations described in
# http://docs.python.org/library/functions.html#round
#  and
# http://dx.doi.org/10.1145/103162.103163
#
# Adapted from https://github.com/gerbaudo/python-scripts/blob/master/various/pdgRounding.py by davide.gerbaudo@gmail.com


__all__ = ["atlasRound"]

def atlasRound(value, stat, syst = None, nsig = None, close = 0.5) :
    """
    Given a `value` and an error (`stat` and optional `syst`), round and format them according to the ATLAS 
    rules for significant digits.

    * If no systematic error is given the rule is the same as the PDG rule.

    * If a systematic error is given, the larger of the two errors is used, except for the case where they 
      are of similar size and on either side of the boundary for 1 or 2 s.f., when 2 s.f. are kept
      - Similar is defined as abs(stat-syst) < `close` * min(stat, syst), where `close` defaults to 0.5

    * If the errors are asymmetric (i.e. different up and down) the larger is taken

    * if `nsig` is given, then do not calculate rounding rules but round directly to that number of s.f.
      - Useful for tables or systematic errors, where ATLAS rule is 2 s.f.

    """

    def threeDigits(value) :
        "extract the three most significant digits and return them as an int"
        return int(("%.2e"%float(error)).split('e')[0].replace('.','').replace('+','').replace('-',''))

    def nSignificantDigits(threeDigits) :
        assert threeDigits<1000,"three digits (%d) cannot be larger than 10^3"%threeDigits
        if threeDigits<101 : return 2 # not sure
        elif threeDigits<356 : return 2
        elif threeDigits<950 : return 1
        else : return 2

    def frexp10(value) :
        "convert to mantissa+exp representation (same as frex, but in base 10)"
        valueStr = ("%e"%float(value)).split('e')
        return float(valueStr[0]), int(valueStr[1])

    def nDigitsValue(expVal, expErr, nDigitsErr) :
        "compute the number of digits we want for the value, assuming we keep nDigitsErr for the error"
        return expVal-expErr+nDigitsErr

    def formatValue(value, exponent, nDigits, extraRound=0) :
        "Format the value; extraRound is meant for the special case of threeDigits>950"
        roundAt = nDigits-1-exponent - extraRound
        nDec = roundAt if exponent<nDigits else 0
        if nDec < 0: nDec = 0
        val = float(('%.'+str(nDec)+'f')%round(value,roundAt))
        val = int(val) if val % 1 == 0 else val
        return val

    # deal with asymmetric errors, taking the larger
    mstat, msyst = stat, syst
    if isinstance(stat, tuple):
        mstat = max(e for e in stat)
    if syst is not None and isinstance(syst, tuple):
        msyst = max(e for e in syst)

    # Take larger of stat/syst error if one is significantly bigger than other, 
    # else evaulate both and take the larger number of significant figures

    tD = 0
    error = mstat
    if nsig is not None: 
        # Overwite to nsig
        nD = nsig
    elif syst is not None:
        mE = min(mstat, msyst)
        error = max(mstat, msyst)
        if abs(msyst - mstat) < close*mE:
            tD = threeDigits(mstat)
            nD = nSignificantDigits(tD)
            if nD == 1:
                stD = threeDigits(msyst)
                snD = nSignificantDigits(stD)
                if snD == 2:
                    nD = 2
        else:
            tD = threeDigits(error)
            nD = nSignificantDigits(tD)
    else:
        tD = threeDigits(error)
        nD = nSignificantDigits(tD)

    # Round
    extraRound = 1 if tD>=950 else 0
    expVal, expErr = frexp10(value)[1], frexp10(error)[1]

    val = formatValue(value, expVal, nDigitsValue(expVal, expErr, nD), extraRound)

    statOut = []
    stat = stat if isinstance(stat, (tuple, list)) else (stat,)
    for e in stat:
        exp = frexp10(e)[1]
        statOut.append(formatValue(e, exp, nDigitsValue(exp, expErr, nD), extraRound))

    if syst is None:
        return (val, tuple(statOut) if len(statOut)>1 else statOut[0])

    systOut = []
    syst = syst if isinstance(syst, (tuple, list)) else (syst,)
    for e in syst:
        exp = frexp10(e)[1]
        systOut.append(formatValue(e, exp, nDigitsValue(exp, expErr, nD), extraRound))

    return (val, tuple(statOut) if len(statOut)>1 else statOut[0], tuple(systOut) if len(systOut)>1 else systOut[0])
            

def test(valueError=(0., 0.)) :
    val, err = valueError
    print(val,' +/- ',err,' --> ', end=' ')
    val, err = atlasRound(val, err)
    print(' ',val,' +/- ',err)

if __name__=='__main__' :
    for x in [(0.827, 0.119121212)
              ,(0.827, 0.3676565)
              ,(0.827, 0.952)
              ,(1.2345e7, 67890.1e2)
              ,(1.2345e7, 54321.1e2)
              ,(1.2345e7, 32100.1e2)
              ,(0.00827, 0.0000123)
              ,(0.00827, 0.0000456)
              ,(0.00827, 0.0000952)
              ] : test(x)

    print()

    for x in [(0.9441, 0.119),
              (0.9441, 0.367),
              (0.9441, 0.967),
              (0.9441, 0.0632),
              (0.9441, 1.0632),
              (0.9441, 9.0632),
              (0.9441, 9.6632)] : test(x)

    print() 

    for x in [(191819, 17), 
              (191819, 17891),
              (191819, 37891), 
              (191819, 97891)] : test(x)
