-- ============================================================
-- queries.sql
-- Requêtes d'agrégation sur le modèle relationnel patient_dataset
-- (à charger dans PostgreSQL / SQLite / DuckDB depuis patient_dataset.csv)
--
-- Table supposée : patients(
--   patient_id, gender, age, city, state,
--   diabetes, hypertension, bmi, systolic_bp, diastolic_bp,
--   hba1c, glucose, risk_score, risk_category
-- )
-- ============================================================

-- 1. Prévalence du diabète par tranche d'âge
SELECT
    CASE
        WHEN age < 30 THEN '18-29'
        WHEN age < 45 THEN '30-44'
        WHEN age < 60 THEN '45-59'
        WHEN age < 75 THEN '60-74'
        ELSE '75+'
    END AS tranche_age,
    COUNT(*) AS nb_patients,
    SUM(CASE WHEN diabetes THEN 1 ELSE 0 END) AS nb_diabetiques,
    ROUND(100.0 * SUM(CASE WHEN diabetes THEN 1 ELSE 0 END) / COUNT(*), 1) AS prevalence_pct
FROM patients
GROUP BY tranche_age
ORDER BY tranche_age;

-- 2. Prévalence croisée diabète / hypertension par sexe
SELECT
    gender,
    COUNT(*) AS nb_patients,
    ROUND(100.0 * SUM(CASE WHEN diabetes THEN 1 ELSE 0 END) / COUNT(*), 1) AS prevalence_diabete_pct,
    ROUND(100.0 * SUM(CASE WHEN hypertension THEN 1 ELSE 0 END) / COUNT(*), 1) AS prevalence_hta_pct,
    ROUND(100.0 * SUM(CASE WHEN diabetes AND hypertension THEN 1 ELSE 0 END) / COUNT(*), 1) AS comorbidite_pct
FROM patients
GROUP BY gender;

-- 3. Distribution des patients par catégorie de risque
SELECT
    risk_category,
    COUNT(*) AS nb_patients,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM patients), 1) AS part_pct,
    ROUND(AVG(age), 1) AS age_moyen,
    ROUND(AVG(bmi), 1) AS imc_moyen
FROM patients
GROUP BY risk_category
ORDER BY
    CASE risk_category
        WHEN 'faible' THEN 1
        WHEN 'modéré' THEN 2
        WHEN 'élevé' THEN 3
    END;

-- 4. Top villes/régions par taux de risque élevé (pour ciblage santé publique)
SELECT
    city,
    COUNT(*) AS nb_patients,
    SUM(CASE WHEN risk_category = 'élevé' THEN 1 ELSE 0 END) AS nb_risque_eleve,
    ROUND(100.0 * SUM(CASE WHEN risk_category = 'élevé' THEN 1 ELSE 0 END) / COUNT(*), 1) AS taux_risque_eleve_pct
FROM patients
GROUP BY city
HAVING COUNT(*) >= 10
ORDER BY taux_risque_eleve_pct DESC
LIMIT 15;

-- 5. Indicateurs cliniques moyens par catégorie de risque (vérification cohérence du score)
SELECT
    risk_category,
    ROUND(AVG(systolic_bp), 1) AS tension_systolique_moyenne,
    ROUND(AVG(hba1c), 2) AS hba1c_moyenne,
    ROUND(AVG(glucose), 1) AS glycemie_moyenne
FROM patients
GROUP BY risk_category;
