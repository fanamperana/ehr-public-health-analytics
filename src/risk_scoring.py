"""
risk_scoring.py
----------------
Calcule un score de risque cardio-métabolique simplifié à des fins
pédagogiques/démonstratives (NE remplace PAS un score clinique validé
tel que le score de Framingham ou SCORE2).

Le score combine : âge, IMC, tension artérielle, glycémie/HbA1c,
et présence de pathologies chroniques déjà diagnostiquées.

Usage :
    from src.risk_scoring import compute_risk_score
    df = compute_risk_score(df)
"""

import pandas as pd
import numpy as np


def _score_age(age: float) -> int:
    if pd.isna(age):
        return 0
    if age < 40:
        return 0
    if age < 55:
        return 1
    if age < 70:
        return 2
    return 3


def _score_bmi(bmi: float) -> int:
    if pd.isna(bmi):
        return 0
    if bmi < 25:
        return 0
    if bmi < 30:
        return 1
    if bmi < 35:
        return 2
    return 3


def _score_bp(systolic: float) -> int:
    if pd.isna(systolic):
        return 0
    if systolic < 130:
        return 0
    if systolic < 140:
        return 1
    if systolic < 160:
        return 2
    return 3


def _score_glucose(hba1c: float) -> int:
    if pd.isna(hba1c):
        return 0
    if hba1c < 5.7:
        return 0
    if hba1c < 6.5:
        return 1
    return 3


def compute_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute au DataFrame patient les colonnes :
    - risk_score (numérique, 0 à ~13)
    - risk_category ("faible", "modéré", "élevé")
    """
    df = df.copy()

    age_col = df["age"] if "age" in df.columns else pd.Series([np.nan] * len(df))
    bmi_col = df["bmi"] if "bmi" in df.columns else pd.Series([np.nan] * len(df))
    bp_col = df["systolic_bp"] if "systolic_bp" in df.columns else pd.Series([np.nan] * len(df))
    hba1c_col = df["hba1c"] if "hba1c" in df.columns else pd.Series([np.nan] * len(df))

    score = (
        age_col.apply(_score_age)
        + bmi_col.apply(_score_bmi)
        + bp_col.apply(_score_bp)
        + hba1c_col.apply(_score_glucose)
    )

    if "diabetes" in df.columns:
        score = score + df["diabetes"].fillna(False).astype(int) * 2
    if "hypertension" in df.columns:
        score = score + df["hypertension"].fillna(False).astype(int) * 2

    df["risk_score"] = score

    df["risk_category"] = pd.cut(
        df["risk_score"],
        bins=[-1, 3, 7, 100],
        labels=["faible", "modéré", "élevé"],
    )

    return df
