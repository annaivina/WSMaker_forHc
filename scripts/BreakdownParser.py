import os, re

class BreakdownParser:
    """
    Parser to extract information from uncertainty breakdown files usually found in plots/breakdown/*.txt.

    Author: Philipp Windischhofer
    Date:   November 2019
    Email:  philipp.windischhofer@cern.ch

    Description:
        Provides some methods to extract information from breakdown tables in *.txt format.
    """
    
    @staticmethod
    def get_POI_name(filepath):        
        """
        Return the name of the POI this breakdown belongs to.
        Arguments:
            filepath ... full path to the breakdown *.txt file
        """

        POI_name_regex = re.compile(".*poi: (.+);.*")

        extracted_POI_names = BreakdownParser._extract_with_regex(filepath, POI_name_regex)

        if len(extracted_POI_names) == 1:
            return extracted_POI_names[0]
        else:
            raise Exception(f"Error: found more than one POI in file '{filepath}'")

    @staticmethod
    def get_POI_value(filepath):
        """
        Returns the fitted value of the POI this breakdown belongs to.
        Arguments:
            filepath ... full path to the breakdown *.txt file
        """

        POI_value_regex = re.compile(r".*muhat: (.+)\s*")

        extracted_POI_values = BreakdownParser._extract_with_regex(filepath, POI_value_regex)

        if len(extracted_POI_values) == 1:
            return float(extracted_POI_values[0])
        else:
            raise Exception(f"Error: found more than one POI in file '{filepath}'")

    @staticmethod
    def get_unc(filepath, unc_name):
        """
        Returns a given uncertainty component contained in this breakdown.
        Arguments:
            filepath ... full path to the breakdown *.txt file
            unc_name ... name of the uncertainty component
        Returns:
            a dictionary of the form {'unc_hi': ..., 'unc_lo': ..., 'unc_sym': ...}
            that contains the up / down as well as the symmetrised uncertainty.
        """

        unc_regex = fr"\s*{unc_name}\s*\+\s*(.+)\s*\-\s*(.+)\s*\+\-\s*(.+)"

        def unc_lambda(m):
            return {'unc_hi': float(m.group(1)), 
                    'unc_lo': float(m.group(2)), 
                    'unc_sym': float(m.group(3))}

        return BreakdownParser._apply_func(filepath, unc_lambda, regex = unc_regex, 
                                          section_start_regex = r".*Set of nuisance\s*Impact on error.*", 
                                          section_end_regex = ".*Impact on error quadratically subtracted from total, except for:.*")

    # internal methods
    @staticmethod
    def _apply_func(filepath, func, regex, section_start_regex, section_end_regex):
        """
        Apply a function to a line in the breakdown file that matches certain criteria.
        """

        if isinstance(regex, str):
            regex = re.compile(regex)

        if isinstance(section_start_regex, str):
            section_start_regex = re.compile(section_start_regex)

        if isinstance(section_end_regex, str):
            section_end_regex = re.compile(section_end_regex)

        section_active = False
        with open(filepath) as infile:
            for line in infile:
                if re.match(section_start_regex, line):
                    section_active = True

                if re.match(section_end_regex, line):
                    section_active = False

                if section_active:
                    m = re.match(regex, line)
                    if m:
                        return func(m)

    @staticmethod
    def _extract_with_regex(filepath, regex):
        """
        Convenience method to return the value returned by the first capturing group of a given regex.
        """
        extracted = []

        with open(filepath) as infile:
            for line in infile:
                m = re.match(regex, line)
                if m:
                    extracted.append(m.group(1))

        return extracted
