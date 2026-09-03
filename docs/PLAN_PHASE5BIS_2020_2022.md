# 🔧 DIAGNOSTIC & PLAN DE REDÉMARRAGE — Phase 5bis
### Bascule vers le corpus StockTwits intraday 2020–2022

**Auteur :** Kammoun Skander — PFE Actuariat & Finance Quantitative
**Date :** 2 septembre 2026
**Statut :** remplace la stratégie de modélisation de `05_Modeling_Baselines.ipynb`

---

## 0. Résumé exécutif (à lire en 60 secondes)

| Question | Réponse |
|---|---|
| Pourquoi les résultats de la phase 5 sont mauvais ? | **3 causes** : densité du signal texte quasi nulle (médiane **2 messages/jour/ticker**), **mauvaise cible** (`(Close-Open)/Open`), et **absence d'horodatage** rendant la synchronisation texte↔marché impossible. |
| Le nouveau dataset (3,7 M tweets) résout-il le problème ? | **Oui, et c'est démontré chiffres à l'appui** : ρ = **+0,35** (AAPL) entre sentiment pré-ouverture et gap d'ouverture, contre ρ ≈ 0,10 dans l'ancien périmètre. |
| Dois-je scraper des prix financiers intraday (heure par heure) sur 2020-2022 ? | **NON — ce n'est pas nécessaire pour débloquer le projet.** Le bon design consiste à *agréger le texte en fenêtres calées sur la séance*, pas à descendre le prix à l'heure. C'est optionnel (Phase 8) et c'est faisable (voir §3). |
| Quelle est la vraie action à faire maintenant ? | **Redéfinir la cible** : ton sentiment nocturne prédit le **gap d'ouverture**, pas le rendement intra-séance. C'est le cœur du redémarrage. |

---

## 1. Diagnostic : pourquoi la phase 5 a échoué

### 1.1 Rappel des résultats obtenus (notebook `05_Modeling_Baselines.ipynb`)

| Modèle | F1-macro | MCC | AUC |
|---|---|---|---|
| LightGBM (meilleur) | 0,511 | **0,026** | 0,516 |
| XGBoost | 0,506 | 0,024 | 0,511 |
| LogisticRegression | 0,494 | 0,024 | 0,506 |
| RandomForest | 0,488 | −0,006 | 0,493 |
| GRU / LSTM / BiLSTM | 0,33–0,42 | 0,00–0,07 | 0,48–0,52 |
| Chronos / Chronos-MV | 0,45–0,46 | **−0,08 / −0,09** | 0,47 |

**Lecture :** MCC ≈ 0 et AUC ≈ 0,51 = **absence totale de pouvoir prédictif**. Les modèles ne
sont pas en cause (le pipeline est propre, anti-fuite, walk-forward correct). **La donnée est en cause.**

### 1.2 Cause n°1 — Le signal textuel était trop peu dense (cause principale)

Statistiques réelles de `MASTER_DATASET_ML_READY_FIXED.csv` (33 K articles → 3 798 lignes) :

| Ticker | moyenne msg/jour | **médiane** | Q75 |
|---|---|---|---|
| AAPL | 8,4 | **2** | 3 |
| AMZN | 7,0 | **2** | 3 |
| BRK-B | 4,0 | **3** | 5 |
| GOOGL | 8,4 | **2** | 3 |
| JPM | 7,7 | **2** | 10 |
| META | 8,0 | **2** | 3 |
| MSFT | 8,7 | **1,5** | 3 |
| TSLA | 8,5 | **2** | 4 |
| UNH | 8,0 | **5** | 10 |

> **79,4 % des couples (jour, ticker) reposent sur 5 messages ou moins.
> 86,7 % sur 10 ou moins.**

Conséquence statistique : `Score_Net` d'un jour est la moyenne empirique de ~2 titres.
L'erreur-type d'une moyenne vaut σ/√n ; avec n = 2 et σ ≈ 0,4, l'erreur de mesure du
sentiment quotidien est de **± 0,28**, soit **du même ordre de grandeur que le signal lui-même**.
Aucun modèle, quelle que soit son architecture, ne peut extraire un alpha d'une variable
mesurée avec un rapport signal/bruit ≈ 1. **C'était perdu d'avance.**

Avec le corpus StockTwits, le même indicateur repose sur :

| Ticker | tweets/jour (médiane) | total 2020-2022 |
|---|---|---|
| TSLA | **1 766** | 1 906 665 |
| AAPL | **910** | 904 344 |
| AMZN | **475** | 421 330 |
| META | **173** | 256 031 |
| NVDA | **136** | 222 963 |

