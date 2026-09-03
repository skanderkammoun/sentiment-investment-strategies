# Analyse détaillée des remarques EDA → Décisions de modélisation (Notebook 05)

**Source** : commentaires ajoutés par l'utilisateur dans `src/notebooks/04_EDA_Sentiment_Market.ipynb`
**Cible** : `05_Modeling_Baselines.ipynb` (modélisation + prédiction)
**Périmètre de référence** : les **5 tickers alpha** `JPM, AMZN, TSLA, MSFT, UNH` (2 085 observations après fusion inner)

Chaque remarque est découpée en : **observation** → **implication statistique** → **mise en œuvre dans 05**.

---

## Remarque 0 — CELL 8 : « il n'y a pas des valeurs manquantes »

### Observation
Après fusion, `df_master.isnull().sum()` = 0 partout.

### Implication
C'est vrai **AVANT** la construction des features, mais **FAUX après** :
- Toute variable `shift(k)` (lag) crée **k NaN** en tête de chaque série de ticker.
- Tout `rolling(h)` crée des NaN sur les **h−1 premières lignes**.
- La cible multi-horizon `shift(−h)` crée des NaN **en fin de série**.

### Décision pour 05
1. Créer les lags **par ticker** (`groupby('Ticker').shift()`).
2. Supprimer les lignes NaN **uniquement sur les colonnes qui en contiennent** (`dropna(subset=...)`), jamais un `dropna()` global aveugle.
3. Vérifier qu'aucune ligne réelle (pas de ticker vide) ne disparaît : log `shape avant/après`.

---

## Remarque 1 — CELL 11 : Rapport statistique financier

### 1.1 Hétérogénéité d'échelle (Volume 10⁷ vs StockChange 10⁻²)
- `Volume` : moyenne **33,3 M**, σ **34,9 M** (max 318,7 M).
- `StockChange` : σ = 1,64 %, `Daily_Volatility` : moyenne 2,33 %.
- Sur les 5 alpha : volume moyen **TSLA 98,3 M vs JPM 10,0 M** (facteur ~10×).

**Décision 05** :
- **Linéaires (LogReg, SVM) + Deep Learning** : `StandardScaler` **obligatoire** (entré dans un `Pipeline` pour éviter toute fuite de scaling).
- **Arbres (RF, XGB, LGBM)** : pas de scaling nécessaire (invariance par monotone), le mettre quand même via le même `Pipeline` ne coûte rien.
- Option robuste : `RobustScaler` (médiane/IQR) pour limiter l'influence des journées de volume exceptionnelles.

### 1.2 Queues de distribution / valeurs extrêmes
- TSLA : σ rendement 2,88 % (3× BRK-B 0,89 %) ; pics de volatilité jusqu'à 22,6 %.
- `Volume_Messages` : médiane **2**, max **226** → traîne extrême à droite.
- Sur 5 alpha : quantiles rendement 1 % = **−4,6 %**, 99 % = **+5,0 %**.

**Décision 05** :
- Log-transformer les variables sociales/volumes : `log1p(Volume_Messages)`, éventuellement `log1p(Volume)` (sinon le scaling suffira).
- Garder les **événements de queue** (ne pas winsoriser) : ce sont eux que le sentiment peut anticiper ; évaluer par séparation de folds plutôt que par clipping.
- Mesurer la robustesse : comparer MCC/AUC **avec et sans** les données de forte volatilité (TSLA).

### 1.3 Asymétrie par ticker
- AAPL `skew=+1,48` (haussier), UNH `skew=−0,33` (seul asymétrie négative côté finance).
- Côté sentiment (CELL 13) : **asymétrie négative dominante** sauf BRK-B → les réactions aux mauvaises nouvelles sont plus intenses que l'enthousiasme.

