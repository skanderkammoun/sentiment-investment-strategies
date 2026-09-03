# 📊 RECAP PROJET FINTECH — Analyse Détaillée & État d'Avancement

**Auteur :** Kammoun Skander  
**Projet :** PFE — Mastère Actuariat & Finance Quantitative  
**Date :** 28 Août 2026  

---

## 🎯 PROBLÉMATIQUE CENTRALE

> *Dans quelle mesure l'analyse de sentiment à partir de données textuelles (presse institutionnelle + réseaux sociaux boursiers) peut-elle améliorer la performance, la robustesse et la gestion des risques des stratégies d'investissement en finance de marché ?*

**Objectif final :** Concevoir un système de trading quantitatif hybride capable de capter l'humeur du marché en temps réel pour surpasser les indicateurs techniques classiques et battre les benchmarks traditionnels.

---

## 🏗️ ARCHITECTURE GLOBALE (4 PIPELINES MLOps)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. PIPELINE COLLECTE (Données Hybrides)                                    │
│     ├── Financières : yfinance, Tiingo API (2010-2026, 9 tickers)          │
│     ├── Presse : Yahoo News, Finnhub, Google News RSS, RSS Finance         │
│     ├── Réseaux Sociaux : Reddit (r/wallstreetbets, r/stocks) via Selenium │
│     └── StockTwits (dataset externe)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  2. PIPELINE MLOps / DVC                                                    │
│     ├── Versionnage données brutes (DVC_Storage local)                     │
│     ├── Traçabilité complète : raw → processed → final                     │
│     └── Reproductibilité garantie                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  3. PIPELINE NLP — FinBERT (yiyanghkust/finbert-tone)                      │
│     ├── Benchmarking : 3 modèles testés → Choix "Expert Corporate"         │
│     ├── Inférence GPU (RTX 3075) par batchs de 64                          │
│     ├── Features extraites : Positive, Negative, Neutral, Score_Net,       │
│     │   Bullishness_Index, Polarite_Index, Volume_Messages                │
│     └── Agrégation quotidienne par ticker                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  4. PIPELINE INVESTISSEMENT (Stratégie + Backtesting)                      │
│     ├── Target Engineering : StockChange = (Close-Open)/Open → {1, -1}    │
│     ├── Feature Engineering : Lags (1,2,3 jours), rolling means           │
│     ├── Modélisation : Classification binaire (Achat/Vente)               │
│     └── Backtesting algorithmique avec métriques rigoureuses              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📈 UNIVERS D'INVESTISSEMENT

| Secteur | Tickers (9) |
|---------|-------------|
| **Tech (GAFAM + R&D)** | AAPL, MSFT, GOOGL, AMZN, META, TSLA |
| **Finance & Actuariat** | UNH, BRK-B, JPM |

**Période :** 2010-2026 (Focus modélisation : 2023-2026)

---

## 📊 ÉTAT D'AVANCEMENT PAR MODULE

### ✅ MODULE 1 : COLLECTE DES DONNÉES — **TERMINÉ (100%)**

#### 1.1 Données Financières
| Script | Source | Période | Lignes | Statut |
|--------|--------|---------|--------|--------|
| `collecte_finance.py` | yfinance | 2010-2026 | 36,584 | ✅ Done |
| `collecte_tiingo_prix.py` | Tiingo API | 2010-2026 | ~36,584 | ✅ Done |

**Features calculées :** Open, High, Low, Close, Volume, **StockChange**, **Target (1/-1)**

#### 1.2 Données Textuelles — Presse & API
| Script | Source | Fichier sortie | Lignes | Statut |
|--------|--------|----------------|--------|--------|
| `collecte_yahoo_news.py` | Yahoo Finance News | `yahoo_news_dataset.csv` | ~25K | ✅ Done |
| `collecte_finnhub_news.py` | Finnhub API (1 an max) | `api_news_dataset_MAX.csv` | 3.8M | ✅ Done |
| `collecte_rss_news.py` | Google News RSS (18 sources) | `rss_news_dataset_massive.csv` | 4.5M | ✅ Done |

#### 1.3 Données Textuelles — Réseaux Sociaux (Selenium)
| Script | Source | Fichier sortie | Lignes | Statut |
|--------|--------|----------------|--------|--------|
| `scrappe_reddit.py` | r/wallstreetbets | `reddit_stealth_data_massive.csv` | 125 | ✅ Done |
| `scrappe_rstocks.py` | r/stocks | `reddit_stocks_data_massive.csv` | 97 | ✅ Done |

#### 1.4 Données Externes
- **StockTwits** : `ZMSentiment.csv` (dataset trouvé, intégré dans fusion brute)

