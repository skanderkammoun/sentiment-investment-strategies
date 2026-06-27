import requests
import pandas as pd
import logging
import sys
import os
from dotenv import load_dotenv


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('collecte_tiingo.log')
    ]
)
logger = logging.getLogger(__name__)


load_dotenv()
API_KEY = os.getenv("TIINGO_API_KEY")

if not API_KEY:
    logger.critical("Clé API Tiingo introuvable. Vérifiez votre fichier .env.")
    sys.exit()


tickers = ['GOOGL', 'AAPL', 'META', 'AMZN', 'MSFT', 'TSLA', 'UNH', 'BRK-B', 'JPM']
date_debut = '2010-01-01'
date_fin = '2026-06-27'
headers = {'Content-Type': 'application/json'}

def collecter_prix_tiingo():
    logger.info("Démarrage de l'extraction des prix via l'API Tiingo...")
    toutes_les_donnees = []

    for ticker in tickers:
        logger.info(f"Requête API Tiingo en cours pour : {ticker}")
        
        # URL officielle de l'API Tiingo pour l'historique des prix
        url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices?startDate={date_debut}&endDate={date_fin}&token={API_KEY}"
        
        try:
            response = requests.get(url, headers=headers)
            
            
            if response.status_code == 200:
                data = response.json()
                if not data:
                    logger.warning(f"Aucune donnée retournée par Tiingo pour {ticker}.")
                    continue
                
                
                df = pd.DataFrame(data)
                
                
                df['Ticker'] = ticker
                df.rename(columns={'date': 'Date', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
                
                
                df['StockChange'] = (df['Close'] - df['Open']) / df['Open']
                df['Target'] = df['StockChange'].apply(lambda x: 1 if x > 0 else -1)
                
                toutes_les_donnees.append(df)
                logger.info(f"Succès pour {ticker} : {len(df)} lignes extraites depuis Tiingo.")
                
            else:
                logger.error(f"Erreur API pour {ticker}: Code {response.status_code}")
                
        except Exception as e:
            logger.error(f"Erreur critique lors de l'extraction de {ticker}: {str(e)}")

    
    if not toutes_les_donnees:
        logger.critical("Échec total : Aucune donnée Tiingo n'a pu être collectée.")
        return

    logger.info("Fusion des DataFrames Tiingo en cours...")
    dataset_final = pd.concat(toutes_les_donnees)
    
    colonnes_finales = ['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'StockChange', 'Target']
    dataset_final = dataset_final[colonnes_finales]
    
    nom_fichier_sortie = 'dataset_finance_tiingo_2010_2026.csv'
    dataset_final.to_csv(nom_fichier_sortie, index=False)
    logger.info(f"Pipeline terminé avec succès. Fichier sauvegardé : {nom_fichier_sortie}")

if __name__ == "__main__":
    collecter_prix_tiingo()