**Décision 05** :
- Introduire des features **asymétriques** : décomposer le sentiment en composantes positives/négatives.
- Le CSV sentiment contient déjà `FinBERT_Positive`, `FinBERT_Negative`, `FinBERT_Neutral` → créer :
  - `Neg_Intensity = FinBERT_Negative` (amplitude baissière)
  - `Pos_Intensity = FinBERT_Positive`
  - et leurs **lags** (J-1) quand elles deviennent features.

---

## Remarque 2 — CELL 13 : Rapport de sentiment social

### 2.1 `Volume_Messages` très clairsemé et asymétrique
Sur 5 alpha : médiane **2/jour** (MSFT 1,5 !), moyenne 6,9–8,7, max 68–199.

**Décision 05** :
- `Volume_Messages` en **log1p** avant de servir de feature ; sans quoi un jour viral écrase 2 mois de signal.
- La variabilité jour-à-jour étant énorme, **cumuler** l'activité : `Volume_Messages_Smooth7 = rolling(7).mean(log1p)`.

### 2.2 Biais haussier du sentiment
- `Score_Net` moyen +0,18 (sur −1..+1) ; `Bullishness_Index` médiane 0,668.
- **Conséquence** : un `Score_Net = 0` n'est pas « neutre » mais déjà négatif relativement à la normale. Le niveau absolu est trompeur.

**Décision 05** :
- Standardiser/fixer un **niveau de référence par ticker** : `Score_Net_dev = Score_Net − median_ticker(Score_Net)` (sur fenêtre glissante passée) — transforme un niveau absolu en **sur/ sous-réaction relative**.
- Ou à défaut : `Score_Net_centered = Score_Net − Score_Net.rolling(60).mean()`.

### 2.3 TSLA : forte activité, faible adhésion (hyper-polarisation)
- Volume social élevé (7,66) mais `Score_Net` moyen faible (+0,065), σ max 0,506.
- C'est paradoxalement le ticker **le plus corrélé au rendement** (rho +0,142) : quand l'opinion se nettoie (passe de division à consensus), le cours bouge fort.

**Décision 05** :
- TSLA doit conserver ses features d'**intensité de désaccord** : `|Score_Net|`, `Polarite_Index` (fort = division), `Volume_Messages`.
- Ne pas le retirer malgré sa volatilité : il porte le signal le plus fort.

---

## Remarque 3 — CELL 16 : « on garde tous les variables »

### Observation
L'utilisateur, après la matrice de corrélation, décide de **conserver toutes les variables** (pas de suppression sur la base de la corrélation avec la cible).

### Conséquence directe pour 05
1. **Ne pas** filtrer les features par `|corr(feature, Target)| < seuil` : un ρ faible n'implique pas l'inutilité en modèle non-linéaire ou en interaction.
2. La **corrélation croisée entre features** (>0.95) reste à surveiller (cf. `Bullishness_Index` ~ `Score_Net`, ~0,7–0,85) → laisser le modèle (forêts) ou la régularisation trier, OU retirer seulement les doublons stricts.
3. Autrement dit : le **bloc complet** (finance + sentiment + lags + Δ + interactions) entre dans le modèle ; la sélection se fait par importance (RF/permutation) a posteriori, pas par seuil a priori.

---

## Remarque 4 — CELL 23 : Corrélation sentiment–rendement

### Observations chiffrées (5 alpha — recalculées)
| Ticker | ρ(Score_Net, StockChange) | ρ(Polarite, StockChange) |
|---|---|---|
| JPM   | **+0,105** | −0,017 |
| AMZN  | **+0,115** | +0,074 |
| TSLA  | **+0,142** | −0,088 |
| MSFT  | **+0,091** | −0,102 |
| UNH   | **+0,130** | −0,094 |
| **Global** | **+0,116** | — |

### Implications
1. **`Score_Net` et `Bullishness_Index` : signe positif attendu** sur les 5 alpha (effet directionnel fiable).
2. **`Polarite_Index` : signe négatif attendu** (sauf AMZN) → forte polarisation émotionnelle = séances de stress/baisse.
3. Ces deux blocs apportent de l'information **complémentaire et opposée** : les ajouter **ensemble**, jamais l'un sans l'autre, sinon la LogReg sous-estimera l'un des deux effets.

