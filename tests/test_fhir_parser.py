"""
test_fhir_parser.py
--------------------
Tests unitaires pour src/fhir_parser.py : extraction et transformation
des ressources FHIR (Patient, Condition, Observation, Encounter) en
DataFrames pandas.

Usage :
    pytest tests/test_fhir_parser.py -v
"""

import sys
import os
import json
import tempfile

import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from fhir_parser import (  # noqa: E402
    _extract_resources,
    parse_patients,
    parse_conditions,
    parse_observations,
    parse_encounters,
    parse_all_bundles,
)


# ---------------------------------------------------------------------
# _extract_resources
# ---------------------------------------------------------------------

def test_extract_resources_filters_by_type():
    bundle = {
        "entry": [
            {"resource": {"resourceType": "Patient", "id": "p1"}},
            {"resource": {"resourceType": "Condition", "id": "c1"}},
            {"resource": {"resourceType": "Patient", "id": "p2"}},
        ]
    }
    patients = _extract_resources(bundle, "Patient")
    assert len(patients) == 2
    assert all(r["resourceType"] == "Patient" for r in patients)


def test_extract_resources_empty_bundle():
    assert _extract_resources({}, "Patient") == []


# ---------------------------------------------------------------------
# parse_patients
# ---------------------------------------------------------------------

def test_parse_patients_basic_fields():
    resources = [{
        "id": "p1",
        "name": [{"given": ["Marie"], "family": "Rakoto"}],
        "gender": "female",
        "birthDate": "1990-01-01",
        "address": [{"city": "Antananarivo", "state": "Analamanga"}],
    }]

    df = parse_patients(resources)

    assert len(df) == 1
    assert df.loc[0, "patient_id"] == "p1"
    assert df.loc[0, "full_name"] == "Marie Rakoto"
    assert df.loc[0, "gender"] == "female"
    assert df.loc[0, "city"] == "Antananarivo"
    # L'âge doit être calculé automatiquement à partir de la date de naissance
    assert df.loc[0, "age"] > 30


def test_parse_patients_handles_missing_name_and_address():
    resources = [{"id": "p2", "gender": "male", "birthDate": "2000-06-15"}]
    df = parse_patients(resources)

    assert df.loc[0, "full_name"] == ""
    assert pd.isna(df.loc[0, "city"])


def test_parse_patients_empty_list_returns_empty_dataframe():
    df = parse_patients([])
    assert df.empty


# ---------------------------------------------------------------------
# parse_conditions
# ---------------------------------------------------------------------

def test_parse_conditions_extracts_patient_id_from_reference():
    resources = [{
        "subject": {"reference": "Patient/p1"},
        "code": {"coding": [{"code": "44054006", "display": "Type 2 diabetes mellitus"}]},
        "onsetDateTime": "2020-03-01",
        "clinicalStatus": {"coding": [{"code": "active"}]},
    }]
    df = parse_conditions(resources)

    assert df.loc[0, "patient_id"] == "p1"
    assert df.loc[0, "condition_label"] == "Type 2 diabetes mellitus"
    assert df.loc[0, "clinical_status"] == "active"


def test_parse_conditions_strips_urn_uuid_prefix():
    resources = [{
        "subject": {"reference": "urn:uuid:abc-123"},
        "code": {"coding": [{"code": "X", "display": "Test"}]},
    }]
    df = parse_conditions(resources)
    assert df.loc[0, "patient_id"] == "abc-123"


def test_parse_conditions_empty_list():
    df = parse_conditions([])
    assert df.empty


# ---------------------------------------------------------------------
# parse_observations
# ---------------------------------------------------------------------

def test_parse_observations_extracts_value_and_unit():
    resources = [{
        "subject": {"reference": "Patient/p1"},
        "code": {"coding": [{"code": "39156-5", "display": "Body Mass Index"}]},
        "valueQuantity": {"value": 27.5, "unit": "kg/m2"},
        "effectiveDateTime": "2023-05-10",
    }]
    df = parse_observations(resources)

    assert df.loc[0, "obs_code"] == "39156-5"
    assert df.loc[0, "value"] == 27.5
    assert df.loc[0, "unit"] == "kg/m2"


def test_parse_observations_missing_value_quantity():
    resources = [{
        "subject": {"reference": "Patient/p1"},
        "code": {"coding": [{"code": "X", "display": "Test"}]},
    }]
    df = parse_observations(resources)
    assert pd.isna(df.loc[0, "value"])


# ---------------------------------------------------------------------
# parse_encounters
# ---------------------------------------------------------------------

def test_parse_encounters_basic_fields():
    resources = [{
        "subject": {"reference": "Patient/p1"},
        "class": {"code": "ambulatory"},
        "period": {"start": "2023-01-01", "end": "2023-01-01"},
    }]
    df = parse_encounters(resources)

    assert df.loc[0, "patient_id"] == "p1"
    assert df.loc[0, "encounter_class"] == "ambulatory"
    assert pd.notna(df.loc[0, "start_date"])


def test_parse_encounters_empty_list():
    df = parse_encounters([])
    assert df.empty


# ---------------------------------------------------------------------
# parse_all_bundles (test d'intégration sur un vrai fichier)
# ---------------------------------------------------------------------

def test_parse_all_bundles_reads_json_files_from_directory():
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            {"resource": {
                "resourceType": "Patient",
                "id": "p1",
                "name": [{"given": ["Jean"], "family": "Rabe"}],
                "gender": "male",
                "birthDate": "1985-07-20",
                "address": [{"city": "Toamasina", "state": "Atsinanana"}],
            }},
            {"resource": {
                "resourceType": "Condition",
                "subject": {"reference": "Patient/p1"},
                "code": {"coding": [{"code": "59621000", "display": "Essential hypertension"}]},
            }},
        ],
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        filepath = os.path.join(tmp_dir, "bundle_test.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(bundle, f)

        patients, conditions, observations, encounters = parse_all_bundles(tmp_dir)

        assert len(patients) == 1
        assert patients.loc[0, "full_name"] == "Jean Rabe"
        assert len(conditions) == 1
        assert conditions.loc[0, "condition_label"] == "Essential hypertension"
        assert observations.empty
        assert encounters.empty


def test_parse_all_bundles_empty_directory():
    with tempfile.TemporaryDirectory() as tmp_dir:
        patients, conditions, observations, encounters = parse_all_bundles(tmp_dir)
        assert patients.empty
        assert conditions.empty
        assert observations.empty
        assert encounters.empty
