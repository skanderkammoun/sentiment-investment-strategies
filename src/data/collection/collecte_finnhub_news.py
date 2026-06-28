import requests
import pandas as pd
import logging
import time
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv, find_dotenv


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
OUTPUT_FILE = OUTPUT_DIR / "api_news_dataset.csv"


DATE_FIN = datetime.today()
DATE_DEBUT = DATE_FIN - timedelta(days=365)
FORMAT_DATE = "%Y-%m-%d"

str_debut = DATE_DEBUT.strftime(FORMAT_DATE)
str_fin = DATE_FIN.strftime(FORMAT_DATE)


def scraper_finnhub_news():
    logger.info(f"Démarrage de l'API Finnhub (Période : {str_debut} au {str_fin})...")
    
    toutes_les_news = []
    
    for count, ticker in enumerate(TICKERS):
        logger.info(f" [{count+1}/{len(TICKERS)}] Requête API pour {ticker}...")
        
        
        url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={str_debut}&to={str_fin}&token={FINNHUB_API_KEY}"
        
        try:
            
            response = requests.get(url, timeout=15)
            
            
            response.raise_for_status()
            
            news_data = response.json()
            
            if news_data and isinstance(news_data, list):
                logger.info(f" {len(news_data)} articles bruts extraits pour {ticker}.")
                
                for article in news_data:
                    
                    timestamp = article.get('datetime')
                    date_pub = datetime.fromtimestamp(timestamp).strftime(FORMAT_DATE) if timestamp else str_fin
                    
                    toutes_les_news.append({
                        'Date_Publication': date_pub,
                        'Ticker': ticker,
                        'Source': article.get('source', 'Finnhub API'),
                        'Titre': article.get('headline', ''),
                        'Description': article.get('summary', ''),
                        'URL': article.get('url', '')
                    })
            else:
                logger.warning(f"Aucune News trouvée pour {ticker} sur cette période.")
                
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 429:
                logger.error(f"Limite de requêtes atteinte (Rate Limit 429) sur {ticker}.")
            else:
                logger.error(f"Erreur HTTP {response.status_code} pour {ticker} : {http_err}")
        except Exception as e:
            logger.warning(f"Erreur système/réseau pour {ticker} : {e}")
        
        
        time.sleep(1.5) 

 
    if toutes_les_news:
        logger.info("Traitement terminé. Création du DataFrame Pandas...")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame(toutes_les_news)
        
       
        df = df[df['Titre'] != '']
        df_unique = df.drop_duplicates(subset=['Ticker', 'Titre'])
        
        try:
            df_unique.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
            logger.info(f"🎉 BINGO ! {len(df_unique)} News d'API sauvegardées dans : {OUTPUT_FILE}")
        except Exception as e:
            logger.error(f"Erreur d'écriture CSV : {e}")
    else:
        logger.warning(" L'API n'a rien renvoyé. Vérifiez votre clé Finnhub.")

if __name__ == "__main__":
    scraper_finnhub_news()