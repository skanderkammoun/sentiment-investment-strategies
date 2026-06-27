import yfinance as yf
import pandas as pd
import logging
import sys


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout), 
        logging.FileHandler('collecte_finance.log') 
    ]
)
logger = logging.getLogger(__name__)


tickers = ['GOOGL', 'AAPL', 'META', 'AMZN', 'MSFT', 'TSLA', 'UNH', 'BRK-B', 'JPM']
date_debut = '2010-01-01'
date_fin = '2026-06-27'
nom_fichier_sortie = 'dataset_finance_hybride_2010_2026.csv'

def collecter_donnees_financieres():
    logger.info(f"Démarrage du pipeline d'extraction : {date_debut} à {date_fin}")
    toutes_les_donnees = []

    for ticker in tickers:
        logger.info(f"Requête API yfinance en cours pour le ticker : {ticker}")
        
        try:
            df = yf.download(ticker, start=date_debut, end=date_fin, progress=False)
            
            if df.empty:
                logger.warning(f"Aucune donnée trouvée pour {ticker}. Ignoré.")
                continue
                
            df['Ticker'] = ticker
            df['StockChange'] = (df['Close'] - df['Open']) / df['Open']
            df['Target'] = df['StockChange'].apply(lambda x: 1 if x > 0 else -1)
            
            toutes_les_donnees.append(df)
            logger.info(f"Succès pour {ticker} : {len(df)} lignes extraites.")
            
        except Exception as e:
            logger.error(f"Erreur critique lors de l'extraction de {ticker}: {str(e)}")

    if not toutes_les_donnees:
        logger.critical("Échec total : Aucune donnée n'a été extraite.")
        return

    logger.info("Fusion des DataFrames en cours...")
    dataset_final = pd.concat(toutes_les_donnees)
    colonnes_finales = ['Ticker', 'Open', 'High', 'Low', 'Close', 'Volume', 'StockChange', 'Target']
    dataset_final = dataset_final[colonnes_finales]
    
    try:
        dataset_final.to_csv(nom_fichier_sortie)
        logger.info(f"Pipeline terminé avec succès. Fichier sauvegardé : {nom_fichier_sortie}")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du fichier CSV : {str(e)}")

if __name__ == "__main__":
    collecter_donnees_financieres()