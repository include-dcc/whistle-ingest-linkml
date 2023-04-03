#!/usr/bin/env python

"""
The data we are getting is going to contain a number of different datasets 
merged into a single csv file. That doesn't conform to the way Whistler works. 
This script splits those files into files that contain only lines that matching 
the "Study ID" field (which is how the files will be named). 
"""

import sys
from packaging import version
from yaml import safe_load
from pathlib import Path
import csv

from wstlr import die_if
import pdb

from argparse import ArgumentParser, FileType

parser = ArgumentParser(description="Split data-tables into files containing "
                        "only data for a single study")

"""
parser.add_argument("portal_table",
                    type=FileType('rt'),
                    nargs='+',
                    help="One or more tables containing studies in the portal"
                        "table format")
"""
parser.add_argument("-o",
                    "--output",
                    default="data/tables/",
                    help="Root directory for output files (each Study ID gets "
                        "it's own subdirectory")

args = parser.parse_args()
args.portal_table = ["data/INCLUDE-Spring-2023.3/all_cohorts_condition.csv",
                     "data/INCLUDE-Spring-2023.3/all_cohorts_participant.csv"]

outdir = Path(args.output)
outdir.mkdir(parents=True, exist_ok=True)

condition_min_header = ["Study Code",
                        "Participant ID",
                        "Condition Description",
                        "Age at Condition Observation",
                        "Condition Interpretation",
                        "Condition Source"]

for table_name in args.portal_table:
    table_type = Path(table_name).stem.replace("all_cohorts_", "")
    with open(table_name, 'rt') as table:
        reader = csv.DictReader(table)
        header = reader.fieldnames

        studies = set()

        for line in reader:
            studies.add(line['Study Code'])
        
        studies = sorted(list(studies))
        print(f"{len(studies)} studies were found: {', '.join(studies)}")

        for study in studies:
            table.seek(0)

            study_home = outdir / study
            study_home.mkdir(parents=True, exist_ok=True)

            outfilename = study_home / f"{Path(table_type).name}.csv"
            with outfilename.open('wt') as outf:
                writer = csv.writer(outf)

                # We have to weed out duplicate columns for condition, since the
                # same condition can have multiple mondo/hp codes. 
                observed_conditions = set()
                # This is a copy of what I used with the previous portal model
                # but I am hopeful the issues with the conditions have been
                # worked out
                if table_type == "condition----":
                    writer.writerow(condition_min_header)
                else:
                    writer.writerow(header)

                for line in reader:
                    lstudy = line['Study Code']

                    if study==lstudy:
                        if table_type == "condition----":
                            min_data = [line[x] for x in condition_min_header]
                            fake_hash = ".".join(min_data)

                            if fake_hash not in observed_conditions:
                                writer.writerow(min_data)
                                observed_conditions.add(fake_hash)
                        else:
                            writer.writerow([line[x] for x in header])


