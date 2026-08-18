"""
etl.py
------
Construit un dataset "patient unique" à partir des tables FHIR parsées :
une ligne par patient, avec ses conditions chroniques (flags), ses dernières
observations cliniques (IMC, tension, glycémie) et son score de risque.

Usage :
    python src/etl.py
    -> génère data/patient_dataset.csv
"""

import os
import pandas as pd

from fhir_parser import parse_all_bundles
from risk_scoring import compute_risk_score

# Codes LOINC courants pour les observations cliniques ciblées
OBS_CODES_OF_INTEREST = {
    "39156-5": "bmi",              # Body Mass Index
    "8480-6": "systolic_bp",       # Systolic blood pressure
    "8462-4": "diastolic_bp",      # Diastolic blood pressure
    "4548-4": "hba1c",             # Hemoglobin A1c
    "2339-0": "glucose",           # Glucose
}

# Mots-clés pour flaguer les pathologies chroniques d'intérêt
CHRONIC_CONDITIONS = {
    "diabetes": ["diabetes"],
    "hypertension": ["hypertension"],
}


def flag_chronic_conditions(conditions: pd.DataFrame) -> pd.DataFrame:
    """Crée une table patient_id -> flags booléens par pathologie chronique."""
    if conditions.empty:
        return pd.DataFrame(columns=["patient_id"] + list(CHRONIC_CONDITIONS.keys()))

    conditions = conditions.copy()
    conditions["condition_label_lower"] = conditions["condition_label"].str.lower().fillna("")

    flags = conditions[["patient_id"]].drop_duplicates().set_index("patient_id")

    for flag_name, keywords in CHRONIC_CONDITIONS.items():
        mask = conditions["condition_label_lower"].apply(
            lambda label: any(k in label for k in keywords)
        )
        patient_ids_with_flag = set(conditions.loc[mask, "patient_id"])
        flags[flag_name] = flags.index.isin(patient_ids_with_flag)

    return flags.reset_index()


def latest_observations_pivot(observations: pd.DataFrame) -> pd.DataFrame:
    """
    Garde la dernière observation de chaque type d'intérêt par patient,
    et pivote en colonnes (bmi, systolic_bp, diastolic_bp, hba1c, glucose).
    """
    if observations.empty:
        return pd.DataFrame(columns=["patient_id"] + list(OBS_CODES_OF_INTEREST.values()))

    obs = observations[observations["obs_code"].isin(OBS_CODES_OF_INTEREST.keys())].copy()
    obs["metric"] = obs["obs_code"].map(OBS_CODES_OF_INTEREST)

    obs = obs.sort_values("effective_date")
    latest = obs.groupby(["patient_id", "metric"], as_index=False).last()

    pivot = latest.pivot(index="patient_id", columns="metric", values="value").reset_index()
    return pivot


def build_patient_dataset(data_dir: str = "data/synthea_output") -> pd.DataFrame:
    """Pipeline complet : parsing FHIR -> dataset patient unique avec score de risque."""
    patients, conditions, observations, _ = parse_all_bundles(data_dir)

    if patients.empty:
        raise ValueError(
            f"Aucune donnée patient trouvée dans '{data_dir}'. "
            "Placez vos bundles FHIR Synthea (*.json) dans ce dossier."
        )

    condition_flags = flag_chronic_conditions(conditions)
    obs_pivot = latest_observations_pivot(observations)

    dataset = patients.merge(condition_flags, on="patient_id", how="left")
    dataset = dataset.merge(obs_pivot, on="patient_id", how="left")

    for flag_name in CHRONIC_CONDITIONS.keys():
        if flag_name in dataset.columns:
            dataset[flag_name] = dataset[flag_name].fillna(False)

    dataset = compute_risk_score(dataset)
    return dataset


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    df = build_patient_dataset()
    output_path = "data/patient_dataset.csv"
    df.to_csv(output_path, index=False)
    print(f"Dataset patient généré : {output_path} ({len(df)} patients)")
