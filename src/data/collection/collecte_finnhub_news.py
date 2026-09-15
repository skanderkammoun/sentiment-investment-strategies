import requests
import pandas as pd
import logging
import time
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv, find_dotenv

# ==========================================
# 1. CONFIGURATION
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s] - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

env_path = find_dotenv()
load_dotenv(env_path)

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

if not FINNHUB_API_KEY:
    logger.critical(f"Clé API Finnhub introuvable. Fichier .env détecté à : {env_path}")
    sys.exit(1)

TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'TSLA', 'UNH', 'BRK.B', 'JPM']
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "api_news_dataset_MAX.csv"

# ==========================================
# 2. GESTION DU TEMPS (Le Saucissonnage)
# ==========================================
# On force la limite de 1 an exactement (limite de l'API gratuite)
DATE_FIN = datetime.today()
DATE_DEBUT = DATE_FIN - timedelta(days=365)
FORMAT_DATE = "%Y-%m-%d"

# Création de sous-périodes (fréquence mensuelle 'ME') pour éviter la troncature de l'API
date_ranges = pd.date_range(start=DATE_DEBUT, end=DATE_FIN, freq='ME').to_list()
if DATE_FIN not in date_ranges:
    date_ranges.append(DATE_FIN)

# ==========================================
# 3. FONCTION PRINCIPALE
# ==========================================
def scraper_finnhub_news_maximum():
    logger.info(f"🚀 Démarrage de l'API Finnhub (Extraction MAXIMALE : 1 an)")
    toutes_les_news = []
    
    for count, ticker in enumerate(TICKERS):
        logger.info(f"--- [{count+1}/{len(TICKERS)}] Extraction pour {ticker} ---")
        
        # On boucle sur chaque petit bloc de dates (ex: du 1er au 31 janvier)
        for i in range(len(date_ranges) - 1):
            chunk_debut = date_ranges[i].strftime(FORMAT_DATE)
            chunk_fin = date_ranges[i+1].strftime(FORMAT_DATE)
            
            logger.info(f"    -> Requête pour la période : {chunk_debut} au {chunk_fin}...")
            
            url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={chunk_debut}&to={chunk_fin}&token={FINNHUB_API_KEY}"
            
            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                news_data = response.json()
                
                if news_data and isinstance(news_data, list):
                    logger.info(f"       ✅ {len(news_data)} articles trouvés.")
                    for article in news_data:
                        timestamp = article.get('datetime')
                        date_pub = datetime.fromtimestamp(timestamp).strftime(FORMAT_DATE) if timestamp else chunk_fin
                        
                        toutes_les_news.append({
                            'Date_Publication': date_pub,
                            'Ticker': ticker,
                            'Source': article.get('source', 'Finnhub API'),
                            'Titre': article.get('headline', ''),
                            'Description': article.get('summary', ''),
                            'URL': article.get('url', '')
                        })
                else:
                    pass # Rien trouvé pour ce mois précis
                    
            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 429:
                    logger.error(f"       ⚠️ Limite de requêtes atteinte (Rate Limit). Pause de 60s...")
                    time.sleep(60) # Finnhub bloque 1 minute quand on dépasse les 60 appels
                else:
                    logger.error(f"       ❌ Erreur HTTP {response.status_code} : {http_err}")
            except Exception as e:
                logger.warning(f"       ❌ Erreur système pour {ticker} : {e}")
            
            # Finnhub autorise 60 requêtes par minute en version gratuite
            # Pause de 1.5s entre chaque mois = 40 requêtes/minute, c'est très sécurisé !
            time.sleep(1.5) 

    # ==========================================
    # 4. NETTOYAGE ET EXPORT
    # ==========================================
    if toutes_les_news:
        logger.info("Traitement terminé. Création du DataFrame Pandas...")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame(toutes_les_news)
        df = df[df['Titre'] != '']
        df_unique = df.drop_duplicates(subset=['Ticker', 'Titre', 'Date_Publication'])
        
        try:
            df_unique.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
            logger.info(f"🎉 BINGO ! {len(df_unique)} News d'API sauvegardées dans : {OUTPUT_FILE}")
        except Exception as e:
            logger.error(f"Erreur d'écriture CSV : {e}")
    else:
        logger.warning("L'API n'a rien renvoyé. Vérifiez votre clé Finnhub.")

if __name__ == "__main__":
    scraper_finnhub_news_maximum()