### Décision 05
- **LogReg** : vérifier le **sens des coefficients** dans le rapport d'analyse : `Score_Net` devrait être +, `Polarite_Index` devrait être −. Un signe inversé signale une fuite ou une corrélation parasite → à déboguer avant de conclure.
- Créer `Opinion_Divergence = Polarite_Index × Volume_Messages` (polarisation × participation) : proxy de « débat virulent » souvent précurseur de retournement.

---

## Remarque 5 — CELL 26 : Lag effect (LA découverte critique)

### Observations (5 alpha — recalculées)
| Lag | ρ(Score_Net décalé de k, StockChange) |
|---|---|
| **0** | **+0,116** |
| 1 | −0,014 |
| 2 | −0,016 |
| 3 | −0,012 |
| 4 | −0,007 |
| 5 | **−0,050** |

- Le signal est **contemporain** (lag 0). Dès lag 1, la corrélation tombe à ~0 voire devient légèrement négative (par ticker : JPM **−0,078**, AMZN **−0,059**).
- Conclusion de l'utilisateur (juste) : **le niveau brut du sentiment de la veille n'a quasi aucun pouvoir prédictif linéaire** sur la direction du lendemain.

### Ce que cela change fondamentalement
Le pipeline précédent utilisait `Score_Net_Lag1` comme feature reine → c'est pourquoi les MCC étaient plafonnés à ~0,08. **Il faut changer le type de features, pas seulement ajouter des modèles.**

### Décision 05 (le cœur du plan)
1. **Ne plus miser sur les niveaux retardés seuls** : les conserver (les modèles non-linéaires peuvent exploiter des effets de seuil que Pearson ne voit pas), mais **compléter par des variables de variation et d'interaction** — exactement ce que recommande ta remarque :

   - **Variables d'accélération (Δ)** — *seules vraies porteuses de signal* :
     ```
     Score_Chg1   = Score_Net_Lag1 − Score_Net_Lag2      # +0 → signal se renforce
     Score_Chg2   = Score_Net_Lag2 − Score_Net_Lag3
     Score_Accel  = Score_Net_Lag1 − 2·Score_Net_Lag2 + Score_Net_Lag3   # dérivée seconde
     Msgs_Chg1    = log1p(Volume_Messages_Lag1) − log1p(Volume_Messages_Lag2)
     Bull_Chg1    = Bullishness_Index_Lag1 − Bullishness_Index_Lag2
     ```
     Interprétation : prédire une hausse non pas parce que « hier le sentiment était bon », mais parce que **« le sentiment s'améliore »** (momentum d'opinion).

   - **Croisements volume/volatilité** (recommandé dans ta remarque) :
     ```
     Sent_x_Vol  = Score_Net_Lag1 × Daily_Volatility_Lag1
     Sent_x_Msg  = Score_Net_Lag1 × log1p(Volume_Messages_Lag1)
     Neg_x_Msg   = FinBERT_Negative_Lag1 × Volume_Messages_Lag1   # mauvaise nouvelle virale
     ```

2. **⚠️ Correction d'une fuite détectée dans l'ancien FE** :
   L'ancien code utilisait `Daily_Volatility` **du jour J** dans les interactions (`Sentiment_x_Volatility = Score_Net_Lag1 × Daily_Volatility`) — c'est **un regard en avant** : au matin de J on ne connaît pas la volatilité de J. **Tout `Daily_Volatility` feature doit être `Daily_Volatility_Lag1`** (volatilité du jour précédent, connue). Idem `Volume` → `Volume_Lag1`.

