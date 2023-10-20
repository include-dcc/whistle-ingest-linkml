#!/usr/bin/env python

"""
Merges the contents of multiple files with matching header rows, tries to identify enumerated fields and then identify the unique values. 
"""

import sys
import csv
from collections import defaultdict
from argparse import ArgumentParser, FileType
from yaml import safe_load

import pdb

max_categories = 35


def get_type(value):
    try:
        x = int(value)
        return int
    except:
        pass

    try:
        x = float(value)
        return float
    except:
        pass

    return str


class Variable:
    header = ["variable_name", "description", "data_type", "enumerations", "min", "max"]

    def __init__(self, varname):
        self.distinct_values = defaultdict(set)
        self.varname = varname

        self.integer_values = set()
        self.float_values = set()

    def add_value(self, value, filename):
        dtype = get_type(value)

        if dtype is int:
            self.integer_values.add(value)
        elif dtype is float:
            self.float_values.add(value)
        else:
            # pdb.set_trace()
            self.distinct_values[value].add(filename)

    def writerow(self, writer, max_categorical_count):
        floaters = len(self.float_values)
        inters = len(self.integer_values)
        others = len(self.distinct_values)

        if floaters > inters and floaters > others:
            numbers = sorted(list(self.float_values))
            # writer.writerow([self.varname, self.varname, "Numeric", "", numbers[0], numbers[-1]])

        elif inters > others:
            numbers = sorted(list(self.integer_values))
            # writer.writerow([self.varname, self.varname, "Int", "", numbers[0], numbers[-1]])

        else:
            categoricals = ""

            if len(self.distinct_values) <= max_categorical_count:
                collisions = defaultdict(list)
                distinct = list(self.distinct_values.keys())

                categoricals = ";".join(
                    sorted(
                        list(self.distinct_values.keys()), key=lambda s: s.casefold()
                    )
                )
                writer.writerow([self.varname, " --> ", categoricals])

                for enumeration in list(self.distinct_values.keys()):
                    collisions[enumeration.lower()].append(
                        f"\n\t\t{enumeration} : {' '.join(list(self.distinct_values[enumeration]))}"
                    )
                for d in sorted(collisions.keys()):
                    if len(collisions[d]) > 1:
                        # pdb.set_trace()
                        print(f"   ->\tCollision\t{d}" + " ".join(collisions[d]))


if __name__ == "__main__":
    parser = ArgumentParser(
        description="After looking through the file, this "
        "script will attempt to create a data dictionary"
    )
    parser.add_argument(
        "config",
        nargs="+",
        type=FileType("rt"),
        help="Dataset YAML file with details required to run conversion.",
    )
    parser.add_argument(
        "-t", "--table", type=str, required=True, help="Which table to be considered"
    )
    args = parser.parse_args()

    # pdb.set_trace()
    variables = {}
    print(args.table)
    for file in args.config:
        config = safe_load(file)

        # print(f"{file.name}: {config['dataset'].keys()}")
        if args.table in config["dataset"]:
            # print(config["dataset"][args.table])
            if config["dataset"][args.table]["filename"] not in ["None"]:
                csv_filenames = config["dataset"][args.table]["filename"].split(",")

                print(f"\t: {file.name}\n\t\t* " + "\n\t\t* ".join(csv_filenames))

                for csv_filename in csv_filenames:
                    reader = csv.DictReader(
                        open(csv_filename, "rt"), delimiter=",", quotechar='"'
                    )
                    header = reader.fieldnames

                    for varname in header:
                        if varname not in variables:
                            variables[varname] = Variable(varname)

                    for line in reader:
                        for varname in header:
                            variables[varname].add_value(line[varname], file.name)

    writer = csv.writer(sys.stdout, delimiter=",", quotechar='"')
    writer.writerow(Variable.header)

    for varname in sorted(variables.keys()):
        variables[varname].writerow(writer, max_categories)
