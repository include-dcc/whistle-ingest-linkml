#!/usr/bin/env python

"""Build a Data-Dictionary from a CSV file for situations where one doesn't exist"""


from argparse import ArgumentParser, FileType
import sys
import uuid
from pathlib import Path
import pdb
import csv

drs_url_prefix = "drs://example.com/ga4gh/drs/v1/objects"


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
        self.distinct_values = set()
        self.varname = varname

        self.integer_values = set()
        self.float_values = set()

    def add_value(self, value):
        dtype = get_type(value)

        if dtype is int:
            self.integer_values.add(value)
        elif dtype is float:
            self.float_values.add(value)
        else:
            # pdb.set_trace()
            self.distinct_values.add(value)

    def writerow(self, writer, max_categorical_count):
        floaters = len(self.float_values)
        inters = len(self.integer_values)
        others = len(self.distinct_values)

        if floaters > inters and floaters > others:
            numbers = sorted(list(self.float_values))
            writer.writerow(
                [self.varname, self.varname, "Numeric", "", numbers[0], numbers[-1]]
            )

        elif inters > others:
            numbers = sorted(list(self.integer_values))
            writer.writerow(
                [self.varname, self.varname, "Int", "", numbers[0], numbers[-1]]
            )

        else:
            categoricals = ""

            if len(self.distinct_values) <= max_categorical_count:
                categoricals = ";".join(
                    sorted(list(self.distinct_values), key=lambda s: s.casefold())
                )
            writer.writerow(
                [self.varname, self.varname, "String", categoricals, "", ""]
            )


if __name__ == "__main__":
    parser = ArgumentParser(
        description="After looking through the file, this script will attempt to create a data dictionary"
    )

    parser.add_argument(
        "-f",
        "--file",
        required=True,
        action="append",
        type=FileType("rt"),
        help="The CSV file to be examined",
    )
    parser.add_argument(
        "-m",
        "--max-entries",
        default=25,
        type=int,
        help="The maximum number of distinct values to be recognized as a categorical",
    )
    parser.add_argument(
        "--tab",
        action="store_true",
        help="Data input is provided as TAB separated instead of Comma Separated",
    )
    args = parser.parse_args()

    writer = csv.writer(sys.stdout, delimiter=",", quotechar='"')
    writer.writerow(Variable.header)

    delimiter = ","

    if args.tab:
        delimiter = "\t"
    for filename in args.file:
        # pdb.set_trace()
        sys.stderr.write(f"\n\n--> {filename.name}\n")
        reader = csv.reader(filename, delimiter=delimiter, quotechar='"')

        header = reader.__next__()
        variables = []
        for varname in header:
            variables.append(Variable(varname))

        colcount = len(variables)
        linecount = 0
        # pdb.set_trace()
        for line in reader:
            if len(line) != colcount:
                print(f"{linecount} doesn't match header: {len(line)} != {colcount}")

            assert len(line) == colcount
            for i in range(colcount):
                variables[i].add_value(line[i])
            linecount += 1

        for var in variables:
            var.writerow(writer, args.max_entries)
