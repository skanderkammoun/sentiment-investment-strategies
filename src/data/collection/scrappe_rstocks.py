import logging
import datetime
from pathlib import Path
import pandas as pd
from seleniumbase import SB

# ==========================================
# 1. CONFIGURATION DU LOGGING (Niveau Prod)
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s] - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ==========================================
# 2. CONSTANTES DE L'ENVIRONNEMENT
# ==========================================
TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'TSLA', 'UNH', 'BRK.B', 'JPM']
SUBREDDIT = "stocks"  # Cible : Le forum des investisseurs rationnels
MAX_SCROLLS = 150     # Mode "Maximum" : On force Reddit jusqu'à la limite de ses serveurs

OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / f"reddit_{SUBREDDIT}_data_massive.csv"

# ==========================================
# 3. FONCTION D'EXTRACTION MASSIVE
# ==========================================
def scraper_reddit_stocks_maximum() -> None:
    toutes_les_donnees = []
    
    logger.info(f"Demarrage du navigateur furtif pour la cible : r/{SUBREDDIT}...")
    
    try:
        with SB(uc=True, test=True) as sb:
            
            # Echauffement du navigateur pour initialiser les cookies et eviter les blocages
            logger.info("Echauffement du navigateur sur la page d'accueil...")
            sb.activate_cdp_mode("https://www.reddit.com")
            sb.sleep(5) 
            
            for ticker in TICKERS:
                logger.info(f"Recherche en cours pour le ticker : {ticker} ...")
                # Parametres : restrict_sr=1 (limite a ce forum) & sort=new (les plus recents)
                url = f"https://www.reddit.com/r/{SUBREDDIT}/search/?q={ticker}&restrict_sr=1&sort=new"
                
                sb.activate_cdp_mode(url)
                sb.sleep(6) # Pause legerement augmentee pour les chargements lourds
                
                post_title_selector = '[data-testid="post-title"]'
                
                try:
                    # Timeout long (25s) pour la robustesse réseau
                    sb.wait_for_element(post_title_selector, timeout=25)
                except Exception as e:
                    logger.warning(f"Aucun post trouve pour {ticker} (ou temps de reponse trop long).")
                    continue
                    
                logger.info(f"Defilement PROFOND (Mode Maximum : {MAX_SCROLLS} scrolls) pour {ticker}...")
                
                # --- BOUCLE D'EXTRACTION MAXIMALE ---
                for scroll_idx in range(MAX_SCROLLS):
                    sb.scroll_down(45)
                    # Pause indispensable : plus la page est longue, plus elle met de temps a charger la suite
                    sb.sleep(0.6) 
                    
                    # Log de progression tous les 50 scrolls pour savoir que le script n'est pas planté
                    if (scroll_idx + 1) % 50 == 0:
                        logger.info(f"Progression : {scroll_idx + 1}/{MAX_SCROLLS} scrolls effectues pour {ticker}...")
                
                # Aspiration du DOM HTML final
                posts = sb.select_all(post_title_selector)
                logger.info(f"Extraction terminee : {len(posts)} elements bruts captures pour {ticker}.")
                
                for post in posts:
                    titre = post.text
                    if titre:
                        toutes_les_donnees.append({
                            'Date_Scraping': datetime.datetime.now().strftime('%Y-%m-%d'),
                            'Ticker': ticker,
                            'Subreddit': SUBREDDIT,
                            'Titre': titre
                        })
                        
                # Pause pour refroidir la connexion avant la prochaine recherche
                logger.info(f"Pause de securite avant le prochain ticker...")
                sb.sleep(4) 
                
    except Exception as e:
        logger.error(f"Une erreur critique est survenue dans le processus global : {e}")
        return

    # ==========================================
    # 4. DATA ENGINEERING : NETTOYAGE ET EXPORT
    # ==========================================
    if toutes_les_donnees:
        logger.info("Traitement termine. Demarrage du nettoyage Pandas (Data Cleaning)...")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame(toutes_les_donnees)
        
        # Filtre anti-doublons strict
        df_unique = df.drop_duplicates(subset=['Ticker', 'Titre'])
        
        try:
            df_unique.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
            logger.info(f"SUCCES ! {len(df_unique)} posts UNIQUES sauvegardes dans : {OUTPUT_FILE}")
        except Exception as e:
            logger.error(f"Erreur d'ecriture lors de la sauvegarde CSV : {e}")
    else:
        logger.warning("Aucune donnee n'a ete recoltee a l'issue du script.")

if __name__ == "__main__":
    scraper_reddit_stocks_maximum()