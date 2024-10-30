#!/usr/bin/env python


from argparse import ArgumentParser
import glob, os, re, functools

def get_POI_name(lines):
    poi_extractor = re.compile(".*poi: (.+);")
    for line in lines:
        m = poi_extractor.match(line)
        if m:
            return m.group(1)

    raise RuntimeError("Error: no poi information found in this header!")

def get_POI_central_value(lines):
    poi_extractor = re.compile("muhat: (.+)")
    for line in lines:
        m = poi_extractor.match(line)
        if m:
            return m.group(1)

    raise RuntimeError("Error: no information about poi central value found in this header!")

def get_TeX_table_header(lines):

    tex_header = []
    column_extractor = re.compile(r"(.+)\s{2,}(.+)")
    
    for line in lines:

        m = column_extractor.match(line)
        if m:
            tex_header.append(" & ".join([m.group(1), m.group(2), ""]))

        if is_table_start_line(line):
            break

    return tex_header

def get_TeX_table_datalines(lines):

    tex_lines = []
    table_line_parser = re.compile(r"(.+)\+(.+)\-(.+)\+\-(.+)")

    for line in lines:

        m = table_line_parser.match(line)
        if m:
            tex_lines.append(r"{name} & +{unc_p} / -{unc_m} & $\pm {unc_pm}$".format(name = m.group(1).strip().ljust(30), unc_p = m.group(2).strip(), 
                                                                                    unc_m = m.group(3).strip(), unc_pm = m.group(4).strip()))

    return tex_lines

def add_TeX_EOL(lines):
    # add end-of-line characters everywhere
    return [cur + "\\\\" for cur in lines]

def get_TeX_table_body(lines):

    table_header = add_TeX_EOL(get_TeX_table_header(lines))
    table_data = add_TeX_EOL(get_TeX_table_datalines(lines))
    tex_table = table_header + ["\\hline", "\\hline"] + table_data

    return tex_table

def get_TeX_table(lines, poi_name, poi_value):
    
    tex_table = []
    tex_table_prolog = ["\\begin{tabular}{|l|c|c|}", "\\hline"]
    tex_table_epilog = ["\\hline", "\\end{tabular}"]

    # compose the table
    tex_table += ["POI & Central Value & \\\\"]
    tex_table += [f"{poi_name} & {poi_value} & \\\\"]
    tex_table += ["\\hline", "\\hline"]
    tex_table += get_TeX_table_body(lines)
    
    return "\n".join(tex_table_prolog + tex_table + tex_table_epilog)

def is_table_line(line):

    table_line_parser = re.compile(r"(.+)\+(.+)\-(.+)+-(.+)")
    if table_line_parser.match(line):
        return True
    else:
        return False

def is_separation_line(line):
    return True if line == "\n" else False

def is_table_start_line(line):
    return True if "------------------" in line else False

def parse_file(lines):

    # to hold the extracted parts of the file
    header = []
    tables = []
    
    # simple state machine
    state = "wait_for_table"

    for line in lines:
        
        if state == "wait_for_table":
            header.append(line)

            if is_table_line(line):
                # start a new table
                state = "table"
                cur_table = []

                # add table header post-hoc
                table_header = []
                while True:
                    table_header.append(header.pop())
                    if is_separation_line(table_header[-1]):
                        break

                cur_table += reversed(table_header)

            continue

        if state == "table":
            
            if is_table_line(line):
                cur_table.append(line)
            else:
                tables.append(cur_table)
                state = "wait_for_table"

            continue

    return header, tables

def ConvertBreakdown(breakdown_path, converted_path):
    
    # read all lines from the file
    lines = []
    with open(breakdown_path) as infile:
        for line in infile:
            lines.append(line)

    # split the file into the file header and the tables
    header, tables = parse_file(lines)

    # extract all the necessary information
    poi_name = get_POI_name(header)
    poi_value = get_POI_central_value(header)
    tex_tables = list(map(functools.partial(get_TeX_table, poi_name = poi_name, poi_value = poi_value), tables))

    # start composing the output file
    with open(converted_path, 'w') as outfile:
        for table in tex_tables:
            outfile.write(table)
            outfile.write("\n\n\n")

def ConvertAllBreakdowns(ws_path):
    
    # find available breakdown files
    available_breakdowns = glob.glob(os.path.join(ws_path, "*.txt"))

    for cur_breakdown in available_breakdowns:
        converted_breakdown = os.path.splitext(cur_breakdown)[0] + ".tex"
        ConvertBreakdown(cur_breakdown, converted_breakdown)

if __name__ == "__main__":
    
    parser = ArgumentParser()
    parser.add_argument("ws")
    args = parser.parse_args()

    ws_path = f"output/{args.ws}/plots/breakdown"
    ConvertAllBreakdowns(ws_path)
