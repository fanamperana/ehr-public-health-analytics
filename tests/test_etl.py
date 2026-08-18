"""
test_etl.py
-----------
Tests unitaires pour les fonctions du pipeline ETL et du score de risque.
Ces tests utilisent des données factices, sans dépendre de vrais bundles FHIR.

Usage :
    pytest tests/
"""

import sys
import os
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from risk_scoring import compute_risk_score  # noqa: E402
from etl import flag_chronic_conditions, latest_observations_pivot  # noqa: E402


def test_compute_risk_score_basic():
    df = pd.DataFrame({
        "age": [25, 60, 80],
        "bmi": [22, 31, 36],
        "systolic_bp": [118, 145, 165],
        "hba1c": [5.2, 6.1, 7.5],
        "diabetes": [False, True, True],
        "hypertension": [False, False, True],
    })

    result = compute_risk_score(df)

    assert "risk_score" in result.columns
    assert "risk_category" in result.columns
    # Le score doit croître avec la sévérité des indicateurs
    assert result.loc[0, "risk_score"] < result.loc[1, "risk_score"]
    assert result.loc[1, "risk_score"] < result.loc[2, "risk_score"]
    assert result.loc[0, "risk_category"] == "faible"
    assert result.loc[2, "risk_category"] == "élevé"


def test_compute_risk_score_handles_missing_values():
    df = pd.DataFrame({
        "age": [None],
        "bmi": [None],
        "systolic_bp": [None],
        "hba1c": [None],
    })
    result = compute_risk_score(df)
    assert result.loc[0, "risk_score"] == 0
    assert result.loc[0, "risk_category"] == "faible"


def test_flag_chronic_conditions():
    conditions = pd.DataFrame({
        "patient_id": ["p1", "p1", "p2"],
        "condition_label": ["Type 2 diabetes mellitus", "Essential hypertension", "Asthma"],
    })

    flags = flag_chronic_conditions(conditions)
    flags = flags.set_index("patient_id")

    assert flags.loc["p1", "diabetes"] == True  # noqa: E712
    assert flags.loc["p1", "hypertension"] == True  # noqa: E712
    assert flags.loc["p2", "diabetes"] == False  # noqa: E712


def test_latest_observations_pivot_empty():
    empty_obs = pd.DataFrame(columns=["patient_id", "obs_code", "value", "effective_date"])
    result = latest_observations_pivot(empty_obs)
    assert "patient_id" in result.columns
    assert len(result) == 0