→ **précision de mesure multipliée par ~20 à ~30** (√n passe de 1,4 à 30–42).

### 1.3 Cause n°2 — La cible choisie est la composante la moins prédictible

`StockChange = (Close − Open) / Open` a été choisie pour « éliminer le bruit nocturne ».
**C'est exactement l'inverse qu'il fallait faire.** L'information contenue dans les news et
les réseaux sociaux publiés *hors séance* est **intégrée dans le prix au moment de l'ouverture** :
elle se matérialise donc dans le **gap** `Open_J / Close_{J-1} − 1`, et **pas** dans la
séance qui suit. En supprimant le gap, tu as supprimé précisément la partie du rendement
que ton signal pouvait expliquer.

**Preuve empirique**, calculée sur le nouveau corpus (2020-01-02 → 2022-03-04, 548 jours de
bourse × 4 tickers avec prix disponibles ; fichier `data/processed/DIAG_correlations_2020_2022.csv`) :

| Feature (fenêtre) | vs **gap** `Open_J/Close_{J-1}−1` | vs **`(Close−Open)/Open`** (cible actuelle) |
|---|---|---|
| `mu_pre` (sentiment 00:00→09:30 ET) | **+0,184** | +0,003 |
| `mu_night_full` (16:00 J-1 → 09:30 J) | **+0,173** | −0,010 |
| `mu_overnight` (16:00 → 24:00 J-1) | +0,113 | −0,024 |

Détail par ticker, `mu_night_full` → **gap** :

| | AAPL | AMZN | META | TSLA |
|---|---|---|---|---|
| ρ | **+0,358** | **+0,256** | **+0,214** | **+0,302** |

Détail par ticker, `mu_night_full` → **cible actuelle** :

| | AAPL | AMZN | META | TSLA |
|---|---|---|---|---|
| ρ | −0,081 | −0,011 | +0,040 | +0,018 |

> **Conclusion sans ambiguïté :** le signal existe et il est fort (ρ jusqu'à 0,36, contre 0,10
> annoncé dans le `recap.md`). Il est simplement **sur une autre cible que celle que tu modélises**.

