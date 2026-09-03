# Notebooks 04bis → 09 — mode d'emploi

## Installation

Place ce dossier `notebooks/` dans `Fintech_project/`. Chaque notebook commence par :

```python
PROJET = r"C:\Users\semy4\OneDrive\Bureau\Fintech_project"
```

C'est **la seule ligne à modifier** si tu changes de machine. Tous les autres chemins en découlent.

Dépendances : `pandas numpy matplotlib scipy scikit-learn statsmodels seaborn`

```bash
pip install pandas numpy matplotlib scipy scikit-learn statsmodels seaborn
```

## Ordre d'exécution — obligatoire

Les notebooks se passent des fichiers entre eux. Il faut les lancer dans l'ordre.

| # | Notebook | Lit | Écrit |
|---|----------|-----|-------|
| 1 | `04bis_Corrections_EDA.ipynb` | `PANEL_SENTIMENT_WINDOWS_2020_2022.csv` | figures + CSV dans `docs/` |
| 2 | `05_Features_et_Split.ipynb` | le panel | **`DATASET_MODELISATION_2020_2022.csv`** + `config_modelisation.json` |
| 3 | `06_Modeling_M1_Gap.ipynb` | le dataset + la config | `PREDICTIONS_M1_TEST.csv`, résultats M1 |
| 4 | `07_Modeling_M2_M3.ipynb` | le dataset + la config | résultats M2 et M3, backtest VaR |
| 5 | `08_Backtest.ipynb` | le dataset + la config | sensibilité aux coûts, courbes de capital |
| 6 | `09_Synthese_Memoire.ipynb` | tous les CSV de `docs/` | tableau récapitulatif |

**Le notebook 05 est bloquant** : sans lui, les notebooks 06 à 08 ne trouvent pas leur fichier d'entrée.

## Ce que chaque notebook apporte

**04bis** — corrige trois bugs de ton EDA : le tri des quintiles (qui inversait le signe du Spearman par
ticker), la p-value impossible sur 5 points, et le mélange entre corrélations prédictives et
contemporaines. Ajoute les IC par bootstrap et le test de falsification par lags négatifs.

**05** — construit les variables normalisées par ticker, le découpage temporel avec embargo, et exécute
quatre tests anti-fuite (dont un test placebo sur cible permutée). C'est le notebook à montrer si le jury
demande comment tu garantis l'absence de fuite.

**06** — modèle M1 (signe du gap) : baselines, logistique, arbres, walk-forward, ablations, calibration,
leave-one-ticker-out, puis évaluation finale sur le test — **à ne lancer qu'une fois**.

**07** — M2 (séance) : démontre l'absence de signal avec une analyse de puissance, ce qui transforme
« je n'ai rien trouvé » en « il n'y a rien au-delà de tel seuil ». M3 (risque) : incrément de R² au-delà
de la volatilité passée, et backtest de VaR conditionnelle avec test de Kupiec.

**08** — backtest close-to-open avec coûts. Produit le **coût de break-even**, qui est la vraie conclusion
économique du mémoire.

**09** — rassemble tout, propose le plan de rédaction chapitre par chapitre et les réponses aux questions
probables du jury.

## Avertissement sur le notebook 06

La dernière section évalue le modèle sur le bloc de test (déc. 2021 → mars 2022), qui n'a jamais servi
auparavant. **Ne la relance pas après avoir modifié le modèle** : à partir du deuxième passage, le test
devient une deuxième validation et le chiffre annoncé n'a plus la signification qu'on lui prête.

## Note sur les versions de scikit-learn

Le notebook 06 gère les deux API de calibration (`cv="prefit"` avant la 1.6, `FrozenEstimator` après) —
aucune adaptation nécessaire de ton côté.