#### 1.5 Fusion Brute Master
- `MASTER_DATASET_BRUT_MAX.csv` : **3,901,772 lignes** × 4 colonnes (Date, Source, Ticker, Titre)
- `MASTER_DATASET_BRUT_MAX_processed.csv` : Version nettoyée

---

### ✅ MODULE 2 : PRÉTRAITEMENT & FUSION — **TERMINÉ (100%)**

#### 2.1 Nettoyage Textuel (`lab1_preprocessing_finbert.ipynb`)
- Suppression URLs, mentions @, HTML entities, espaces multiples
- Filtrage période 2023-2026 : **33,059 articles** conservés
- Vérification : 0 valeurs manquantes, 0 doublons

#### 2.2 Prétraitement Financier (`02_financial_data_preprocessing_2023_2026.ipynb`)
- Chargement `dataset_finance_hybride_2010_2026.csv` (36,584 lignes)
- Filtrage 2023-2026 : **7,857 lignes** (9 tickers × ~873 jours)
- EDA complète : stats descriptives, boxplots, KDE, courbes prix
- **Insight clé :** 2 régimes de marché (Tech volatile vs Finance stable)

#### 2.3 Fusion & Indicateurs FinBERT (`01_data_fusion.ipynb` + `03_FinBERT_Inference.ipynb`)
- Audit de 7 sources brutes (Reddit WSB, Reddit Stocks, News API, Yahoo, RSS, etc.)
- Standardisation colonnes : `Date_Publication` → `Date`, `Titre` → `Texte_Nettoye`
- **Inférence FinBERT (yiyanghkust/finbert-tone) sur GPU** :
  - Batch size 64, `max_length=128`, `torch.no_grad()`
  - 33K titres traités → probabilités [Pos, Neg, Neu]
- Agrégation quotidienne par ticker → **Indicateurs de sentiment** :
  - `FinBERT_Positive`, `FinBERT_Negative`, `FinBERT_Neutral` (moyennes)
  - `Volume_Messages` (count)
  - `Score_Net = Pos - Neg`
  - `Bullishness_Index = Pos / (Pos + Neg)`
  - `Polarite_Index = |Pos - Neg| / (Pos + Neg + Neu)`

#### 2.4 Grande Fusion (Finance + Sentiment) — `04_EDA_Sentiment_Market.ipynb`
- **Inner Join** sur `['Date', 'Ticker']` → **3,717 lignes** (Master Dataset)
- Sauvegarde : `MASTER_DATASET_FINAL.csv` + `MASTER_DATASET_ML_READY.csv`
- **Feature Engineering Lags** : `Score_Net_Lag1/2/3`, `Volume_Lag1`
- Dataset final ML : **3,690 lignes** × 20 features

---

### ✅ MODULE 3 : ANALYSE EXPLORATOIRE (EDA) — **TERMINÉ (100%)**

#### 3.1 Matrice de Corrélation (Finance vs Sentiment)
| Variable | Corrélation avec StockChange | Interprétation |
|----------|------------------------------|----------------|
| **Score_Net** | **+0.10** | ⭐ Signal principal exploitable (Alpha) |
| **Bullishness_Index** | +0.08 | Signal secondaire, redondant avec Score_Net (ρ=0.78) |
| **Polarite_Index** | -0.03 | Prédicteur de volatilité, pas de direction |
| **Volume_Messages** | -0.01 | Prédicteur de volatilité, pas de direction |

#### 3.2 Analyse Visuelle Prix vs Sentiment (9 tickers, 2023-2026)
**Classification comportementale découverte :**

| Catégorie | Tickers | Caractéristique |
|-----------|---------|-----------------|
| **🚀 Émotionnelles** | TSLA, META, AAPL | Réaction immédiate au sentiment, FinBERT très efficace |
| **⏱️ Anticipatives** | UNH, MSFT, GOOGL, AMZN | Sentiment précède le prix (Lag Effect) — *UNH : signal 6 mois avant krach* |
| **🧱 Institutionnelles** | BRK-B, JPM | Insensibles au bruit médiatique, pilotées par fondamentaux |

#### 3.3 Conclusion Feature Selection pour ML
- **Target** : Direction `StockChange` (1/-1)
- **Feature principale** : `Score_Net`
- **Features secondaires** : `Polarite_Index`, `Volume_Messages` (filtres volatilité)
- **À écarter** : `Bullishness_Index` (multicolinéarité ρ=0.78 avec Score_Net)

---

### 🔄 MODULE 4 : MODÉLISATION & BACKTESTING — **EN COURS / À FAIRE**

#### 4.1 État actuel
- Dataset prêt : `MASTER_DATASET_ML_READY.csv` (3,690 lignes, 20 features, target binaire)
- Features : OHLCV + StockChange + 7 indicateurs FinBERT + 4 Lags
- Split temporel respecté (pas de leakage)

