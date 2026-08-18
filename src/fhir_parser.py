"""
fhir_parser.py
---------------
Parse les bundles FHIR générés par Synthea (data/synthea_output/*.json)
et les transforme en tables pandas exploitables.

Ressources FHIR extraites :
- Patient
- Condition
- Observation
- Encounter

Usage :
    from src.fhir_parser import parse_all_bundles
    patients, conditions, observations, encounters = parse_all_bundles("data/synthea_output")
"""

import json
import glob
import os
from datetime import datetime

import pandas as pd


def _load_bundle(filepath: str) -> dict:
    """Charge un fichier JSON de bundle FHIR."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_resources(bundle: dict, resource_type: str) -> list:
    """Extrait toutes les ressources d'un type donné depuis un bundle FHIR."""
    entries = bundle.get("entry", [])
    return [
        e["resource"]
        for e in entries
        if e.get("resource", {}).get("resourceType") == resource_type
    ]


def parse_patients(resources: list) -> pd.DataFrame:
    """Transforme une liste de ressources Patient FHIR en DataFrame."""
    rows = []
    for r in resources:
        name = r.get("name", [{}])[0]
        given = " ".join(name.get("given", []))
        family = name.get("family", "")
        address = r.get("address", [{}])[0]

        rows.append({
            "patient_id": r.get("id"),
            "full_name": f"{given} {family}".strip(),
            "gender": r.get("gender"),
            "birth_date": r.get("birthDate"),
            "city": address.get("city"),
            "state": address.get("state"),
            "deceased": bool(r.get("deceasedDateTime") or r.get("deceasedBoolean", False)),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
        today = pd.Timestamp(datetime.now().date())
        df["age"] = ((today - df["birth_date"]).dt.days // 365).astype("Int64")
    return df


def parse_conditions(resources: list) -> pd.DataFrame:
    """Transforme une liste de ressources Condition FHIR en DataFrame."""
    rows = []
    for r in resources:
        code = r.get("code", {})
        coding = code.get("coding", [{}])[0]
        subject_ref = r.get("subject", {}).get("reference", "")

        rows.append({
            "patient_id": subject_ref.replace("urn:uuid:", "").replace("Patient/", ""),
            "condition_code": coding.get("code"),
            "condition_label": coding.get("display") or code.get("text"),
            "onset_date": r.get("onsetDateTime"),
            "clinical_status": r.get("clinicalStatus", {})
                .get("coding", [{}])[0].get("code"),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["onset_date"] = pd.to_datetime(df["onset_date"], errors="coerce")
    return df


def parse_observations(resources: list) -> pd.DataFrame:
    """Transforme une liste de ressources Observation FHIR en DataFrame."""
    rows = []
    for r in resources:
        code = r.get("code", {})
        coding = code.get("coding", [{}])[0]
        subject_ref = r.get("subject", {}).get("reference", "")

        value = r.get("valueQuantity", {}).get("value")
        unit = r.get("valueQuantity", {}).get("unit")

        rows.append({
            "patient_id": subject_ref.replace("urn:uuid:", "").replace("Patient/", ""),
            "obs_code": coding.get("code"),
            "obs_label": coding.get("display") or code.get("text"),
            "value": value,
            "unit": unit,
            "effective_date": r.get("effectiveDateTime"),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["effective_date"] = pd.to_datetime(df["effective_date"], errors="coerce")
    return df


def parse_encounters(resources: list) -> pd.DataFrame:
    """Transforme une liste de ressources Encounter FHIR en DataFrame."""
    rows = []
    for r in resources:
        subject_ref = r.get("subject", {}).get("reference", "")
        period = r.get("period", {})

        rows.append({
            "patient_id": subject_ref.replace("urn:uuid:", "").replace("Patient/", ""),
            "encounter_class": r.get("class", {}).get("code"),
            "start_date": period.get("start"),
            "end_date": period.get("end"),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
        df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    return df


def parse_all_bundles(data_dir: str):
    """
    Parcourt tous les fichiers JSON d'un dossier, extrait les ressources
    Patient / Condition / Observation / Encounter, et retourne 4 DataFrames.
    """
    filepaths = glob.glob(os.path.join(data_dir, "*.json"))

    all_patients, all_conditions, all_observations, all_encounters = [], [], [], []

    for path in filepaths:
        bundle = _load_bundle(path)
        all_patients += _extract_resources(bundle, "Patient")
        all_conditions += _extract_resources(bundle, "Condition")
        all_observations += _extract_resources(bundle, "Observation")
        all_encounters += _extract_resources(bundle, "Encounter")

    return (
        parse_patients(all_patients),
        parse_conditions(all_conditions),
        parse_observations(all_observations),
        parse_encounters(all_encounters),
    )


if __name__ == "__main__":
    patients, conditions, observations, encounters = parse_all_bundles("data/synthea_output")
    print(f"Patients: {len(patients)}")
    print(f"Conditions: {len(conditions)}")
    print(f"Observations: {len(observations)}")
    print(f"Encounters: {len(encounters)}")
