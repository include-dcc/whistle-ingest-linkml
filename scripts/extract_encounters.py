#!/usr/bin/env python

from pathlib import Path
import csv
from argparse import ArgumentParser, FileType

import pdb

from yaml import safe_load

PID_COLNAME = "Participant External ID"
AGE_COLNAME = "Age At Condition or Measure Observation"
FIRST_ENCOUNTER = "Age at First Patient Engagement"
FIRST_ENCOUNTER_TYPE = "First Patient Engagement Event"
LAST_ENCOUNTER = "Age at Last Vital Status"


class Encounter:
    def __init__(self, participant_id, age_at, encounter_id=None, event_type=""):
        self.participant_id = participant_id
        self.age_at = age_at
        self.encounter_id = encounter_id
        self.event_type = event_type
        self.first_encounter = False
        self.last_encounter = False

        if self.age_at == "NA":
            pdb.set_trace()
        elif self.age_at.strip() != "" and self.event_type.strip() == "":
            self.event_type = "Visit"
            if self.encounter_id.strip() == "":
                self.encounter_id = "Baseline"

    @property
    def key(self):
        return f"P{self.participant_id}-{self.age_at}"

    @property
    def id(self):
        if self.encounter_id != None:
            return self.encounter_id
        return self.age_at

    @classmethod
    def write_header(cls, writer):
        writer.writerow(
            [
                "Participant External ID",
                "Event ID",
                "Event Type",
                "Age At Event",
                "First Encounter",
                "Last Known Encounter",
            ]
        )

    def write(self, writer):
        writer.writerow(
            [
                self.participant_id,
                self.id,
                self.event_type,
                self.age_at,
                self.first_encounter,
                self.last_encounter,
            ]
        )


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
    args = parser.parse_args()

    for f in args.config:
        config = safe_load(f)
        condition_filename = config["dataset"]["condition"]["filename"]

        filedir = Path(condition_filename).parent

        encounters = {}

        # Pull Condition events out and build out our discrete event list
        with open(condition_filename, "rt") as condf:
            conditions = csv.DictReader(condf, delimiter=",", quotechar='"')

            pdb.set_trace()
            for line in conditions:
                # For actual conditions, there is no actual event, so we have
                # neither age nor event id. So, those are ignored for these
                if line[AGE_COLNAME] not in ["NA", "Not collected"]:
                    key = "-".join([line[PID_COLNAME], line[AGE_COLNAME]])
                    if key not in encounters:
                        encounters[key] = Encounter(
                            line[PID_COLNAME],
                            line[AGE_COLNAME],
                            line["Event ID"],
                            line["Event Type"],
                        )

        subject_filename = config["dataset"]["participant"]["filename"]
        with open(subject_filename, "rt") as subf:
            subjects = csv.DictReader(subf, delimiter=",", quotechar='"')
            for line in subjects:
                pid = line[PID_COLNAME]
                age1 = line[FIRST_ENCOUNTER]
                age1_type = line[FIRST_ENCOUNTER_TYPE]
                age2 = line[LAST_ENCOUNTER]

                if age1 not in ["NA", "Not collected"]:
                    k1 = "-".join([pid, age1])
                    if k1 not in encounters:
                        encounters[k1] = Encounter(pid, age1, event_type=age1_type)

                    encounters[k1].first_encounter = True

                # These won't always exist
                if age2 not in ["NA", "Not collected"]:
                    # pdb.set_trace()
                    k2 = "-".join([pid, age2])
                    if k2 not in encounters:
                        encounters[k2] = Encounter(pid, age2)
                    encounters[k2].last_encounter = True

        encounter_path = filedir / "encounter.csv"
        print(encounter_path)
        # pdb.set_trace()
        # For now, we won't worry if the file exists
        with encounter_path.open("wt") as outf:
            ewriter = csv.writer(outf, delimiter=",", quotechar='"')
            Encounter.write_header(ewriter)
            for enc in encounters:
                encounters[enc].write(ewriter)
