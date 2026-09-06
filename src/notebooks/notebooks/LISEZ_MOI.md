# Partie 4 → 9 — mode d'emploi

## Installation

Place ce dossier `notebooks/` dans `Fintech_project/`. Chaque notebook commence par :

```python
PROJET = r"C:\Users\semy4\OneDrive\Bureau\Fintech_project"
```

C'est **la seule ligne à modifier** si tu changes de machine.

```bash
pip install pandas numpy matplotlib scipy scikit-learn statsmodels
```

## Ordre d'exécution — obligatoire

| # | Notebook | Lit | Écrit |
|---|----------|-----|-------|
| 0 | `03_Construction_Panel.ipynb` | les messages scorés FinBERT + les prix | **`PANEL_SENTIMENT_WINDOWS_2020_2022_v2.csv`** |
| 1 | `04_EDA_Sentiment_Market.ipynb` | `PANEL_SENTIMENT_WINDOWS_2020_2022.csv` | figures + CSV dans `docs/` |
| 2 | `05_Features_et_Split.ipynb` | le panel | **`DATASET_MODELISATION_2020_2022.csv`** + `config_modelisation.json` |
| 3 | `06_Modeling_M1_Gap.ipynb` | le dataset + la config | `PREDICTIONS_M1_TEST.csv` |
| 4 | `07_Modeling_M2_M3.ipynb` | le dataset + la config | résultats M2/M3, backtest VaR |
| 5 | `08_Backtest.ipynb` | le dataset + la config | sensibilité aux coûts |
| 6 | `09_Synthese_Memoire.ipynb` | les CSV de `docs/` | récapitulatif |

**Le notebook 05 est bloquant** : sans lui, les 06 à 08 ne trouvent pas leur fichier d'entrée.

`04bis_Corrections_EDA.ipynb` est conservé pour mémoire (il documente les corrections apportées
à la première version de l'EDA). Le notebook **04 le remplace entièrement** : tout ce que 04bis
corrigeait est déjà intégré, avec en plus la règle de statut prédictif/contemporain corrigée.

## Ce que chaque notebook apporte

**03 — Construction du panel.** Comment on passe de 3,7 M de messages à 2 740 lignes × 76 colonnes :
conversion de fuseau horaire, calendrier de bourse déduit des prix, affectation de chaque message à un
jour et à une fenêtre, agrégation en 7 statistiques, puis toutes les variables dérivées. C'est le notebook
à lire **en premier** — il explique d'où vient chaque colonne du panel.

**04 — Partie 4 complète, reconstruite de zéro.** Anatomie des 76 colonnes, vérification des identités
comptables, statistiques descriptives, densité du corpus, prix vs sentiment, corrélations avec colonne
STATUT, quintiles intra-ticker, z-test + bootstrap par blocs, lags positifs **et négatifs**, incrément de
R² sur l'amplitude, régimes de marché, figure principale et conclusion.

**05 — Features et découpage anti-fuite.** Normalisation z-score glissante par ticker, contrôles de
marché, découpage temporel avec embargo, et **quatre tests anti-fuite** dont un test placebo sur cible
permutée. C'est le notebook à montrer si le jury demande comment tu garantis l'absence de fuite.

**06 — Modèle M1 (signe du gap).** Baselines, logistique, arbres, walk-forward, ablations, calibration,
leave-one-ticker-out, puis évaluation finale sur le test — **à ne lancer qu'une fois**.

**07 — M2 (séance) et M3 (risque).** Démonstration de l'absence de signal sur la séance **avec analyse de
puissance**, puis incrément de R² sur l'amplitude et backtest de VaR conditionnelle (test de Kupiec).

**08 — Backtest avec coûts.** Produit le **coût de break-even**, la vraie conclusion économique.

**09 — Synthèse.** Plan de rédaction chapitre par chapitre et réponses aux questions probables du jury.

## Trois anomalies détectées dans le panel actuel

Le notebook 03 les corrige toutes les trois :

1. `disp_night_full` est **entièrement vide** — les percentiles ne s'additionnent pas entre fenêtres.
2. `nabn` est **faussé sur les 20 premiers jours de chaque titre** — le dénominateur de la moyenne
   mobile est fixé à 20 même quand moins de 20 jours sont disponibles.
3. `sd_night_full` est une **moyenne pondérée d'écarts-types**, pas l'écart-type de l'union : la
   variance entre les deux sous-fenêtres est ignorée.

Aucune n'invalide les conclusions, mais mieux vaut les signaler soi-même.

Le panel reconstruit sort en `..._v2.csv` (81 colonnes : les 76 d'origine + les déciles manquants de
`overnight` et `night_full` + la cible à zone morte `y_gap_net`). Il n'écrase pas ton fichier actuel.

## Avertissement sur le notebook 06

La dernière section évalue le modèle sur le bloc de test (déc. 2021 → mars 2022), jamais utilisé
auparavant. **Ne la relance pas après avoir modifié le modèle** : à partir du deuxième passage, le test
devient une deuxième validation et le chiffre annoncé perd sa signification.
