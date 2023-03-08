#!/usr/bin/env python

"""
For now, we will automate the download of obo files specific to the disease
terminologies and provide the ability to verify those terms.
"""

import networkx
import obonet
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import csv
import requests
import wget
import pdb

MONDO_SYSTEM = "http://purl.obolibrary.org/obo/mondo.owl"
HP_SYSTEM = "http://purl.obolibrary.org/obo/hp.owl"
MAXO_SYSTEM = "http://purl.obolibrary.org/obo/maxo.owl"

INVALID_CODES = ["", "NA"]

class InvalidCode(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(self.message())

    def message(self):
        return f"The code, {self.code}, doesn't appear to be a valid code."

class ObsoleteCode(Exception):
    def __init__(self, code, replacement):
        self.code = code
        self.replacement = "\n".join(replacement)
        super().__init__(self.message())

    def message(self):
        return f"The code, {self.code}, appears to be obsolete. Replacement text: {self.replacement}"

"""
class MismatchedLabel(Exception):
    def __init__(self, code, label, other_label):
        self.code = code
        self.label = label
        self.other_label = other_label
        super().__init__(self.message())

    def message(self):
        return f"{self.code} has a different label than what was expected: {self.label} != {self.other_label}."
"""
class MismatchedLabel:
    def __init__(self, code, label, other_label):
        self.code = code
        self.label = label
        self.other_label = other_label
    
    def report(self, terminology, writer):
        writer.writerow([terminology, self.code, self.label, self.other_label])

class TermLookup:
    obo_files = {
        "hp": "https://github.com/obophenotype/human-phenotype-ontology/raw/master/hp-full.obo",
        "maxo": "https://github.com/monarch-initiative/MAxO/raw/master/maxo-full.obo",
        "mondo": "http://purl.obolibrary.org/obo/mondo.obo"
    }

    systems = {
        "hp": HP_SYSTEM,
        "maxo": MAXO_SYSTEM,
        "mondo": MONDO_SYSTEM
    }

    local_obo_files = {}

    script_path = Path(__file__).parent / "obo_files"
    def __init__(self, force_download=False):
        self.terms = {}

        # Actual codes from the ontology, not necessary those in use
        self.obsolete_terms = {}

        self.download_terms(force_download=force_download)
        self.load_terms()

        # terminology => code => obj
        self.mismatched_labels = defaultdict(dict)

        # code => description
        self.invalid_codes = {}

        # code => replacement
        self.obsolete_codes = {}


    def load_terms(self):
        for onto in TermLookup.local_obo_files.keys():
            obo_file = TermLookup.local_obo_files[onto]
            print(obo_file)

            #pdb.set_trace()
            obsolete = {}

            graph = obonet.read_obo(obo_file, ignore_obsolete=False)
            nodes = graph.nodes(data=True)
            nodedata = {id_: data.get('name') for id_, data in nodes}
            for id, data in nodes:
                if 'alt_id' in data:
                    for aid in data['alt_id']:
                        if aid not in data:
                            nodedata[aid] = data.get('name')
                if 'is_obsolete' in data:
                    obsolete[id] = ""
                    if 'replaced_by' in data:
                        obsolete[id] = data['replaced_by']    

            print(f"The length of the system is {len(nodedata)}")
            print(f"The number of obsolete terms is {len(obsolete)}")
            self.terms[onto] = nodedata
            self.obsolete_terms[onto] = obsolete

    def download_terms(self, max_file_age_days=30, force_download=False):
        TermLookup.script_path.mkdir(parents=True, exist_ok=True)
        print(TermLookup.obo_files.keys())
        for onto in TermLookup.obo_files.keys():
            #pdb.set_trace()
            url = TermLookup.obo_files[onto]
            obo_filename = url.split("/")[-1]
            local_fn = TermLookup.script_path / obo_filename

            TermLookup.local_obo_files[onto] = local_fn

            download_file = True

            if not force_download and local_fn.is_file():
                stat_info = local_fn.stat()
                download_file = stat_info.st_size > 100 and (datetime.now() - 
                        datetime.fromtimestamp(stat_info.st_mtime)
                        ).days > max_file_age_days

            if download_file:
                print(f"Downloading file for ontology: {onto}")
                wget.download(TermLookup.obo_files[onto], str(local_fn))
                """
                response = requests.get(TermLookup.obo_files[onto], allow_redirects=True)
                print(response)
                pdb.set_trace()
                with local_fn.open('wt') as outf:
                    outf.write(response.text)
                """
            else:
                print(f"Skipping obo file for {onto}")

    def get_code(self, terminology, code):
        if code in self.terms[terminology]:
            if code in self.obsolete_terms[terminology]:
                raise ObsoleteCode(code, self.obsolete_terms[terminology][code])
            return {
                "code": code,
                "display": self.terms[terminology][code],
                "system": TermLookup.systems[terminology]
            }
        else:
            raise InvalidCode(code)

    def hp(self, row):
        code = row['HPO Code']
        if code.strip() not in INVALID_CODES:
            try:
                coding = self.get_code("hp", code.strip())
                if coding['display'] != row['HPO Label']:
                    self.mismatched_labels["HP"][code] = MismatchedLabel(code, coding['display'], row['HPO Label'])
                return coding
            except InvalidCode:
                self.invalid_codes[code] = row['HPO Label']
            except ObsoleteCode as e:
                self.obsolete_codes[code] = e.replacement
    def mondo(self, row):
        code = row['MONDO Code']
        if code.strip() not in INVALID_CODES:
            try:
                coding = self.get_code("mondo", code.strip())
                if coding['display'] != row['MONDO Label']:
                    self.mismatched_labels["MONDO"][code] = MismatchedLabel(code, coding['display'], row['MONDO Label'])
                return coding
            except InvalidCode:
                self.invalid_codes[code] = [row['MONDO Label']]
            except ObsoleteCode as e:
                self.obsolete_codes[code] = e.replacement

    def maxo(self, row):
        code = row['MAXO Code']
        if code.strip() not in INVALID_CODES:
            try:
                coding = self.get_code("maxo", code.strip())
                if coding['display'] != row['MAXO Label']:
                    self.mismatched_labels["MAXO"][code] = MismatchedLabel(code, coding['display'], row['MAXO Label'])
                return coding
            except InvalidCode:
                self.invalid_codes[code] = [row['MAXO Label']]
            except ObsoleteCode as e:
                self.obsolete_codes[code] = e.replacement

    def report_invalid_codes(self, outfile):
        writer = csv.writer(outfile)
        writer.writerow(['Code', 'Description'])

        for code in sorted(self.invalid_codes.keys()):
            writer.writerow([code, self.invalid_codes[code]])

        return len(self.invalid_codes)

    def report_obsolete_codes(self, outfile):
        writer = csv.writer(outfile)
        writer.writerow(['Code', 'Replacement'])

        for code in sorted(self.obsolete_codes.keys()):
            writer.writerow([code, self.obsolete_codes[code]])

        return len(self.obsolete_codes)        

    def report_mismatched_labels(self, outfile):
        mismatch_count = 0

        writer = csv.writer(outfile)
        writer.writerow(['Terminology', 'Code','Display', 'Local Label'])

        for term in ['HP', 'MONDO', 'MAXO']:
            for code in self.mismatched_labels[term]:
                self.mismatched_labels[term][code].report(term, writer)
                mismatch_count += 1
        return mismatch_count
"""
def try_code(code):
    print(f"Tring {code}")
    curie, thecode = code.strip().split(":")
    if curie == "MONDO":
        print(tlkup.mondo(code))
    if curie == "HP":
        print(tlkup.hp(code))
    if curie == "MAXO":
        print(tlkup.maxo(code))

tlkup = TermLookup(force_download=False)

try_code("MONDO:0700030")
try_code("MONDO:0000050")
try_code("HP:0001051")
try_code("HP:0001631")
try_code("MAXO:0009044")
try_code("MAXO:0025002")
        

"""