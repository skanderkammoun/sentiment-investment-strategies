import yfinance as yf
import pandas as pd
import logging
from pathlib import Path
import datetime

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
# 2. CONSTANTES DU PROJET
# ==========================================
TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'TSLA', 'UNH', 'BRK-B', 'JPM']
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "yahoo_news_dataset.csv"

# ==========================================
# 3. FONCTION D'EXTRACTION (Yahoo Finance)
# ==========================================
def scraper_yahoo_news():
    logger.info("🚀 Démarrage de la collecte des News via Yahoo Finance...")
    toutes_les_news = []
    
    for ticker in TICKERS:
        logger.info(f"📰 Récupération des articles pour {ticker}...")
        try:
            action = yf.Ticker(ticker)
            news_data = action.news
            
            if news_data:
                logger.info(f"✅ {len(news_data)} articles bruts trouvés pour {ticker}.")
                
                for article in news_data:
                    # L'ASTUCE EST ICI : Gérer le nouveau format de Yahoo (les données sont souvent dans 'content')
                    data = article.get('content', article)
                    
                    # 1. Extraction de la Date
                    timestamp = data.get('providerPublishTime')
                    if timestamp:
                        # Conversion du timestamp Unix
                        date_pub = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                    else:
                        # Si le timestamp n'existe pas, on cherche une date texte
                        date_pub = data.get('pubDate', '')[:10]
                        
                    # 2. Extraction de la Source (Parfois c'est un dictionnaire, parfois du texte)
                    provider = data.get('provider', 'Unknown')
                    if isinstance(provider, dict):
                        source = provider.get('displayName', 'Unknown')
                    else:
                        source = data.get('publisher', str(provider))
                        
                    # 3. Extraction du Titre
                    titre = data.get('title', '')
                    
                    # 4. Extraction de l'URL (Yahoo utilise plusieurs noms selon les articles)
                    url = data.get('canonicalUrl', data.get('clickThroughUrl', data.get('link', '')))
                    
                    # SÉCURITÉ : On ne sauvegarde QUE si on a réussi à extraire un titre !
                    if titre:
                        toutes_les_news.append({
                            'Date_Publication': date_pub,
                            'Ticker': ticker,
                            'Source': source,
                            'Titre': titre,
                            'URL': url
                        })
            else:
                logger.warning(f"⚠️ Aucune News trouvée pour {ticker}.")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération pour {ticker} : {e}")

    # ==========================================
    # 4. SAUVEGARDE ET EXPORT
    # ==========================================
    if toutes_les_news:
        logger.info("Traitement terminé. Création du DataFrame Pandas...")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame(toutes_les_news)
        df_unique = df.drop_duplicates(subset=['Ticker', 'Titre'])
        
        try:
            df_unique.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
            logger.info(f"🎉 SUCCÈS ! {len(df_unique)} News VALIDES sauvegardées dans : {OUTPUT_FILE}")
        except Exception as e:
            logger.error(f"❌ Erreur d'écriture CSV : {e}")
    else:
        logger.warning("⚠️ Aucune News n'a été extraite au final (Vérifier le format de l'API).")

if __name__ == "__main__":
    scraper_yahoo_news()