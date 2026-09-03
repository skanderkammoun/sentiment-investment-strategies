import logging
import datetime
import time
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
    
    logger.info(f"🚀 Demarrage du navigateur furtif pour la cible : r/{SUBREDDIT}...")
    
    try:
        with SB(uc=True, test=True) as sb:
            
            # Echauffement du navigateur pour initialiser les cookies et eviter les blocages
            logger.info("Echauffement du navigateur sur la page d'accueil...")
            sb.activate_cdp_mode("https://www.reddit.com")
            sb.sleep(5) 
            
            for ticker in TICKERS:
                logger.info(f"🔍 Recherche en cours pour le ticker : {ticker} ...")
                # Parametres : restrict_sr=1 (limite a ce forum), sort=new & t=all (historique max)
                url = f"https://www.reddit.com/r/{SUBREDDIT}/search/?q={ticker}&restrict_sr=1&sort=new&t=all"
                
                sb.activate_cdp_mode(url)
                sb.sleep(6) # Pause legerement augmentee pour les chargements lourds
                
                logger.info(f"⏬ Defilement PROFOND (Smart Scrolling max {MAX_SCROLLS}) pour {ticker}...")
                
                # --- NOUVEAU SMART SCROLLING ---
                last_height = sb.execute_script("return document.body.scrollHeight")
                scroll_count = 0
                
                while scroll_count < MAX_SCROLLS:
                    sb.scroll_down(45)
                    sb.sleep(0.6) 
                    
                    new_height = sb.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        logger.info(f"🛑 Fin de la page atteinte pour {ticker} apres {scroll_count} scrolls.")
                        break
                    last_height = new_height
                    scroll_count += 1
                    
                    # Log de progression tous les 50 scrolls
                    if scroll_count % 50 == 0:
                        logger.info(f"Progression : {scroll_count}/{MAX_SCROLLS} scrolls effectues pour {ticker}...")
                
                logger.info(f"🧠 Extraction JS ultra-agressive pour {ticker}...")
                
                # --- LE SUPER EXTRACTEUR JS (Titre + Vraie Date) ---
                js_extractor = """
                var extracted_data = [];
                var titles_found = new Set();
                
                // Strategie 1 : Balise shreddit-post
                var posts = document.querySelectorAll('shreddit-post');
                if (posts.length > 0) {
                    posts.forEach(function(post) {
                        var title = post.getAttribute('post-title');
                        var timestamp = post.getAttribute('created-timestamp');
                        if (title && timestamp) {
                            var date_only = timestamp.split('T')[0];
                            title = title.replace(/\\n/g, ' ').trim();
                            if (!titles_found.has(title)) {
                                extracted_data.push({'titre': title, 'date': date_only});
                                titles_found.add(title);
                            }
                        }
                    });
                }
                
                // Strategie 2 : Recherche par liens (Fallback si l'interface change)
                if (extracted_data.length === 0) {
                    // On cible spécifiquement le forum stocks
                    var links = document.querySelectorAll('a[href*="/r/stocks/comments/"]');
                    links.forEach(function(link) {
                        var title = link.innerText;
                        if (title && title.trim().length > 5 && !title.includes(' comments')) {
                            title = title.replace(/\\n/g, ' ').trim();
                            var container = link.closest('faceplate-tracker, div') || document;
                            var timeNode = container.querySelector('time, faceplate-timeago');
                            var date_only = "Date_Inconnue";
                            
                            if (timeNode) {
                                var ts = timeNode.getAttribute('ts') || timeNode.getAttribute('datetime');
                                if (ts) {
                                    date_only = ts.split('T')[0];
                                }
                            }
                            
                            if (!titles_found.has(title)) {
                                extracted_data.push({'titre': title, 'date': date_only});
                                titles_found.add(title);
                            }
                        }
                    });
                }
                return extracted_data;
                """
                
                posts_data = sb.execute_script(js_extractor)
                logger.info(f"✅ Extraction terminee : {len(posts_data)} posts captures pour {ticker}.")
                
                for item in posts_data:
                    toutes_les_donnees.append({
                        'Date_Publication': item['date'], # Injection de la date reelle !
                        'Ticker': ticker,
                        'Subreddit': SUBREDDIT,
                        'Titre': item['titre']
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
        
        # Filtre anti-doublons strict avec la Date de Publication
        df_unique = df.drop_duplicates(subset=['Ticker', 'Titre', 'Date_Publication'])
        
        try:
            df_unique.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
            logger.info(f"🎉 SUCCES ! {len(df_unique)} posts UNIQUES sauvegardes dans : {OUTPUT_FILE}")
            
            print("\n🔍 APERÇU DES 5 PREMIÈRES LIGNES :")
            print(df_unique.head())
            
        except Exception as e:
            logger.error(f"Erreur d'ecriture lors de la sauvegarde CSV : {e}")
    else:
        logger.warning("Aucune donnee n'a ete recoltee a l'issue du script.")

if __name__ == "__main__":
    scraper_reddit_stocks_maximum()