⚠️ À noter également : `mu_mkt` (sentiment pendant la séance 09:30–16:00) corrèle à **+0,25**
(jusqu'à +0,41 sur AMZN) avec `(Close−Open)/Open` — mais c'est une corrélation **contemporaine**,
donc **inutilisable en prédiction** en l'état. Elle devient exploitable uniquement en
décalage intra-journalier (→ Phase 8, §3).

### 1.4 Cause n°3 — L'absence d'horodatage rendait la synchronisation impossible

Sans heure de publication, tu avais deux options, toutes deux mauvaises :
- utiliser le sentiment du jour J pour prédire J → **fuite de données** ;
- décaler de J-1 à J-5 → tu **détruis le signal**, car l'effet du sentiment sur les prix se
  résorbe en quelques heures, pas en plusieurs jours. C'est exactement ce que ton EDA a
  constaté (« ρ ≈ 0 dès le lag 1 »).

`Heure_decimale` résout définitivement ce problème. La distribution horaire du corpus
confirme d'ailleurs que **l'heure est bien en Eastern Time** (pic 09:00–16:00, creux 01:00–05:00),
donc directement alignable sur la séance NYSE/NASDAQ.

---

## 2. Ce que change le nouveau périmètre 2020–2022

### 2.1 Ce que tu gagnes

1. **Densité** : 3 711 333 tweets scorés (FinBERT-tone) contre 33 059 titres.
2. **Horodatage** : synchronisation texte↔marché rigoureuse, la faiblesse n°2 du cahier des charges.
3. **Diversité de régimes** — argument fort pour la soutenance :
   - krach COVID (fév.–mars 2020),
   - rallye liquidité (avr. 2020 – 2021),
   - épisode meme-stock / retail (jan. 2021),
   - début du bear market et retournement des taux (jan.–mars 2022).
4. **Un vrai objet de recherche** : le sentiment retail intraday (StockTwits) est la source
   utilisée par la référence académique du domaine (Renault, *Journal of Banking & Finance*, 2017).

### 2.2 Ce que tu perds (à assumer explicitement dans le mémoire)

| Perte | Ampleur | Mitigation |
|---|---|---|
| Univers réduit à 5 tickers | AAPL, AMZN, META, NVDA, TSLA (MSFT, GOOGL, UNH, BRK-B, JPM sortent) | Assumer : univers « tech méga-cap à forte couverture retail ». Les 9 tickers 2023-2026 deviennent un **test de robustesse hors-échantillon** (§5.7). |
| Période : 2020-01-01 → **2022-03-05** | 26 mois, **548 jours de bourse** ≈ 2 740 lignes (5 tickers) | Comparable aux 3 798 lignes actuelles, mais chaque ligne est ~200× mieux mesurée. |
| Concentration | **TSLA = 51 %** des tweets, AAPL = 24 % | Toujours reporter les résultats **par ticker**, jamais uniquement en pooled. Pondération inverse au volume dans le portefeuille. |
| Prix quotidiens **NVDA absents** | `dataset_finance_hybride_2010_2026.csv` ne contient pas NVDA | Collecte triviale : yfinance en quotidien n'a **aucune limite d'historique** (voir étape 0). |

---

## 3. ⭐ Réponse directe à ta question : faut-il scraper des prix intraday 2020-2022 ?

### 3.1 Réponse méthodologique : non, ce n'est pas le bon réflexe

Quand une source est plus fine qu'une autre, on **agrège la fine vers la grossière** — on ne
désagrège pas la grossière. Descendre le prix à l'heure pour « matcher » le texte reviendrait
à multiplier par 7 le nombre d'observations sans ajouter d'information sur les mêmes journées,
tout en important le bruit de microstructure (bid-ask bounce, faible liquidité pré/post-marché).

Le design correct, et celui de la littérature, est :

> **texte horodaté → agrégé en fenêtres calées sur la séance → aligné sur les 3 rendements
> quotidiens naturels (gap, intra-séance, close-to-close).**

Tu obtiens ainsi **3 cibles au lieu d'une**, un test de causalité propre, et zéro donnée
supplémentaire à collecter. C'est le §4 de ce document.

### 3.2 Réponse technique : et si tu veux quand même le faire (extension Phase 8)

**yfinance ne peut pas** remonter à 2020 en intraday. Limites de l'API Yahoo :
`1m` → 30 jours d'historique (7 jours par requête), `1h` → **730 jours** (donc rien avant ~sept. 2024).
Toute tentative de contournement par scraping échouera ou violera les CGU.

Sources réellement capables de fournir 2020–2022 en intraday :

| Source | Coût | Historique | Granularité | Remarque |
|---|---|---|---|---|
| **Alpaca Market Data** | **Gratuit** (plan Free) | **7+ ans** | barres 1 min | Flux **IEX** uniquement sur le plan gratuit (~2-3 % du volume consolidé) → barres bruitées en 1 min, **acceptables en agrégat 30 min sur des méga-caps**. Plan « Algo Trader Plus » 99 $/mois pour le flux SIP complet. **Meilleur rapport coût/faisabilité pour un PFE.** |
| **Polygon.io** — Stocks Starter | ~29 $/mois | 5 ans | 1 min consolidé | Qualité institutionnelle, API simple, la référence si tu peux payer un ou deux mois. |
| **Databento** | Pay-as-you-go | complet | tick / 1 min | Facturation au volume, très propre, mais plus cher à l'usage. |
| **FirstRate Data / Kibot** | Achat unique (~50–150 $) | 15+ ans | 1 min | Fichiers plats, pas d'API — pratique pour un mémoire (téléchargement une fois). |

**Ma recommandation :** ne fais **pas** ça maintenant. Termine d'abord les §4–§5 avec les
données que tu as déjà (tu as tout). **Si** il te reste du temps avant la soutenance, ajoute
Alpaca (gratuit) pour une section « extension haute fréquence » qui testera :
*le sentiment de la demi-heure t prédit-il le rendement de la demi-heure t+1 ?* — c'est
exactement le protocole de Renault (2017) et ça fait une très belle contribution finale.

---

## 4. Plan d'action — Phase 5bis

### Étape 0 — Compléter les prix quotidiens *(30 min)*
- Collecter **NVDA** en quotidien via yfinance sur `2019-12-01 → 2022-03-31` (aucune limite en `interval='1d'`).
- Rejouer la collecte pour les 5 tickers sur cette fenêtre → `data/raw/finance_2020_2022_5T.csv`.
- Colonnes calculées : `Open, High, Low, Close, Volume` puis
  `gap = Open/Close.shift(1) − 1`, `ret_oc = (Close−Open)/Open`, `ret_cc = Close.pct_change()`.

### Étape 1 — Construire le panel de sentiment par fenêtres de séance *(le livrable clé)*
Script fourni : **`src/data/traitement/build_panel_windows_2020_2022.py`**

Fenêtres (Eastern Time, cohérentes avec `Heure_decimale`) :

| Fenêtre | Plage | Rôle |
|---|---|---|
| `overnight` | 16:00 J-1 → 24:00 J-1 | information post-clôture |
| `pre` | 00:00 J → 09:30 J | information pré-ouverture |
| **`night_full`** | **16:00 J-1 → 09:30 J** | **prédicteur du gap (signal principal)** |
| `open30` | 09:30 → 10:00 J | réaction immédiate |
| `mkt` | 09:30 → 16:00 J | contemporain — **jamais** en feature d'une cible du jour J |
| `post` | 16:00 → 24:00 J | contemporain de J, prédicteur de J+1 |

**Règle anti-fuite absolue :** pour prédire une cible qui se réalise à l'instant *t*, seules
les fenêtres **entièrement antérieures à *t*** sont autorisées.
- Cible `gap_J` (réalisée à 09:30) → autorisé : `night_full`, tout J-1 et avant.
- Cible `ret_oc_J` (réalisée à 16:00) → autorisé : `night_full`, `open30`, tout J-1 et avant. **Interdit : `mkt_J`, `post_J`.**

Statistiques par fenêtre (à calculer pour chaque couple ticker × jour) :
`n` (volume), `mu` (moyenne de `net = Pos − Neg`), `sd` (**désaccord des investisseurs** —
variable très prédictive de la volatilité), `pos_rate`, `neg_rate`, `p10`, `p90`,
`n_log`, et `n_abnormal = log(n) − moyenne mobile 20j de log(n)` (**choc d'attention**).

### Étape 2 — Redéfinir les cibles
Trois modèles, trois questions de recherche distinctes :

| Modèle | Cible | Prédicteurs autorisés | Signal attendu |
|---|---|---|---|
| **M1 — Overnight** | `sign(gap_J)` | `night_full_J`, lags J-1 | **fort** (ρ observé 0,21–0,36) |
| **M2 — Intra-séance** | `sign(ret_oc_J)` | `night_full_J`, `open30_J`, lags | faible — **c'est le résultat honnête à publier** |
| **M3 — Close-to-close** | `sign(ret_cc_J)` | `night_full_J`, `open30_J`, `post_{J-1}`, lags | intermédiaire (ρ ≈ 0,11–0,23) |

> **Argument de mémoire :** montrer que M1 fonctionne et M2 non **est un résultat scientifique
> en soi** — c'est une validation empirique de l'efficience semi-forte intra-journalière :
> l'information textuelle publique est intégrée dès l'ouverture. C'est bien plus fort qu'un
> modèle qui prédit tout à 51 %.

### Étape 3 — Feature engineering
- **Niveau** : `mu_*` par fenêtre.
- **Désaccord** : `sd_*`, `p90−p10`, `pos_rate·neg_rate` (proxy de polarisation).
- **Attention** : `n_log`, `n_abnormal` (choc de volume de messages).
- **Dynamique** : `Δmu = mu_J − mu_{J-1}`, momentum 3j/5j, accélération.
- **Interactions** : `mu × n_abnormal` (le sentiment ne compte que s'il est écouté),
  `mu × volatilité 20j`.
- **Contrôles marché** : rendement veille, volume veille, volatilité 20j, RSI, position Bollinger.
- ❌ **À bannir** : toute variable de la fenêtre `mkt_J` ou `post_J` pour une cible du jour J.

### Étape 4 — Validation
- **Walk-forward par blocs de dates** (pas par index de ligne : le panel est empilé par ticker,
  `TimeSeriesSplit` sur l'index mélange les tickers — c'est un défaut du notebook 05 à corriger).
- **Purge + embargo** de 5 jours entre train et test (protocole López de Prado).
- Métriques : **MCC**, F1-macro, AUC, + **accuracy directionnelle par ticker**.
- Baseline obligatoire : classe majoritaire, et un modèle « momentum seul, sans sentiment »
  → l'apport du sentiment se mesure **en différentiel**, c'est ça la contribution.

### Étape 5 — Modèles
Logistic (L2, interprétable, base du mémoire) → RandomForest → XGBoost/LightGBM →
GRU/LSTM sur séquences de fenêtres. Optuna sur le meilleur uniquement.
⚠️ Sur 548 jours, le deep learning surapprendra : le résultat attendu est que
**LightGBM régularisé bat les réseaux** — c'est normal et il faut le dire.

### Étape 6 — Backtesting
- **Stratégie overnight (M1)** : acheter à la clôture J-1 si `mu_night_full` > seuil,
  vendre à l'ouverture J. Coûts : **10 bps A/R + slippage**, et discuter honnêtement du
  risque de détention overnight (gaps de earnings).
- **Stratégie hybride (M3)** : sentiment + momentum, rebalancement quotidien.
- Benchmarks : Buy & Hold par ticker, portefeuille équipondéré 5 tickers, momentum pur.
- Métriques : rendement cumulé, **Sharpe**, Sortino, Max Drawdown, Calmar, hit rate,
  turnover, et **P&L net de frais** (le brut ne compte pas).

### Étape 7 — Robustesse
- Performance par sous-période : COVID (2020 T1), rallye (2020 T2–2021), meme (jan. 2021), bear (2022).
- Performance par ticker (obligatoire vu la domination TSLA).
- **Contrôle des earnings** : exclure ou marquer par une dummy les jours J-1/J d'annonce de
  résultats — sinon on attribue au sentiment ce qui vient de l'annonce.
- Test de significativité : bootstrap sur le Sharpe, test de Diebold-Mariano vs benchmark.

### Étape 8 *(optionnelle)* — Extension haute fréquence
Seulement s'il reste du temps : Alpaca (gratuit), barres 30 min 2020-2022, tester
`sentiment[t] → rendement[t+1]` en demi-heures. Réplication du protocole Renault (2017).

---

## 5. Alignement avec le cahier des charges

| Étape du cahier des charges | Statut avant | Statut après Phase 5bis |
|---|---|---|
| 1. Collecte | ✅ | ✅ + corpus StockTwits 3,7 M |
| 2. Prétraitement — **« synchronisation temporelle des données (alignement dates marché / news) »** | ⚠️ **point faible** | ✅ **résolu** : fenêtres calées sur la séance |
| 3. Analyse de sentiment (FinBERT) | ✅ | ✅ inchangé, appliqué à 3,7 M textes |
| 4. EDA — **« détection de décalages temporels (lag effect) »** | ⚠️ concluait ρ≈0 | ✅ **le lag effect est intra-journalier, pas quotidien** — découverte majeure |
| 5. Modélisation | ❌ MCC ≈ 0 | ✅ 3 cibles, signal démontré sur M1 |
| 6. Stratégies | ⏳ | ⏳ overnight + hybride |
| 7. Backtesting | ⏳ | ⏳ avec coûts et benchmarks |
| 8. Évaluation / robustesse | ⏳ | ⏳ 4 régimes de marché |

**La problématique du mémoire n'a pas besoin d'être modifiée** — elle est même mieux servie :
tu passes d'un « ça ne marche pas » à « ça marche, mais à un horizon précis et pour une
raison économique identifiée ».

---

## 6. Points de vigilance

1. **Causalité inverse.** Le sentiment overnight peut *réagir* à une annonce de résultats
   after-hours plutôt que la prédire. → dummy earnings, et vérifier que ρ tient hors jours d'annonce.
2. **Le gap n'est pas gratuit à trader.** Position overnight = risque de queue. Le backtest doit
   l'assumer et le mesurer (VaR overnight, pire drawdown journalier).
3. **Concentration TSLA (51 %).** Ne jamais présenter un résultat pooled sans le détail par ticker.
4. **2020 est un régime exceptionnel.** Un modèle entraîné sur le krach COVID ne se généralise pas.
   Traiter 2020 T1 comme un régime à part et le tester séparément.
5. **Flux IEX (si Alpaca gratuit en Phase 8)** : ~2-3 % du volume consolidé, à mentionner comme limite.
6. **Corpus arrêté au 2022-03-05.** Toute affirmation sur « 2020-2022 » doit dire 26 mois, pas 3 ans.

---

## 7. Prochaine action concrète

```bash
# 1) Compléter les prix (NVDA + fenêtre 2020-2022)
python src/data/collection/collecte_finance_2020_2022.py

# 2) Construire le panel de sentiment par fenêtres  ← script fourni
python src/data/traitement/build_panel_windows_2020_2022.py

# 3) Nouveau notebook
#    src/notebooks/06_Modeling_Overnight_2020_2022.ipynb
#    → M1 (gap) / M2 (intra) / M3 (close-close), walk-forward par dates
```

**Fichiers de preuve produits par ce diagnostic :**
- `data/processed/DIAG_correlations_2020_2022.csv` — table complète des corrélations par cible × fenêtre × ticker.
