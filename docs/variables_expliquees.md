# Explication détaillée de chaque variable — Notebook 04 (EDA Sentiment & Marché)

**Projet** : Stratégies d'Investissement basées sur l'Analyse de Sentiment (FinBERT + ML)
**Notebook** : `src/notebooks/04_EDA_Sentiment_Market.ipynb`
**Objectif de ce document** : justifier, une à une, chaque variable produite ou utilisée dans le pipeline, afin de comprendre **pourquoi elle existe**, **ce qu'elle mesure**, **comment elle est calculée** et **quels sont ses risques** (fuite, redondance, interprétation).

---

## 1. Vue d'ensemble — d'où viennent les données ?

Le dataset est construit en **fusionnant deux sources** sur les clés `(Date, Ticker)` :

```
df_finance   (≈ après notebook 02)
├── Date, Ticker
├── Volume             : volume d'échanges
├── StockChange        : retour intraday
├── Target             : cible binaire
└── Daily_Volatility   : volatilité du jour

df_sentiment (≈ après FinBERT, notebook 03)
├── Date, Ticker
├── Score_Net          : score net
├── Polarite_Index     : polarité
├── Bullishness_Index  : intensité haussière
└── Volume_Messages    : nombre de messages

        ↓  fusion (merge inner) + feature engineering
   df_master → df_ml (après suppression des NaN des lags) → export ML
```

> **Point critique** : les colonnes `Open`, `High`, `Low`, `Close` ont été **supprimées** de la table finance (en accord avec l'utilisateur). Tout le code a été réécrit pour fonctionner avec `StockChange` à la place. **Aucune référence à `Close/Open/High/Low` ne doit réapparaître** (bug `KeyError` sinon).

---

## 2. Variables de marché (6 variables) — table finance

### 2.1 `Date`
- **Type** : `datetime`, clé primaire avec `Ticker`.
- **Rôle** : identifie la journée de trading ; sert au tri, aux regroupements temporels et au découpage **TimeSeriesSplit** (jamais de shuffle temporel).
- **Pourquoi** : indispensable pour l'ordre chronologique et le backtest. **Jamais utilisée comme feature** (fuite évidente).

### 2.2 `Ticker`
- **Type** : chaîne/catégoriel.
- **Rôle** : identifie le titre (ex. `JPM`, `AMZN`, `TSLA`, `MSFT`, `UNH`).
- **Pourquoi** : nécessaire pour les groupbys (normaliser par action), les régimes par titre et l'entraînement par ticker. **Jamais utilisée comme feature** (empêcherait la généralisation à d'autres titres).

### 2.3 `Volume`
- **Type** : entier positif (nombre de titres échangés).
- **Formule** : `Volume` brut du jour J.
- **Rôle** : mesure de **participation** au marché.
- **Pourquoi cette variable** :
  - Un mouvement de prix **non confirmé par le volume** est fragile ; un volume élevé donne de la **force/confiance** au signal.
  - Utilisé **en lags** (`Volume_Lag1..5`) et agrégé (`Volume_Avg20d`) pour comparer le jour J à son histoire.
- **Risque** : très hétérogène entre tickers (TSLA ≠ JPM) → toutes les dérivées doivent être calculées **par ticker** (groupby).

