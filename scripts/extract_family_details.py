#!/usr/bin/env python

from pathlib import Path
import csv
from argparse import ArgumentParser,FileType

import pdb
from collections import defaultdict

from yaml import safe_load


class Family:
    def __init__(self, row):
        self.family_id = row["Family ID"]
        self.family_type = row["Family Type"]
        self.proband_ids = set()
        self.relationships = defaultdict(set)

    def extract_id(self, row, colname):
        if row[colname] != "NA":
            ids = [x.strip() for x in row[colname].split(",")]

            for id in ids:
                self.relationships[colname].add(id)

    def add_participant(self, row):
        id = row["Participant External ID"]
        self.extract_id(row, "Sibling ID")
        self.extract_id(row, "Father ID")
        self.extract_id(row, "Mother ID")
        
        relationships = [x.strip() for x in row["Family Relationship"].split(",")]
        for relationship in relationships:
            if relationship == "Proband":
                self.proband_ids.add(id)
            elif relationship == "Mother":
                self.relationships["Mother ID"].add(id)
            elif relationship == "Father":
                self.relationships["Father ID"].add(id)
            elif relationship == "Sibling":
                self.relationships["Sibling ID"].add(id)
            else:
                self.relationships[relationship].add(id)

    @classmethod
    def write_header(cls, writer):
        writer.writerow([
            "Family ID",
            "Family Type",
            "ID1", 
            "ID2",
            "Relationship"
        ])

    def write(self, writer):
        observed_probands = set()
        for proband in self.proband_ids:
            for relationship, idlist in self.relationships.items():
                # Drop the " ID" part
                relid = relationship.split(" ")[0]
                for id in idlist:
                    if id != proband and id not in observed_probands:
                        writer.writerow([
                            self.family_id,
                            self.family_type,
                            id, 
                            proband,
                            relid
                        ])
            observed_probands.add(proband)

                # For now, let's skip the sibling list and only create 
                # relationships that involve a proband

if __name__=="__main__":
    parser = ArgumentParser(description="After looking through the file, this "
                            "script will attempt to create a data dictionary")
    parser.add_argument(
        "config",
        nargs='+',
        type=FileType('rt'),
        help="Dataset YAML file with details required to run conversion.",
    )
    args = parser.parse_args()

    for f in args.config:
        config = safe_load(f)

        # All of the family stuff lives inside the participant table
        filename = config["dataset"]["participant"]["filename"]

        filedir = Path(filename).parent

        families = {}

        # Pull Condition events out and build out our discrete event list
        with open(filename, "rt") as condf:
            participants = csv.DictReader(condf, delimiter=',', quotechar='"')

            for line in participants:
                fid = line["Family ID"]

                if fid not in families:
                    families[fid] = Family(line)
                
                families[fid].add_participant(line)

        family_path = filedir / "family.csv"
        print(family_path)
        #pdb.set_trace()
        # For now, we won't worry if the file exists
        with family_path.open('wt') as outf:
            fwriter = csv.writer(outf, delimiter=',', quotechar='"')
            Family.write_header(fwriter)

            for fam in families:
                families[fam].write(fwriter)