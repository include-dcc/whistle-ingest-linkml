#!/usr/bin/env python

import requests
from io import StringIO
from yaml import safe_load
from pathlib import Path
import csv

import pdb

# We'll get biospecimen and datafile stuff from this when it's time
assay_url = "https://raw.githubusercontent.com/include-dcc/include-linkml/main/src/linkml/include_assay.yaml"

# Participant contains Participant and Condition table definitions
participant_url = "https://raw.githubusercontent.com/include-dcc/include-linkml/main/src/linkml/include_participant.yaml"

# We want to populate any harmony encodings we can to avoid missing stuff like
# we have run into in the past
harmony_seeds = Path("harmony/lml-harmony-seed.csv")

class DdVariable:
    def __init__(self, table_name, name, data, enums, harmony_seed):
        self.name = name
        self.title = data['title']
        self.description = data['description']
        self.enums = None
        if 'range' not in data:
            print(data.keys())
            print(self.name)
        self.data_type = data.get('range')
        if self.data_type is None:
            self.data_type = 'string'

        if data.get('range') in enums:
            self.enums = enums[data.get('range')]
            self.data_type = "enumeration"

            self.enums.write_harmony_seed(harmony_seed, table_name, self.title)

    @classmethod
    def print_header(cls, writer):
        writer.writerow([
            "variable_name",
            "description",
            "data_type",
            "enumerations"
        ])

    def print(self, writer):
        enums = ""

        if self.enums is not None:
            enums = self.enums.as_string()

        title = self.title

        if title == "Has Participant":
            title = "Study Code"
        writer.writerow([
            title, 
            self.description,
            self.data_type, 
            enums
        ])

class DdTable:
    def __init__(self, table_name, data, slots, enums, harmony_seed):
        self.name = table_name
        self.title = data['title']
        self.description: data['description']
        self.variables = []

        for slot in data['slots']:
            self.variables.append(DdVariable(table_name,
                                                slot, 
                                                slots[slot], 
                                                enums, 
                                                harmony_seed))

    def print(self, writer):
        for var in self.variables:
            var.print(writer)

class DdCodeEnumeration:
    def __init__(self, data):
        self.text = data['text']
        self.title = data['title']
        self.description = data.get('description')
        if self.description is None:
            self.description = self.title

        if ";" in self.title:
            # We don't want descriptions with semi colons
            pass
            #self.description = self.description.replace("; ", "--")

        assert(";" not in self.title) 
        self.meaning = data.get('meaning')

    @classmethod
    def harmony_seed_header(cls, writer):
        writer.writerow([
            'local code',
            'text',
            'table_name',
            'parent_varname',
            'local code system',
            'code',
            'display',
            'code system',
            'comment'
        ])

    def harmony_seed(self, table_name, fieldname, writer):
        if writer is not None:
            print(f"{table_name}:{fieldname}:{self.title}")
            writer.writerow([
                self.title,
                self.description,
                table_name,
                fieldname,
                fieldname
            ])

class DdCodeSystem:
    def __init__(self, data):
        self.name = data['name']
        self.codings = {}

        for code, coding in data['permissible_values'].items():
            self.codings[code] = DdCodeEnumeration(coding)

    def as_string(self):
        codings = []

        for code, coding in self.codings.items():
            codings.append(coding.title)

        return ";".join(codings)
    
    def write_harmony_seed(self, harmony_seed, table_name, fieldname):
        for code, enumeration in self.codings.items():
            enumeration.harmony_seed(table_name, fieldname, harmony_seed)

def get_content(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text    

def pull_from_github(url, tablenames, common_slots):
    enums = {}
    tables = {}

    hseed = None        # Harmony Seed file (write)        

    # Only open the seed file if it doesn't exist as this will only be a 
    # template
    if not harmony_seeds.exists():
        seedfile = harmony_seeds.open('wt')
        hseed = csv.writer(seedfile, delimiter=',', quotechar='"')
        DdCodeEnumeration.harmony_seed_header(hseed)

    with StringIO(get_content(url)) as fd:
        content = safe_load(fd)

        # Build out the enumerations
        for enum, data in content['enums'].items():
            enums[enum] = DdCodeSystem(data)

        slots = common_slots | content['slots']

        for name in tablenames:
            tables[name] = DdTable(name, content['classes'][name], slots, enums, hseed)

    return enums, tables

def collect_slots(url, slots={}):
    with StringIO(get_content(url)) as fd:
        content = safe_load(fd)
        return content['slots']

if __name__=='__main__':
    outdir = Path("output/dd/")
    outdir.mkdir(parents=True, exist_ok=True)
    tables_of_interest = ["Participant", "Condition"]
    base_slots = collect_slots(assay_url)
    enums, tables = pull_from_github(participant_url, tables_of_interest, common_slots=base_slots)   

    for table_name, table in tables.items():
        filename = outdir / f"{table_name.lower()}.csv"
        with filename.open('wt') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"')
            DdVariable.print_header(writer)

            table.print(writer)



