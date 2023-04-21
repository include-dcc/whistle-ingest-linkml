#!/usr/bin/env python

"""
Using the Data Dictionary as a starting point, build out the baseline harmony
CSV file. Ultimately, we'll load this into a google sheet to let others 
populate the various external terminology references that correspond to each of
the local values. 

If the file happens to contain column headers: HPO Label/Code, MONDO Label/Code, 
MAXO Label/Code, we'll also add those to the file as well. 

"""

import csv

import pdb

from wstlr import die_if
import sys
from argparse import ArgumentParser, FileType
from pathlib import Path

from collections import defaultdict
from disease_terms import MONDO_SYSTEM, HP_SYSTEM, MAXO_SYSTEM, TermLookup

from rich import print

skip_cols = [
    "Study Code"
]


def pull_values_from_dd(dd_table, writer, empty_writer):

        
    for line in csv.DictReader(dd_table):
        #print(line)
        #pdb.set_trace()
        value_list = line['enumerations']
        varname = line['variable_name']

        if value_list != "" and varname not in skip_cols:
            values = value_list.split(";")

            for value in values:
                desc = value
                if "=" in value:
                    value, desc = value.split("=")
                coding = default_codings.match_coding(varname.lower(), value.lower())

                table_name = Path(dd_table.name).stem
                if table_name == coding['table_name'].lower():
                    #print(coding)
                    #pdb.set_trace()
                    if coding['code system'].strip() != "":
                        writer.writerow(coding.values())
                else:
                    print(f"Skipping {table_name}.{varname}.{value} because that var is listed under {coding['table_name']}")
                    print(coding)
                    empty_writer.writerow([
                        value, 
                        desc,
                        Path(dd_table.name).stem,
                        varname,
                        varname,
                        "",
                        "",
                        "",
                        ""
                    ])

def write_coding(writer, condition, coding, varname, local_desc):
    writer.writerow([
        condition,
        local_desc,
        "condition",
        varname,
        "condition_description",
        coding['code'].split(":")[-1],
        coding['display'],
        coding['system'],
        ""])

def pull_codes_from_condition(condition_file, 
                                writer, 
                                mismatch_report, 
                                invalid_report, 
                                obs_report, 
                                force_download=False):
    tlkup = TermLookup(force_download=force_download)
    missing_codes = set()

    observed_codes = set()

    for line in csv.DictReader(condition_file):
        #study_code = line['Study Code']
        condition_desc = line['Condition or Measure Source Text']

        # HPO
        try:
            coding = tlkup.hp(line)
            if coding:
                key = "-".join([condition_desc, coding['code']])
                if key not in observed_codes:
                    write_coding(writer, condition_desc, coding, "HPO Code", line['HPO Label'])
            
                    observed_codes.add(key)
        except:
            # We are logging these in the lkup object and will report back
            pass

        # MONDO
        try:
            coding = tlkup.mondo(line)
            if coding:
                key = "-".join([condition_desc, coding['code']])
                if key not in observed_codes:
                    write_coding(writer, condition_desc, coding, "MONDO Code", line['MONDO Label'])
            
                    observed_codes.add(key)
        except:
            # We are logging these in the lkup object and will report back
            pass

        # MAXO
        try:
            coding = tlkup.maxo(line)
            if coding:
                key = "-".join([condition_desc, coding['code']])
                if key not in observed_codes:
                    write_coding(writer, condition_desc, coding, "MAXO Code", line['MAXO Label'])
            
                    observed_codes.add(key)
        except:
            # We are logging these in the lkup object and will report back
            pass

    mismatch_count = tlkup.report_mismatched_labels(mismatch_report)
    sys.stderr.write(f"{mismatch_count} labels differed from those found in "
                    "the condition file(s). \n")

    invalid_count = tlkup.report_invalid_codes(invalid_report)
    sys.stderr.write(f"{invalid_count} invalid codes were found. \n")

    obsolete_count = tlkup.report_obsolete_codes(obs_report)
    sys.stderr.write(f"{obsolete_count} obsolete codes were found. \n")

