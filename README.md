# 📊 Stratégies d'Investissement Basées sur l'Analyse de Sentiment et les Données Textuelles

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![DVC](https://img.shields.io/badge/Data_Version_Control-DVC-🚀-hf?color=9cf)](https://dvc.org/)
[![Git](https://img.shields.io/badge/Version_Control-Git-orange.svg)](https://git-scm.com/)
[![Framework](https://img.shields.io/badge/NLP-FinBERT%20%7C%20Transformers-red)](https://huggingface.co/prosusai/finbert)

> **Projet de Fin d'Études (PFE) — Mastère en Actuariat & Finance Quantitative** > **Auteur :** Kammoun Skander  
 

---

## 📌 Présentation du Projet & Problématique

Ce projet de recherche appliquée se positionne à l'intersection de la **Finance de Marché**, du **Traitement Automatique du Langage Naturel (NLP)** et du **MLOps**. 

### 🔍 Problématique
> *Dans quelle mesure l’analyse de sentiment à partir de données textuelles (presse institutionnelle et réseaux sociaux boursiers) peut-elle améliorer la performance, la robustesse et la gestion des risques des stratégies d’investissement en finance de marché ?*

L'objectif principal est de concevoir un système de trading quantitatif hybride capable de capter l'humeur du marché en temps réel afin de surpasser les indicateurs financiers techniques classiques et de battre les benchmarks traditionnels.

---

## 🏗️ Architecture Globale du Système (Pipeline MLOps)

Le projet est conçu selon les standards industriels les plus exigeants de l'ingénierie IA, articulé autour de 4 grands pipelines :

1. **Pipeline de Collecte (Données Hybrides) :** Extraction asynchrone des métriques financières et des flux textuels.
2. **Pipeline MLOps (DVC) :** Versionnage strict des grands volumes de données.
3. **Pipeline NLP (Analyse de Sentiment) :** Extraction des scores de polarité via des architectures de Deep Learning spécialisées (FinBERT).
4. **Pipeline d'Investissement (Stratégie) :** Génération des signaux d'achat/vente (Classification) et exécution du backtesting algorithmique.

---

## 📊 Univers d'Investissement & Dictionnaire des Données

Afin de garantir une diversification optimale tout en conservant une liquidité institutionnelle, l'univers d'investissement est composé de 9 actifs majeurs cotés sur les marchés américains (2010 - Présent) :

* **Secteur Technologique (GAFAM & R&D) :** `AAPL`, `MSFT`, `GOOGL`, `AMZN`, `META`, `TSLA`.
* **Secteur Financier & Actuariat (Piliers) :** `UNH` (UnitedHealth Group), `BRK-B` (Berkshire Hathaway), `JPM` (JPMorgan Chase).

### 📐 Variables Cibles (Target Engineering)
Pour isoler les réactions intraday nettes et éliminer le bruit nocturne ("gaps" d'ouverture), le modèle utilise la formule mathématique de la variation Intra-day :

StockChange = (Close - Open) / Open

Le signal cible est modélisé sous forme de classification binaire :
* **Signal Achat (1) :** StockChange > 0
* **Signal Vente (-1) :** StockChange <= 0

---

## 🛠️ Stack Technique & Excellence Ingénierie

Le projet applique des règles de production strictes (Enterprise Level) :
* **Développement :** Python 3.9+, Pandas, NumPy, Scikit-Learn.
* **Deep Learning & NLP :** Hugging Face `transformers`, PyTorch, FinBERT.
* **Gestion des Données & Traçabilité :** * **Logging Professionnel :** Utilisation du module `logging` natif.
  * **DVC (Data Version Control) :** Intégration de DVC pour stocker de façon sécurisée les fichiers de données bruts de grande taille en dehors de GitHub.