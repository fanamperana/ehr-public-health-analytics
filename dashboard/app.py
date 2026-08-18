"""
app.py
------
Dashboard Streamlit d'exploration de la cohorte patient (données synthétiques).

Usage :
    streamlit run dashboard/app.py
"""

import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

st.set_page_config(page_title="EHR Public Health Analytics", layout="wide")

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "patient_dataset.csv")


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "risk_category" in df.columns:
        df["risk_category"] = pd.Categorical(
            df["risk_category"], categories=["faible", "modéré", "élevé"], ordered=True
        )
    return df


st.title("🏥 EHR Public Health Analytics")
st.caption(
    "Exploration d'une cohorte de patients synthétiques (Synthea/FHIR) — "
    "facteurs de risque cardio-métabolique et pathologies chroniques."
)

if not os.path.exists(DATA_PATH):
    st.warning(
        "Aucun dataset trouvé. Lancez d'abord :\n\n"
        "```\npython src/etl.py\n```\n\n"
        "après avoir placé des bundles FHIR Synthea dans `data/synthea_output/`."
    )
    st.stop()

df = load_data(DATA_PATH)

# --- Filtres (sidebar) ---
st.sidebar.header("Filtres")

genders = st.sidebar.multiselect(
    "Sexe", options=sorted(df["gender"].dropna().unique()), default=None
)
age_min, age_max = int(df["age"].min()), int(df["age"].max())
age_range = st.sidebar.slider("Âge", age_min, age_max, (age_min, age_max))

only_diabetes = st.sidebar.checkbox("Diabète uniquement")
only_hypertension = st.sidebar.checkbox("Hypertension uniquement")

filtered = df.copy()
if genders:
    filtered = filtered[filtered["gender"].isin(genders)]
filtered = filtered[filtered["age"].between(*age_range)]
if only_diabetes and "diabetes" in filtered.columns:
    filtered = filtered[filtered["diabetes"] == True]  # noqa: E712
if only_hypertension and "hypertension" in filtered.columns:
    filtered = filtered[filtered["hypertension"] == True]  # noqa: E712

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Patients (filtrés)", len(filtered))
if "diabetes" in filtered.columns:
    col2.metric("Prévalence diabète", f"{100 * filtered['diabetes'].mean():.1f} %")
if "hypertension" in filtered.columns:
    col3.metric("Prévalence hypertension", f"{100 * filtered['hypertension'].mean():.1f} %")
if "risk_score" in filtered.columns:
    col4.metric("Score de risque moyen", f"{filtered['risk_score'].mean():.1f}")

st.divider()

# --- Graphiques ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("Répartition par catégorie de risque")
    if "risk_category" in filtered.columns:
        fig = px.histogram(filtered, x="risk_category", color="risk_category")
        st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Distribution des âges")
    fig2 = px.histogram(filtered, x="age", nbins=20, color="gender")
    st.plotly_chart(fig2, use_container_width=True)

c3, c4 = st.columns(2)

with c3:
    st.subheader("IMC vs Tension systolique")
    if {"bmi", "systolic_bp"}.issubset(filtered.columns):
        fig3 = px.scatter(
            filtered, x="bmi", y="systolic_bp",
            color="risk_category" if "risk_category" in filtered.columns else None,
            hover_data=["age", "gender"],
        )
        st.plotly_chart(fig3, use_container_width=True)

with c4:
    st.subheader("Top villes par nombre de patients")
    if "city" in filtered.columns:
        top_cities = filtered["city"].value_counts().head(10).reset_index()
        top_cities.columns = ["city", "count"]
        fig4 = px.bar(top_cities, x="city", y="count")
        st.plotly_chart(fig4, use_container_width=True)

st.divider()
st.subheader("Données patients filtrées")
st.dataframe(filtered, use_container_width=True)