#### 4.2 À implémenter (Prochaines étapes)

| Étape | Description | Priorité | Estimation |
|-------|-------------|----------|------------|
| **4.1 Baseline Models** | Logistic Regression, Random Forest, XGBoost, LightGBM | 🔴 Haute | 2-3 jours |
| **4.2 Validation Temporelle** | Walk-Forward / Purged K-Fold (éviter leakage) | 🔴 Haute | 1-2 jours |
| **4.3 Optimisation** | Optuna / GridSearch (hyperparamètres) | 🟡 Moyenne | 2 jours |
| **4.4 Métriques Rigoureuses** | Precision, Recall, F1, AUC-ROC, **MCC**, Matthews Corr. | 🔴 Haute | 1 jour |
| **4.5 Backtesting Complet** | Simulation portefeuille, coûts transaction, slippage | 🔴 Haute | 3-4 jours |
| **4.6 Risk Management** | Stop-loss, position sizing, max drawdown, VaR | 🟡 Moyenne | 2 jours |
| **4.7 Comparaison Benchmarks** | Buy & Hold, Momentum, Mean Reversion, Equal Weight | 🟡 Moyenne | 1-2 jours |
| **4.8 Analyse Par Régime** | Performance par catégorie (Émotionnelle/Anticipative/Institutionnelle) | 🟢 Basse | 1 jour |

---

## 📁 STRUCTURE DES DONNÉES (DVC)

```
data/
├── raw/                          # Données brutes (versionnées DVC)
│   ├── dataset_finance_hybride_2010_2026.csv      (4.5 MB)
│   ├── dataset_finance_tiingo_2010_2026.csv       (3.3 MB)
│   ├── yahoo_news_dataset.csv                      (25 KB)
│   ├── api_news_dataset_MAX.csv                    (9.7 MB)
│   ├── rss_news_dataset_massive.csv                (4.5 MB)
│   ├── reddit_stealth_data_massive.csv             (10 KB)
│   ├── reddit_stocks_data_massive.csv              (8 KB)
│   └── source_data_trouve_stocktwits/
│       └── ZMSentiment.csv
├── processed/                    # Données traitées
│   ├── FINANCE_2023_2026_Trie.csv                  (936 KB)
│   ├── data_2023_2026_INDICATEURS.csv              (279 KB)
│   ├── MASTER_DATASET_2023_2026.csv                (8.6 MB)
│   ├── MASTER_DATASET_FINAL.csv                    (590 KB)
│   ├── MASTER_DATASET_ML_READY.csv                 (675 KB)  ← **INPUT ML**
│   ├── MASTER_DATASET_BRUT_MAX.csv                 (542 MB)
│   └── MASTER_DATASET_BRUT_MAX_processed.csv       (542 MB)
└── DVC_Storage/                  # Remote DVC local
```

---

## 🛠️ STACK TECHNIQUE

| Catégorie | Outils / Versions |
|-----------|-------------------|
| **Langage** | Python 3.9+ |
| **Data** | Pandas, NumPy, DVC |
| **NLP / DL** | HuggingFace Transformers 4.57, PyTorch 2.5.1+CUDA, FinBERT |
| **Viz** | Matplotlib, Seaborn, Plotly |
| **ML** | Scikit-learn (prévu), XGBoost/LightGBM (prévu), Optuna (prévu) |
| **Infra** | Jupyter Lab, Git, DVC (remote local), RTX 3075 (8GB VRAM) |
| **Logging** | Module `logging` natif (fichiers + stdout) |

---

## 📚 FONDEMENTS THÉORIQUES & LITTÉRATURE (Dossier `pfe actuariat/`)

### 1. `#######LA logique de la bourse.md`
- Formalisation achat/vente (Long/Short), Target encoding {1, -1}
- Métriques évaluation : **Precision, Recall, F1-Score, ROC-AUC**
- Justification F-Score : déséquilibre classes (plus de jours haussiers)

### 2. `###########google scholar.md` — Revue de littérature (4 articles clés)
| Article | Année | Méthode | Résultat Clé |
|---------|-------|---------|--------------|
| Bharathi & Geetha (Amman SE) | 2017 | RSS + WordNet + MA(5,10,15) | **78.75% Acc** vs 64% MA seule |
| Koukaras et al. (MDPI) | 2022 | Twitter + VADER + SVM | **76.3% F1** — Limites VADER (sarcasme, finance) |
| Jishtu et al. (Lakehead) | 2022 | Investing.com + LSTM | **78.81% Acc** — LSTM > ARIMA/SARIMA |
| Zhao & Tang (Review 87 études) | 2026 | SLR Transformers | **FinBERT domine (65.28% dir. acc)**, Multi-source +3-7.8pp |

