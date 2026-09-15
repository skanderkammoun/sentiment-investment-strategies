import logging
import datetime
import time
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
# 2. CONSTANTES
# ==========================================
TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'TSLA', 'UNH', 'BRK.B', 'JPM']
SUBREDDIT = "wallstreetbets"
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "reddit_stealth_data_massive.csv"
MAX_SCROLLS = 150 

# ==========================================
# 3. FONCTION PRINCIPALE
# ==========================================
def scraper_reddit_massif() -> None:
    toutes_les_donnees = []
    
    logger.info("🚀 Démarrage du navigateur furtif...")
    
    try:
        with SB(uc=True, test=True) as sb:
            
            logger.info("Échauffement du navigateur sur la page d'accueil...")
            sb.activate_cdp_mode("https://www.reddit.com")
            sb.sleep(5) 
            
            for ticker in TICKERS:
                logger.info(f"🔍 Recherche en cours pour : {ticker} ...")
                url = f"https://www.reddit.com/r/{SUBREDDIT}/search/?q={ticker}&restrict_sr=1&sort=new&t=all"
                
                sb.activate_cdp_mode(url)
                sb.sleep(5) 
                
                logger.info(f"⏬ Démarrage du Smart Scrolling pour {ticker}...")
                
                last_height = sb.execute_script("return document.body.scrollHeight")
                scroll_count = 0
                
                while scroll_count < MAX_SCROLLS:
                    sb.scroll_down(50)
                    sb.sleep(1) 
                    new_height = sb.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        logger.info(f"🛑 Fin de la page atteinte pour {ticker} après {scroll_count} scrolls.")
                        break
                    last_height = new_height
                    scroll_count += 1
                
                logger.info(f"Extraction JS ultra-agressive pour {ticker}...")
                
                # --- LE NOUVEAU SUPER EXTRACTEUR JS ---
                js_extractor = """
                var extracted_data = [];
                var titles_found = new Set(); // Pour éviter les doublons directement en JS
                
                // Stratégie 1 : L'ancienne méthode (shreddit-post)
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
                
                // Stratégie 2 : La nouvelle méthode (Recherche par liens)
                if (extracted_data.length === 0) {
                    // On cible tous les liens qui dirigent vers un commentaire de WallStreetBets
                    var links = document.querySelectorAll('a[href*="/r/wallstreetbets/comments/"]');
                    links.forEach(function(link) {
                        var title = link.innerText;
                        
                        // Exclusion des liens de commentaires "x comments"
                        if (title && title.trim().length > 5 && !title.includes(' comments')) {
                            title = title.replace(/\\n/g, ' ').trim();
                            
                            // Recherche de la date à proximité du titre
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
                logger.info(f"✅ Extraction terminée : {len(posts_data)} posts capturés pour {ticker}.")
                
                for item in posts_data:
                    # On sauvegarde même s'il manque la date temporairement pour sécuriser la donnée
                    toutes_les_donnees.append({
                        'Date_Publication': item['date'],
                        'Ticker': ticker,
                        'Subreddit': SUBREDDIT,
                        'Titre': item['titre']
                    })
                        
                sb.sleep(3) 
                
    except Exception as e:
        logger.error(f"Une erreur critique est survenue : {e}")
        return

    # ==========================================
    # 4. NETTOYAGE ET SAUVEGARDE
    # ==========================================
    if toutes_les_donnees:
        logger.info("Traitement terminé. Nettoyage des données...")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame(toutes_les_donnees)
        df_unique = df.drop_duplicates(subset=['Ticker', 'Titre'])
        
        try:
            df_unique.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
            logger.info(f"🎉 SUCCÈS TOTAL ! {len(df_unique)} posts UNIQUES sauvegardés.")
            print("\n🔍 APERÇU :")
            print(df_unique.head())
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde : {e}")
    else:
        logger.warning("Aucune donnée n'a été récoltée.")

if __name__ == "__main__":
    scraper_reddit_massif()