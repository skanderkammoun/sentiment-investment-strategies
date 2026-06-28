import logging
import datetime
from pathlib import Path
import pandas as pd
from seleniumbase import SB

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
# 2. CONSTANTES (Tes 9 Actions)
# ==========================================
TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'TSLA', 'UNH', 'BRK.B', 'JPM']
SUBREDDIT = "wallstreetbets"
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "reddit_stealth_data_massive.csv"

# ==========================================
# 3. FONCTION PRINCIPALE
# ==========================================
def scraper_reddit_massif() -> None:
    toutes_les_donnees = []
    
    logger.info("🚀 Démarrage du navigateur furtif...")
    
    try:
        # On utilise ton Chrome normal + le masque furtif uc_driver
        with SB(uc=True, test=True) as sb:
            
            # --- ASTUCE DE PRO : L'ÉCHAUFFEMENT ---
            # On charge la page d'accueil une fois pour passer les pop-ups éventuels
            logger.info("Échauffement du navigateur sur la page d'accueil...")
            sb.activate_cdp_mode("https://www.reddit.com")
            sb.sleep(5) 
            
            for ticker in TICKERS:
                logger.info(f"🔍 Recherche en cours pour le ticker : {ticker} ...")
                url = f"https://www.reddit.com/r/{SUBREDDIT}/search/?q={ticker}&restrict_sr=1&sort=new"
                
                sb.activate_cdp_mode(url)
                sb.sleep(5) # Laisse le temps au réseau de charger
                
                post_title_selector = '[data-testid="post-title"]'
                
                try:
                    # On attend jusqu'à 25 secondes pour être sûr
                    sb.wait_for_element(post_title_selector, timeout=25)
                except Exception as e:
                    logger.warning(f"⚠️ Aucun post trouvé pour {ticker} (ou temps trop long).")
                    continue
                    
                logger.info(f"⏬ Défilement PROFOND (scrolling) pour {ticker}. Ça va prendre un moment...")
                
                # --- LE SECRET DE LA MASSE DE DONNÉES ---
                # On scrolle 80 fois au lieu de 15 !
                for _ in range(80):
                    sb.scroll_down(45)
                    sb.sleep(0.5) # Pause vitale pour laisser Reddit charger la suite
                
                # Extraction
                posts = sb.select_all(post_title_selector)
                logger.info(f"Extraction terminée : {len(posts)} posts capturés pour {ticker}.")
                
                for post in posts:
                    titre = post.text
                    if titre:
                        toutes_les_donnees.append({
                            'Date_Scraping': datetime.datetime.now().strftime('%Y-%m-%d'),
                            'Ticker': ticker,
                            'Subreddit': SUBREDDIT,
                            'Titre': titre
                        })
                        
                sb.sleep(3) # Petite pause avant de passer à l'action suivante
                
    except Exception as e:
        logger.error(f"Une erreur critique est survenue : {e}")
        return

    # ==========================================
    # 4. NETTOYAGE ET SAUVEGARDE (Pandas)
    # ==========================================
    if toutes_les_donnees:
        logger.info("Traitement terminé. Nettoyage des données...")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame(toutes_les_donnees)
        
        # --- SUPPRESSION DES DOUBLONS ---
        # Au cas où le scroll capture deux fois le même post
        df_unique = df.drop_duplicates(subset=['Ticker', 'Titre'])
        
        try:
            df_unique.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
            logger.info(f"🎉 SUCCÈS TOTAL ! {len(df_unique)} posts UNIQUES sauvegardés dans : {OUTPUT_FILE}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde : {e}")
    else:
        logger.warning("Aucune donnée n'a été récoltée.")

if __name__ == "__main__":
    scraper_reddit_massif()