class DefaultCodings:
    _header = None
    def __init__(self, filename=None):
        self.coding_list = defaultdict(dict)

        self.load(filename)

    def empty(self):
        nomatch = {}
        for field in DefaultCodings._header:
            nomatch[field] = ""
        return nomatch

    def load(self, filename=None):
        if filename is None:
            filename = Path(__file__).parent / "_default_codes.csv"
        
        with filename.open('rt') as f:
            reader = csv.DictReader(f)

            if DefaultCodings._header is None:
                DefaultCodings._header = reader.fieldnames

            for line in reader:
                #print(line)
                #pdb.set_trace()
                self.coding_list[line['parent_varname'].lower()][line['local code'].lower()] = line

    def match_coding(self, field_name, value):
        match = None
        #if field_name.lower() == "condition interpretation":
        #    pdb.set_trace()
        if field_name.lower() in self.coding_list:
            match = self.coding_list[field_name.lower()].get(value.lower())
        if match is None:
            return self.empty()
        return match

parser = ArgumentParser(description="Build out a baseline harmony csv based "
                        "on the contents of the data-dictionary")
parser.add_argument("table_dd",
                    type=FileType('rt'),
                    nargs='+',
                    help="One or more data-dictionaries. Multiple files will "
                        "be annotated independently.")
parser.add_argument("-c", 
                    "--conditions",
                    type=FileType('rt'),
                    required=True,
                    help="The full condition file containing all codes "
                    "currently recognized")
parser.add_argument("--invalid-report",
                    default="output/invalid-codes.csv",
                    type=FileType('wt'),
                    help="Name of log to report all codes that were not found "
                    "when searching the ontology for a match. ")
parser.add_argument("-m",
                    "--mismatched-report",
                    default="output/mismatched-code-labels.csv",
                    type=FileType('wt'),
                    help="Name of log to report all labels that differ "
                    "between the code system's official display and the "
                    "local description provided. ")
parser.add_argument("-x",
                    "--obsolete-report",
                    default="output/obsolete-codes.csv",
                    type=FileType('wt'),
                    help="Name of log to report all codes used that are "
                    "marked as obsolete")
parser.add_argument("-o",
                    "--output-filename",
                    default="harmony/data-harmony.csv",
                    help="Filename where we'll write our generated CSV file.")
parser.add_argument("-u", 
                    "--unmatched-filename", 
                    default="harmony/empty-harmony.csv",
                    help="Filename where we'll write our terms which don't have a meaningful harmony match")
args = parser.parse_args()
default_codings = DefaultCodings()
outfilename = Path(args.output_filename)
empties = Path(args.unmatched_filename)
print(f"Writing to file, {outfilename}")
print(f"Items without valid harmony to be written to: {empties}.")

with outfilename.open('wt') as outf:
    writer = csv.writer(outf)

    with empties.open('wt') as emptyf:
        empty_writer = csv.writer(emptyf)
        empty_writer.writerow(["local code",
                        "text",
                        "table_name",
                        "parent_varname",
                        "local code system",
                        "code",
                        "display",
                        "code system",
                        "comment"])
        
        # Other are those that aren't necessarily found in the data-dictionary but are
        # otherwise required for harmonizing certain parts of the data
        with open(Path(__file__).parent / "_other_codes.csv", 'rt') as inf:
            reader = csv.reader(inf, delimiter=",", quotechar='"')
            for line in reader:
                writer.writerow(line)

        # We'll cache the "Condition Description" and the specified code to avoid 
        # having redundant entries in the harmony file. 
        harmonized_conditions = set()
        for dd_table in args.table_dd:
            pull_values_from_dd(dd_table, writer, empty_writer)

        pull_codes_from_condition(args.conditions, writer, args.mismatched_report, args.invalid_report, args.obsolete_report)