### 2.4 `StockChange`
- **Type** : réel (exprimé en fraction, ~±0.1).
- **Formule** :
  ```
  StockChange = (Close − Open) / Open
  ```
  (retour **intraday** : seul un retour calculable AVANT l'ouverture du lendemain).
- **Rôle** : **cible continue** du problème. Il remplace avantageusement `Close` puisque les OHLC ont été supprimées.
- **Pourquoi cette variable** :
  - C'est le **signal à prédire** (direction et amplitude).
  - Il sert de base à la cible binaire `Target`, aux targets multi-horizons, et à toutes les features prix (RSI, Bollinger, momentum).
- **Risque / règle d'or** : `StockChange` est la cible → il ne doit **jamais** apparaître dans les features `X` (fuite directe). Il est gardé dans les exports **uniquement pour le backtest** (`_FIXED.csv`).

### 2.5 `Target`
- **Type** : binaire `{0, 1}`.
- **Formule** :
  ```
  Target = 1 si StockChange > 0 (hausse intraday), sinon 0
  ```
- **Rôle** : cible principale de classification.
- **Pourquoi** : transforme un problème de régression (difficile et bruyant) en problème de **direction**, la question réellement posée par l'investisseur (« monte ou descend ? »).

### 2.6 `Daily_Volatility`
- **Type** : réel ≥ 0.
- **Rôle** : amplitude de variation du jour (fournie par le provider / notebook 02).
- **Pourquoi** :
  - Contexte de **risque** : un même sentiment n'a pas le même impact dans un marché calme vs agité.
  - Utilisé en interaction (`Sentiment_x_Volatility`).
- **Remarque** : distinct de `Volatility_20d` (historique glissant), c'est la volatilité **du jour courant**.

---

## 3. Variables de sentiment brut (4 variables) — table FinBERT

### 3.1 `Score_Net`
- **Type** : réel (≈ entre −100 et +100, moyenné sur les posts du jour).
- **Formule** : moyenne des scores individuels FinBERT (−1..+1) ramenée à une échelle, ou agrégation réseau.
- **Rôle** : **direction du sentiment** — le signal principal du projet.
- **Pourquoi** : résume « le marché est-il globalement positif ou négatif aujourd'hui ? ». C'est l'hypothèse centrale : le sentiment Reddit prédit la direction du marché.

### 3.2 `Polarite_Index`
- **Type** : réel entre 0 et 1 (ou −1..1).
- **Rôle** : **netteté / tranchant** du sentiment (les posts sont-ils clairement positifs/négatifs, ou mitigés ?).
- **Pourquoi** : un `Score_Net = 0` peut signifier « pas d'opinion » ou « 50 % pour / 50 % contre ». La polarité distingue ces deux cas → améliore l'interprétation.

### 3.3 `Bullishness_Index`
- **Type** : réel.
- **Formule** : proportion/intensité des messages haussiers sur la journée.
- **Rôle** : **intensité haussière** (indépendamment du Score_Net).
- **Pourquoi** : corrélé à `Score_Net` (~0.7–0.85) mais **conservé** car il mesure la *vigueur* de l'opinion haussière, pas seulement son solde. On ne le retire que si la corrélation dépasse **0.95** (seuil de la feature selection).

### 3.4 `Volume_Messages`
- **Type** : entier ≥ 0 (nombre de messages analysés le jour J).
- **Rôle** : **participation / conviction collective**.
- **Pourquoi** : le *degré de certitude* d'un signal dépend du nombre de voix. Un score fort sur 5 messages ≠ score fort sur 500. Utilisé en lags et en interaction (`Sentiment_Strength`).

---

## 4. Variables de décalage temporel — les LAGS (20 variables)

**Cellule** : `feature-engineering-code`

```
lag_cols = ['Score_Net', 'Volume_Messages', 'Volume', 'Polarite_Index', 'Bullishness_Index']
lag_periods = [1, 2, 3, 5]

→ Score_Net_Lag1, Score_Net_Lag2, Score_Net_Lag3, Score_Net_Lag5
→ Volume_Messages_Lag1..5
→ Volume_Lag1..5
→ Polarite_Index_Lag1..5
→ Bullishness_Index_Lag1..5
```

- **Formule générique** : `X_Lagk = X.shift(k)` **par ticker** (groupby), c'est-à-dire la valeur de k jours avant.
- **Raison d'être fondamentale** :
  - Le sentiment du jour **J n'est connu qu'à la fin de la séance J**. Pour prédire la direction de **J+1**, on ne peut utiliser que l'information de **J−1 et avant**.
  - Sans lags → **fuite de données** (le modèle « voit » le futur). Avec lags → la prédiction utilisée en production est **réalisable** (utilisable en réel).
- **Pourquoi 4 horizons (1, 2, 3, 5)** : le sentiment a une **persistance temporelle** — l'effet d'une actualité se diffuse sur plusieurs jours et décroît. Multiplier les horizons laisse le modèle choisir la vitesse de décroissance (autorégressif).
- **Pourquoi `Volume` en lag** : décision ajoutée lors de la correction — le volume du jour passé reste un signal de momentum d'activité utilisable.
- **Risques** :
  - Chaque lag ajoute des NaN en tête de série (résolus par le `dropna` de `clean-dropna-code`).
  - Corrélés entre eux par construction (Lag1 vs Lag2) → gérés par la feature selection (seuil 0.95).

---

## 5. Variables de contexte / agrégats (2 variables)

### 5.1 `Volatility_20d`
- **Formule** : `std rolling(20 jours, min_periods=5)` de `StockChange`, **shift(1)** (par ticker).
- **Rôle** : volatilité « normale » du titre sur 20 séances.
- **Pourquoi** :
  - **Normalisation** : permet de juger si la volatilité d'aujourd'hui est inhabituelle.
  - Base du régime de marché (`Vol_Regime`) et de la feature d'interaction.
  - Le `shift(1)` évite la fuite (on n'utilise que le passé).

### 5.2 `Volume_Avg20d`
- **Formule** : `mean rolling(20 jours, min_periods=5)` de `Volume`, **shift(1)** (par ticker).
- **Rôle** : volume « de croisière » du titre.
- **Pourquoi** : sert de **référence** pour détecter une activité anormale (`Volume_Trend`) et pour pondérer l'impact du sentiment (`Sentiment_x_Volume`).

---

## 6. Variables d'interaction sentiment × marché (5 variables)

**Cellule** : `23382963` (feature engineering avancé).

### 6.1 `Sentiment_x_Volatility`
- **Formule** : `Score_Net_Lag1 × Daily_Volatility`.
- **Pourquoi** : le même sentiment agit **proportionnellement plus fort** quand le marché est volatile. C'est une non-linéarité : plutôt que de forcer le modèle à la découvrir, on la lui fabrique.

### 6.2 `Sentiment_x_Volume`
- **Formule** : `Score_Net_Lag1 × Volume_Avg20d`.
- **Pourquoi** : un sentiment positif accompagné d'un volume élevé = **validation par le marché** (les baissiers et haussiers investissent réellement).

### 6.3 `Sentiment_Strength`
- **Formule** : `Score_Net_Lag1 × Volume_Messages_Lag1`.
- **Pourquoi** : **conviction pondérée** — le score du jour multiplié par le nombre de voix. Évite qu'un score fort fondé sur 2 messages pèse autant qu'un score équivalent fondé sur 500.

### 6.4 `Sentiment_Momentum_3d`
- **Formule** : `Score_Net_Lag1 − Score_Net_Lag3`.
- **Pourquoi** : capture la **dérive** (« le sentiment s'améliore ou se dégrade ? ») plutôt que le niveau. Un niveau déjà haut peut stagner ; la dérive signale un **changement de régime** imminent.

### 6.5 `Sentiment_Acceleration`
- **Formule** : `Score_Net_Lag1 − 2 × Score_Net_Lag2 + Score_Net_Lag3`.
- **Pourquoi** : c'est la **dérivée seconde** (accélération). Détecte une **accélération** du sentiment (euphorie ou panique naissantes), complémentaire du momentum.

---

## 7. Variables de régime & momentum du prix (5 variables)

### 7.1 `Vol_Regime`
- **Formule** :
  ```
  Vol_Regime = pd.qcut(Volatility_20d, q=3, labels=['Low','Med','High'])
  → encodé 0/1/2
  ```
- **Type** : ordinal discret (0 = calme, 1 = normal, 2 = tempête).
- **Pourquoi** : les règles de trading ne sont pas les mêmes par régime (périodes calmes → mean reversion ; périodes agitées → tendances). Donner ce contexte au modèle réduit la variance des prédictions.

### 7.2 `Return_Momentum_5d`
- **Formule** : `mean rolling(5)` de `StockChange` (par ticker).
- **Pourquoi** : **momentum de prix** classique — les mouvements **tendent à se poursuivre** à court terme. On utilise `StockChange` (ratio) plutôt que `Close` car la série est normalisée et stationnaire.

### 7.3 `Return_1d`
- **Formule** : alias de `StockChange` (déjà présent, conservé pour la clarté du code).
- **Pourquoi** : explicite que le retour du jour fait partie de l'historique de momentum.

### 7.4 `Return_5d`
- **Formule** : `sum rolling(5)` de `StockChange` (par ticker).
- **Pourquoi** : retour **cumulé** sur 5 jours — version plus lissée du momentum, sert de contraste avec la moyenne glissante (endroit vs moyenne).

### 7.5 `Volume_Trend`
- **Formule** : `Volume_Avg20d / mean rolling(10) de Volume_Avg20d`.
- **Pourquoi** : ratio **> 1** = activité en augmentation, **< 1** = en diminution. Détecte les **surrections d'activité** (catalyseurs, annonces, débats Reddit virulents) souvent précurseurs de mouvements.

---

## 8. Indicateurs techniques sur `StockChange` (6 variables)

> Ces indicateurs sont classiquement calculés sur `Close` ; ils ont été **réécrits sur `StockChange`**, faute de colonnes OHLC. Ils perdent le niveau de prix mais conservent la dynamique relative (momentum, mean reversion).

### 8.1 `RSI_14`
- **Formule** (RSI simplifié sur `StockChange`, fenêtre 14) :
  ```
  delta   = StockChange.diff()
  gain    = moyenne(delta si delta > 0, sinon 0)
  perte   = moyenne(−delta si delta < 0, sinon 0)
  RS      = gain / perte
  RSI     = 100 − 100/(1 + RS)
  ```
- **Rôle** : oscille ≈ 0–100 ; **> 70** sur-achat, **< 30** sur-vente.
- **Pourquoi** : détecte les mouvements **excessifs** (probables retournements) — complémentaire du momentum (qui suit la tendance).

### 8.2 `BB_Middle`
- **Formule** : `mean rolling(20)` de `StockChange`.
- **Rôle** : centre des bandes = la « juste valeur » mécanique du mouvement.

### 8.3 `BB_Std`
- **Formule** : `std rolling(20)` de `StockChange`.
- **Rôle** : largeur des bandes = volatilité récente (base des bornes).

### 8.4 `BB_Upper` / `BB_Lower`
- **Formule** : `BB_Middle ± 2 × BB_Std`.
- **Rôle** : bornes statistiques (±2σ) du mouvement attendu.

### 8.5 `BB_Position`
- **Formule** :
  ```
  (StockChange − BB_Lower) / (BB_Upper − BB_Lower)
  ```
- **Rôle** : position **relative** du jour dans les bandes (0 = bordure basse, 1 = bordure haute).
- **Pourquoi** : une variable **normalisée** (même échelle pour tous les tickers), fournissant à la fois mean reversion (près de 0/1) et niveau de tension. Plus utile au ML que les bandes brutes.

---

## 9. Variables cibles — TARGETS (7 variables)

**Cellule** : `target-engineering-code`

| Variable | Type | Formule | But |
|---|---|---|---|
| `Target` | binaire | `(StockChange > 0)` | cible principale de classification |
| `Target_H1` | binaire | `sum rolling(1 → shift(−1)) > 0` | direction au jour **J+1** |
| `Target_H3` | binaire | `sum rolling(3 → shift(−3)) > 0` | direction cumulée J+1→J+3 |
| `Target_H5` | binaire | `sum rolling(5 → shift(−5)) > 0` | direction cumulée sur 5 jours |
| `Target_H10` | binaire | `sum rolling(10 → shift(−10)) > 0` | direction cumulée sur 10 jours |
| `Target_Asym` | binaire | `1 si StockChange > 0 sinon 0` | identique à `Target`, gardé pour comparer l'asymétrie gain/perte |
| `Target_Return` | continu | `= StockChange` | problème de **régression** (amplitude + direction) |
| `Target_Volatility` | continu | `= Daily_Volatility` | prédire **l'amplitude** (pas la direction) |

- **Pourquoi multi-horizons** : tester **à quel horizon** le sentiment prédit le marché (1 j ? 1 semaine ?). Un sentiment peut réagir lentement ; les lags (1-5 j) s'harmonisent avec les horizons H1-H5.
- **Pourquoi multi-tâches** : la classification (direction) a une métrique instable (MCC faible) ; la **régression** et la **volatilité** donnent des visions complémentaires et des métriques plus fines (RMSE, R²).
- **Risque** : `rolling(h).sum().shift(−h)` crée des NaN en queue de série (derniers h jours) → **attention au dernier bloc** lors du backtest (ne pas prédire l'inconnu).

---

## 10. Variable indépendante du ML : la FEATURE SELECTION

**Cellule** : `feature-selection-code`

- `drop_cols_fs = ['Date', 'Ticker', 'Target', 'StockChange']` → **uniquement** les clés et les cibles sont exclues. **`Volume` et `Daily_Volatility` restent candidats**.
- Méthodes :
  1. **Random Forest importance** (100 arbres, class_weight balanced) : hiérarchise les features.
  2. **Mutual Information** : capture les relations **non linéaires** (complémentaire de RF).
  3. **Suppression MI < 0.001** : élimine le bruit pur.
  4. **Corrélation > 0.95** : supprime les doublons (ex. `Sentiment_x_Volatility` très corrélé à une de ses composantes) → garde un representant.
- `final_features` sont **sauvegardées** dans `data/processed/feature_set.json` pour la **reproductibilité** (le notebook 05 doit charger ce fichier et non re-calculer).

---

## 11. Export & cohérence des jeux de données

- `dataset-export-code` → `MASTER_DATASET_FULL_FEATURES_v2.csv` (features complètes) + `TARGETS_ALL_HORIZONS.csv` (tous les targets).
- `export-code` → `MASTER_DATASET_ML_READY_FIXED.csv` : **référence pour le notebook 05**, contient `Date, Ticker, Target, feature_cols…, StockChange` (**StockChange conservé pour backtest uniquement**).
- **Règle absolue** : ne **jamais** retirer `StockChange` des colonnes avant la visualisation/backtest (sinon `KeyError: 'StockChange'`). Le recréer si besoin : `StockChange = (Close−Open)/Open`.

---

## 12. Points d'attention / pièges (à garder en tête)

1. **Fuite temporelle** : lags **obligatoires** pour tout le sentiment ; `shift(1)` sur les agrégats ; TimeSeriesSplit pour l'évaluation.
2. **Ne pas utiliser le jour courant comme feature** : `Score_Net` (non laggé) existe dans `df_master` mais la **véritable feature prédictive est `Score_Net_Lag1`** — si on entraîne sur le jour courant, on « triche » sur le timing intraday. À vérifier dans `features finales` : tout sentiment doit être en Lag≥1.
3. **`Close` n'existe plus** — tout calcul se fait sur `StockChange`. Documenter l'interprétation (RSI/BB perdent le niveau absolu de prix).
4. **Échelle par ticker** : tout rolling/groupby doit se faire **par ticker** (sinon mélange JPM/TSLA).
5. **Qcut** : `pd.qcut` exige assez de données par ticker ; si erreur "Bin edges must be unique", regrouper les tickers ou réduire q.
6. **NaN de queue** : les targets shift(−h) et les lags laissent des NaN → `dropna` ou masque ; le dernier bloc (h jours) est **imprédictible**.
7. **Corrélations** : `Bullishness_Index` vs `Score_Net` (~0.85) est **accepté** (mesures différentes) ; au-delà de **0.95**, la feature selection les gère.

---

*Document généré le 30/08/2026 — à mettre à jour si le pipeline change.*