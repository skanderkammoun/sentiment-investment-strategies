import feedparser
import pandas as pd
import logging
from pathlib import Path
import datetime
import time
from urllib.parse import quote

# ==========================================
# 1. CONFIGURATION DU LOGGING
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s] - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ==========================================
# 2. CONSTANTES ET SOURCES ÉLARGIES
# ==========================================
TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'TSLA', 'UNH', 'BRK.B', 'JPM']

# Élargissement massif : Ajout des géants de la finance et du sentiment Retail
SOURCES_FINANCE = [
    'Reuters', 'Bloomberg', 'Financial Times', 'Wall Street Journal', 'CNBC', 
    'MarketWatch', 'Barron', 'Forbes', 'Yahoo Finance', 'Investing.com',
    'Seeking Alpha', 'Benzinga', 'The Motley Fool', 'Zacks Investment Research',
    'TipRanks', 'TheStreet', 'Investor\'s Business Daily'
]

OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "rss_news_dataset_massive.csv"

# ==========================================
# 3. GESTION DU TEMPS (TIME TRAVEL)
# ==========================================
# On configure ici la fenêtre de recherche (Ex: La dernière année)
DATE_FIN = datetime.datetime.today()
# Tu fixes manuellement : Année, Mois, Jour
DATE_DEBUT = datetime.datetime(2020, 1, 1)
FORMAT_DATE = "%Y-%m-%d"

# Découpage par mois pour contourner la limite de 100 articles de Google News
date_ranges = pd.date_range(start=DATE_DEBUT, end=DATE_FIN, freq='ME').to_list()
if DATE_FIN not in date_ranges:
    date_ranges.append(DATE_FIN)

# ==========================================
# 4. FONCTION D'EXTRACTION MASSIVE
# ==========================================
def scraper_rss_massif():
    logger.info("🚀 Démarrage de la collecte RSS Google News (Mode Archive)...")
    toutes_les_news = []
    
    for count, ticker in enumerate(TICKERS):
        logger.info(f"--- [{count+1}/{len(TICKERS)}] Scraping intensif pour {ticker} ---")
        
        for i in range(len(date_ranges) - 1):
            chunk_debut = date_ranges[i].strftime(FORMAT_DATE)
            chunk_fin = date_ranges[i+1].strftime(FORMAT_DATE)
            
            logger.info(f"    -> Recherche pour la période : {chunk_debut} au {chunk_fin}...")
            
            # Injection des opérateurs de date Google directement dans la requête (URL encodée)
            query = f"{ticker} stock after:{chunk_debut} before:{chunk_fin}"
            safe_query = quote(query)
            rss_url = f"https://news.google.com/rss/search?q={safe_query}&hl=en-US&gl=US&ceid=US:en"
            
            try:
                flux = feedparser.parse(rss_url)
                
                if flux.entries:
                    articles_sauves = 0
                    for article in flux.entries:
                        source_journal = article.get('source', {}).get('title', 'Unknown')
                        
                        # Filtre élargi pour accepter plus d'articles pertinents
                        if any(src.lower() in source_journal.lower() for src in SOURCES_FINANCE):
                            
                            date_brute = article.get('published_parsed')
                            date_pub = time.strftime('%Y-%m-%d', date_brute) if date_brute else chunk_fin
                                
                            toutes_les_news.append({
                                'Date_Publication': date_pub,
                                'Ticker': ticker,
                                'Source': source_journal,
                                'Titre': article.get('title', ''),
                                'URL': article.get('link', '')
                            })
                            articles_sauves += 1
                            
                    logger.info(f"       ✅ {articles_sauves} articles validés extraits.")
                else:
                    pass # Aucun résultat sur ce mois
                    
            except Exception as e:
                logger.error(f"       ❌ Erreur lors de la lecture pour {ticker} : {e}")
                
            time.sleep(2) # Pause pour éviter de se faire bloquer par Google

    # ==========================================
    # 5. SAUVEGARDE INTELLIGENTE (MODE APPEND)
    # ==========================================
    if toutes_les_news:
        logger.info("Traitement terminé. Création du DataFrame Pandas...")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        df_new = pd.DataFrame(toutes_les_news)
        fichier_existe = OUTPUT_FILE.exists()
        
        try:
            # Mode 'a' (Append) pour cumuler les données au fil du temps
            df_new.to_csv(OUTPUT_FILE, mode='a', index=False, encoding='utf-8', header=not fichier_existe)
            
            # Nettoyage des doublons sur l'ensemble de la base
            df_complet = pd.read_csv(OUTPUT_FILE)
            df_complet = df_complet.drop_duplicates(subset=['Ticker', 'Titre'])
            df_complet.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
            
            logger.info(f"🎉 SUCCÈS ! Base de données mise à jour. Total : {len(df_complet)} News uniques.")
        except Exception as e:
            logger.error(f"❌ Erreur d'écriture CSV : {e}")
    else:
        logger.warning("⚠️ Aucune News n'a été récoltée. Les sources n'ont peut-être rien publié.")

if __name__ == "__main__":
    scraper_rss_massif()