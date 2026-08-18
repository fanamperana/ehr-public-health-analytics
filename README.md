# 🏥 EHR Public Health Analytics

Analyse de santé publique à partir de données cliniques synthétiques (format FHIR),
générées avec [Synthea](https://synthetichealth.github.io/synthea/), pour identifier
les facteurs démographiques et cliniques associés aux maladies chroniques
(diabète, hypertension) et suivre l'évolution du risque dans une population simulée.

> Ce projet illustre les fondations analytiques exploitées dans mon mémoire de
> recherche sur le **Graph RAG appliqué aux dossiers patients électroniques (EHR)**,
> en transposant les mêmes données vers un cas d'usage d'analyse de santé publique
> classique (épidémiologie descriptive, stratification du risque, dashboard).

---

## 🎯 Problématique

**Quels facteurs démographiques et cliniques sont associés au risque de maladies
chroniques (diabète, hypertension) dans une population simulée, et comment ce
risque se distribue-t-il selon l'âge, le sexe et la région ?**

Ce type de question est représentatif du travail d'un analyste de données en
santé publique : croiser des données démographiques, cliniques et
temporelles pour produire des indicateurs actionnables (prévalence,
comorbidités, populations à risque) destinés à des décideurs non techniques.

## 🗂️ Structure du projet

```
ehr-public-health-analytics/
├── data/
│   └── synthea_output/        # Bundles FHIR bruts (JSON), générés par Synthea
├── notebooks/
│   ├── 01_eda_demographics.ipynb   # Exploration démographique de la cohorte
│   ├── 02_clinical_indicators.ipynb # Indicateurs cliniques (prévalence, labs)
│   └── 03_risk_analysis.ipynb       # Score de risque & segmentation
├── src/
│   ├── fhir_parser.py          # Extraction FHIR -> tables tabulaires (pandas)
│   ├── etl.py                  # Nettoyage, jointures, dataset patient unique
│   └── risk_scoring.py         # Calcul du score de risque cardio-métabolique
├── sql/
│   └── queries.sql             # Requêtes d'agrégation sur le modèle relationnel
├── dashboard/
│   └── app.py                  # Dashboard interactif Streamlit
├── reports/
│   └── synthese_executive.md   # Synthèse des résultats façon rapport décisionnel
├── tests/
│   └── test_etl.py             # Tests unitaires sur le pipeline
├── requirements.txt
└── README.md
```

## 📦 Données d'exemple incluses

Ce dépôt inclut **150 patients synthétiques** au format FHIR
(`data/synthea_output/`), générés pour que le projet fonctionne immédiatement
après clonage, sans dépendance à un téléchargement externe. La structure des
ressources (`Patient`, `Condition`, `Observation`, `Encounter`) suit le même
format que la sortie officielle de [Synthea](https://synthetichealth.github.io/synthea/).

Pour travailler avec un jeu de données Synthea plus large ou "officiel",
remplace simplement le contenu de `data/synthea_output/` par tes propres
exports Synthea (même format de bundles FHIR).

## ⚙️ Pipeline de données

1. **Génération des données** : Synthea produit des bundles FHIR par patient
   (`data/synthea_output/*.json`), incluant `Patient`, `Condition`,
   `Observation`, `Encounter`.
2. **Parsing** (`src/fhir_parser.py`) : extraction des ressources FHIR vers des
   DataFrames pandas propres (une table par type de ressource).
3. **ETL** (`src/etl.py`) : nettoyage, calcul de l'âge, jointure
   patients/conditions/observations en un dataset patient unique.
4. **Scoring** (`src/risk_scoring.py`) : calcul d'un score de risque
   cardio-métabolique simplifié à partir de l'IMC, tension, glycémie et âge.
5. **Analyse** (`notebooks/`) : exploration démographique, indicateurs
   cliniques, segmentation du risque.
6. **Restitution** (`dashboard/app.py`) : exploration interactive filtrable
   par âge, sexe, pathologie.

## 📊 Indicateurs clés produits

- Prévalence du diabète et de l'hypertension par tranche d'âge et sexe
- Taux de comorbidité (diabète + hypertension)
- Distribution des scores de risque cardio-métabolique
- Évolution des indicateurs cliniques moyens (IMC, tension, HbA1c) dans le temps
- Segmentation de la population en classes de risque (faible / modéré / élevé)

## 🔒 Éthique & confidentialité des données

Toutes les données utilisées sont **synthétiques** (générées par Synthea, aucun
patient réel). Le projet applique néanmoins les principes qu'imposerait un
contexte réel de données de santé :
- Anonymisation systématique (pas d'identifiants directs conservés au-delà du parsing)
- Documentation du traitement conforme à l'esprit du RGPD (finalité, minimisation)
- Séparation claire entre données brutes et données d'analyse

## 🚀 Installation

```bash
git clone https://github.com/<ton-username>/ehr-public-health-analytics.git
cd ehr-public-health-analytics
pip install -r requirements.txt
```

## ▶️ Utilisation

```bash
# 1. Parser les bundles FHIR et générer le dataset patient
python src/etl.py

# 2. Lancer le dashboard interactif
streamlit run dashboard/app.py
```

## 🛠️ Stack technique

- **Python** : pandas, numpy, matplotlib/plotly
- **FHIR / santé** : parsing JSON de ressources FHIR (Synthea)
- **SQL** : requêtes d'agrégation sur modèle relationnel
- **Dashboard** : Streamlit
- **Tests** : pytest

## 📌 Lien avec le mémoire de recherche

Ce dépôt réutilise le même corpus de données FHIR synthétiques que mon mémoire
de Master 2 sur l'**extension de la scalabilité du Graph RAG appliqué aux EHR**
(travaux autour de MediGRAF). Là où le mémoire explore une approche IA générative
avancée (Graph RAG, raisonnement clinique), ce projet démontre la maîtrise des
fondations analytiques classiques indispensables en amont : structuration de la
donnée clinique, indicateurs de santé publique, restitution décisionnelle.

## 👤 Auteur

Dola — Étudiant en Master 2 Ingénierie des Systèmes d'Information et Analyse de
Données (ISA), ESPA Vontovorona, Antananarivo.