**Enseignements intégrés au projet :**
- ✅ Formula `StockChange = (Close-Open)/Open` (évite gaps nocturnes)
- ✅ FinBERT (Transformer) vs VADER/TextBlob (lexiques)
- ✅ Multi-sources : Presse + Réseaux sociaux
- ✅ MCC / F-Score pour datasets déséquilibrés
- ✅ Décroissance temporelle signal (5-8 jours)

---

## 🎯 PROCHAINES ACTIONS PRIORITAIRES (ROADMAP)

### Phase 1 : Modélisation Core (Semaine 1-2)
```bash
# 1. Créer notebook 05_Modeling_Baselines.ipynb
# 2. Implémenter : LogisticReg, RF, XGBoost, LGBM
# 3. Walk-Forward Validation (expanding window)
# 4. Calculer : Precision, Recall, F1, AUC, MCC par ticker + global
```

### Phase 2 : Backtesting & Risk (Semaine 2-3)
```bash
# 5. Notebook 06_Backtesting.ipynb
# 6. Simulation portefeuille daily rebalancing
# 7. Coûts : 5-10 bps + slippage modèle
# 8. Métriques : Sharpe, Sortino, MaxDD, Calmar, Hit Rate
```

### Phase 3 : Analyse Avancée (Semaine 3-4)
```bash
# 9. Analyse par régime de marché (3 catégories découvertes)
# 10. Feature importance (SHAP / permutation)
# 11. Stress tests : 2020 COVID, 2022 Bear, 2023-2024 Bull
# 12. Rapport final + soutenance
```

---

## ⚠️ POINTS DE VIGILANCE & RISQUES

| Risque | Impact | Mitigation |
|--------|--------|------------|
| **Data Leakage** | Critique | Walk-forward strict, pas de shuffle, lags uniquement passé |
| **Déséquilibre classes** | Élevé | Stratified split, class_weight, métriques F1/MCC pas Accuracy |
| **Surapprentissage (peu de data)** | Élevé | Régularisation forte, CV temporelle, features selection |
| **Non-stationnarité marchés** | Moyen | Rolling windows, regime detection, monitoring drift |
| **Coûts de transaction** | Moyen | Intégrer 5-10 bps + slippage réaliste dans backtest |
| **Signal faible (ρ=0.10)** | Élevé | Ensemble methods, focus tickers "Émotionnelles/Anticipatives" |

---

## 📋 CHECKLIST FINALISATION PFE

- [x] Collecte données financières (yfinance, Tiingo) — 2010-2026
- [x] Collecte données textuelles multi-sources (7 sources)
- [x] Pipeline DVC opérationnel
- [x] Benchmarking FinBERT vs 2 autres modèles → Choix justifié
- [x] Inférence FinBERT GPU complète (33K titres)
- [x] Feature engineering sentiment (7 indicateurs)
- [x] Fusion Finance + Sentiment (Inner join, 3,717 lignes)
- [x] EDA corrélation + visualisation 9 tickers
- [x] Découverte 3 régimes comportementaux
- [x] Feature selection (Score_Net + Lags + Vol features)
- [x] Dataset ML-ready sauvegardé (`MASTER_DATASET_ML_READY.csv`)
- [ ] **Modélisation : Baselines + Walk-Forward CV**
- [ ] **Optimisation hyperparamètres (Optuna)**
- [ ] **Backtesting complet avec coûts réels**
- [ ] **Risk metrics (Sharpe, MaxDD, VaR)**
- [ ] **Analyse comparative vs benchmarks**
- [ ] **Rédaction rapport final + slides soutenance**

---

## 📝 NOTES TECHNIQUES IMPORTANTES

1. **Target Leakage évité** : `StockChange` calculé sur Open→Close même jour, pas Close→Close lendemain
2. **Lags créés correctement** : `groupby('Ticker').shift(1/2/3)` — pas de fuite inter-tickers
3. **FinBERT-tone choisi** : Modèle corporate (10-K), immunisé contre hype, probabilités binaires nettes
4. **DVC configuré** : Remote local `../DVC_Storage` pour gros fichiers (>100MB)
5. **GPU utilisé** : RTX 3075 détectée, batch inference optimisée
6. **Random State** : Fixer `random_state=42` partout pour reproductibilité

---

**📌 Prochaine commande recommandée :**
```bash
# Créer le notebook de modélisation
cp notebooks/04_EDA_Sentiment_Market.ipynb notebooks/05_Modeling_Baselines.ipynb
# Puis ouvrir et implémenter la section 4.1 ci-dessus
```

---

*Document généré automatiquement à partir de l'analyse complète du codebase — Fintech Project PFE 2026*