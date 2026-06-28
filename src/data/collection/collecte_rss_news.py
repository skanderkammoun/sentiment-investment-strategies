import feedparser
import pandas as pd
import logging
from pathlib import Path
import datetime
import time


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s] - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'TSLA', 'UNH', 'BRK.B', 'JPM']


SOURCES_PREMIUM = [
    'Reuters', 'Bloomberg', 'Financial Times', 'Wall Street Journal', 'CNBC', 
    'MarketWatch', 'Barron', 'Forbes', 'Yahoo Finance', 'Investing.com'
]

OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "rss_premium_news_dataset.csv"


def scraper_rss_premium():
    logger.info(" Démarrage de la collecte RSS Premium (Reuters, Bloomberg, etc.)...")
    toutes_les_news = []
    
    for ticker in TICKERS:
        logger.info(f" Scraping du flux pour {ticker}...")
        
        
        rss_url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
        
        try:
            flux = feedparser.parse(rss_url)
            
            if flux.entries:
                articles_sauves = 0
                for article in flux.entries:
                    
                    source_journal = article.get('source', {}).get('title', 'Unknown')
                    
                    
                    if any(premium_src.lower() in source_journal.lower() for premium_src in SOURCES_PREMIUM):
                        
                        
                        date_brute = article.get('published_parsed')
                        date_pub = time.strftime('%Y-%m-%d', date_brute) if date_brute else datetime.datetime.now().strftime('%Y-%m-%d')
                            
                        toutes_les_news.append({
                            'Date_Publication': date_pub,
                            'Ticker': ticker,
                            'Source': source_journal,
                            'Titre': article.get('title', ''),
                            'URL': article.get('link', '')
                        })
                        articles_sauves += 1
                        
                logger.info(f"{articles_sauves} articles PREMIUM trouvés pour {ticker}.")
            else:
                logger.warning(f"Aucun article trouvé dans le flux pour {ticker}.")
                
        except Exception as e:
            logger.error(f" Erreur lors de la lecture pour {ticker} : {e}")
            
        time.sleep(2) 


    if toutes_les_news:
        logger.info("Traitement terminé. Création du DataFrame Pandas...")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame(toutes_les_news)
        df_unique = df.drop_duplicates(subset=['Ticker', 'Titre'])
        
        try:
            df_unique.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
            logger.info(f" SUCCÈS ! {len(df_unique)} News PREMIUM sauvegardées dans : {OUTPUT_FILE}")
        except Exception as e:
            logger.error(f" Erreur d'écriture CSV : {e}")
    else:
        logger.warning("Aucune News Premium n'a été récoltée. Les sources n'ont peut-être rien publié récemment.")

if __name__ == "__main__":
    scraper_rss_premium()