3. **Les deux stratégies possibles** (à documenter explicitement dans 05) :
   - **Stratégie « quotidienne » J-1 → J** (features toutes retardées d'au moins 1 jour) : signal linéaire faible, seule l'**accélération du sentiment** + les **non-linéarités** (RF/XGB/LSTM) peuvent produire un gain.
   - **Stratégie « intraday même-séance »** (features δ de J : `Score_Net`, `Score_Net_chg intraday`) : elle capture le ρ=+0,116 contemporain, MAIS suppose d'utiliser le sentiment agrégé **avant la clôture** → modéliser (et backtester) avec une coupure horaire, pas au niveau journalier agrééère.

---

## Synthèse : bloc de features à construire dans 05

| Bloc | Variables | Rôle |
|---|---|---|
| **A. Finance (retardées)** | `Volume_Lag1`, `Daily_Volatility_Lag1`, `Volatility_20d_Lag0` (rolling std de StockChange, shift 1), `Volume_Avg20d_Lag0` | contexte de marché **connu au matin de J** |
| **B. Sentiment, niveaux (retardés)** | `Score_Net_Lag1..5`, `Polarite_Index_Lag1..5`, `Bullishness_Index_Lag1..5`, `log1p(Volume_Messages)_Lag1..5`, `Pos/Neg_Intensity_Lag1` | persistance des niveaux (effets de seuil) |
| **C. Accélération (Δ)** | `Score_Chg1/Chg2/Accel`, `Msgs_Chg1`, `Bull_Chg1` | **signal principal prédictif** (momentum d'opinion) |
| **D. Interactions** | `Sent_x_Vol`, `Sent_x_Msg`, `Neg_x_Msg`, `Opinion_Divergence` | effets croisés (vivacité × amplitude) |
| **E. Cible (choisie pour 05)** | `Target` (binaire) ; dispo aussi `StockChange` (régression) | classification directionnelle = objectif mémoire |

### Règles de non-fuite (vérifiables dans 05)
- Aucun `StockChange`, `Daily_Volatility` **du jour J**, `Target`, `Date` dans X.
- `forbidden = ['Date','Ticker','StockChange','Target']` + tout ce qui est suffixé jour-J.
- Scaling : `StandardScaler` **fit uniquement sur train** (Pipeline `make_pipeline(StandardScaler(), model)`), jamais sur toute la série.

### Validation (données équilibrées)
- Sur 5 alpha : **50,98 %** de classe 1 → *baseline naïve* (prédire toujours 1) ≈ **50,98 %** d'accuracy, MCC=0.
- Métriques : **MCC + F1-macro + AUC** (avec classes ±équilibrées, l'accuracy devient lisible mais reste à dépasser la baseline).
- Split : `TimeSeriesSplit` walk-forward (embargo ~10 j) — **jamais de shuffle**.
- Comparaison finale : chaque modèle vs la baseline naïve ; un modèle utlilise B+C+D.

---

## Risques / pièges à surveiller dans l'implémentation 05

1. **Fuites** : `Daily_Volatility` et `Volume` du jour J (ancien FE fautif), `StockChange`, `Target` dans X.
2. **NaN de début de série** (shifts per ticker) → `dropna(subset=required_features)`.
3. **NaN de fin de série** (targets shiftés) → masque d'évaluation, pas d'erreur.
4. **Scaling par Pipeline** (jamais à la main avant split).
5. **Polarité du sentiment** : garder `Score_Net` ET `Polarite_Index` ensemble (effets opposés).
6. **TSLA** : le plus risqué ET le plus corrélé → à ne pas exclure ; surveiller son poids dans les métriques moyennes.
7. **Multi-ticker** : standardiser au global OK, mais comparer les métriques **par ticker** (un bon MCC global ne doit pas cacher TSLA seul).
8. **Message clair à intégrer** dans la conclusion 05 : « le niveau retardé du sentiment ne prédit pas la direction J+1 ; c'est **l'accélération du sentiment** et ses **interactions** avec la volatilité/le volume social qui constituent le signal ».

---

*Document généré le 30/08/2026 à partir des remarques du notebook 04.*