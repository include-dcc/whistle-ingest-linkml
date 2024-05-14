#!/usr/bin/env python

from argparse import ArgumentParser, FileType
from ncpi_fhir_client.fhir_client import FhirClient
from ncpi_fhir_client.host_config import get_host_config
from collections import defaultdict
from pathlib import Path
from rich import print
import pdb
import yaml

extension_urls = {
    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race": "Race",
    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity": "Ethnicity",
}


"""When we load data into FHIR, the portal team transforms that data into a format used by the portal application. When there are issues with QA, it is often time consuming to tease out which errors are on the portal's ETL/Web code and which are in FHIR. 

We don't have time to create a comprehensive validation script, however, we can provide a set of queries that and report the counts for said queries associated with a given study. """


class Coding:
    def __init__(self, code=None, display=None, system=None):
        self.code = code
        self.display = display
        self.system = system


def parse_extension(content, result):
    """We'll extract each member of the extension array and assign it to it's
    relevant URL is recognized, we'll use the mapped value instead. If said
    URL.

    We are cheating a bit here, because we expect these are simple and
    are therefor not going to contain extensions themselves to be parsed."""

    for chunk in content:
        url = chunk["url"]
        ombvalue = None
        textval = None

        for ext in chunk["extension"]:
            if ext["url"] == "ombCategory":
                ombvalue = Coding(
                    code=ext["valueCoding"].get("code"),
                    display=ext["valueCoding"].get("display"),
                    system=ext["valueCoding"].get("system"),
                )
            elif ext["url"] == "text":
                textval = Coding(display=ext["valueString"])

        # Preference OMB over text
        if ombvalue:
            result[extension_urls[url]][ombvalue.display] += 1
        elif textval:
            result[extension_urls[url]][textval.display] += 1


def summarize_patient(host, study, result):
    qry = f"""Patient?_tag={study}"""

    patients = host.get(qry).entries
    result["patient_count"] = 0
    for patient in patients:
        patient = patient["resource"]
        result["patient_count"] += 1
        # Each patient will look like this: https://hl7.org/fhir/R4B/patient.html
        result["sex"][patient["gender"]] += 1

        # Race and ethnicity are both in extensions under different "URL"s
        # We are going to cheat by working on the assumption that extensions
        # contain race and
        parse_extension(patient["extension"], result)


def report_count(host, qry, label, result):
    entries = host.get(qry).entries

    variable_name = label
    variable_category = None

    if "." in label:
        lcomponents = label.split(".")
        variable_name = lcomponents[0]
        variable_category = lcomponents[1]
    # pdb.set_trace()
    # Should only be one entry
    if "total" in entries[0]:
        if variable_category:
            result[variable_name][variable_category] = entries[0]["total"]
        else:
            result[variable_name] = entries[0]["total"]


def exec():
    host_config = get_host_config()
    env_options = sorted(host_config.keys())

    parser = ArgumentParser(description="Quick and dirty FHIR Summary report")
    parser.add_argument(
        "--host",
        choices=env_options,
        default=None,
        required=True,
        help=f"Remote configuration to be used to access the FHIR server. If no environment is provided, the system will stop after generating the whistle output (no validation, no loading)",
    )
    parser.add_argument(
        "-s", "--study", required=True, help="Study ID to be summarized"
    )

    args = parser.parse_args()
    fhir_client = FhirClient(host_config[args.host])

    print(f"FHIR Server: {fhir_client.target_service_url}")

    # perform the necessary queries and build up the report

    # This will create a dictionary whose type is a dictionary whose
    # type is integers
    summary = defaultdict(lambda: defaultdict(lambda: 0))

    # pdb.set_trace()

    summarize_patient(fhir_client, args.study, summary)

    # perform each of the count style summaries below
    report_count(
        fhir_client,
        f"Observation?_tag={args.study}&value-concept=D21&_summary=count",
        "Down Syndrome Status.D21",
        summary,
    )
    report_count(
        fhir_client,
        f"Observation?_tag={args.study}&value-concept=T21&_summary=count",
        "Down Syndrome Status.T21",
        summary,
    )

    # Dump the summary to file
    report_path = Path("output") / "summary"

    # We'll make sure the directory does exist before trying to write to it
    report_path.mkdir(parents=True, exist_ok=True)

    # Because the defaultdict seems to be overly complex for YAML to handle,
    # we have to strip it down to a very basic dictionary. There is probaby
    # some way to clarify to it that we don't want to treat those differently,
    # but time is too limited ATM:

    # print(summary)
    final_report = {}
    for key, value in summary.items():
        if type(value) is defaultdict:
            final_report[key] = {}

            for subkey in value:
                final_report[key][subkey] = value[subkey]
        else:
            final_report[key] = value

    report_filename = report_path / f"fhir_summary_{args.study}.yaml"
    with report_filename.open("wt") as f:
        yaml.dump(final_report, f)
        print(yaml.dump(final_report))


if __name__ == "__main__":
    exec()
