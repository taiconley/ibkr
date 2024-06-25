import sys
sys.path.append("..")

import logging
import passwords
from databaseClass import DB
# from sql_files import queries
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time
import pandas as pd
from databaseClass import DB
import passwords
from datetime import datetime, timedelta

# from sql_files import queries



logging.basicConfig(filename='getDataPairs.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

userName = passwords.userName
userPass = passwords.userPass
dataBaseName = passwords.dataBaseName
host = passwords.host

tickers = ['SPY']
#tickers = ['FRME', 'NWBI','TCMD', 'TPH','CCS', 'LEN','LILA', 'LILAK']
#tickers = pd.read_csv("tickers.csv")['Ticker'].tolist() #normally use this
#tickers = pd.read_csv("tickers_pairs.csv")['Ticker'].tolist()

class App(EWrapper, EClient):
    def __init__(self, db, tableName, currentTicker):
        EClient.__init__(self, self)
        self.db = db
        self.tableName = tableName
        self.currentTicker = currentTicker

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=None):
        logging.error(f"Error: {reqId} {errorCode} {errorString}")
        if advancedOrderRejectJson:
           logging.error(f"Advanced Order rejection Reason: {advancedOrderRejectJson}") 


    def historicalData(self, reqId, bar):
        data = pd.DataFrame({
                            'date': [bar.date],
                            'ticker': [self.currentTicker],
                            'open': [bar.open],
                            'high': [bar.high],
                            'low': [bar.low],
                            'close': [bar.close],
                            'volume': [bar.volume],
                            'count': [bar.barCount],
                            'wap': [bar.wap],
        })
        self.db.DFtoDB(data, self.tableName)  # Insert data into database
        print(data)

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        print(f"HistoricalDataEnd {reqId} {start} {end}")
        self.disconnect()


def create_contract(symbol):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
    return contract


def main():
    for ticker in tickers:
        app = None
        try:
            # Setup database connection
            db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host=host, docker=False)

            # Create the IBKR App
            #app = App(db, "pairs", ticker)
            app = App(db, "pairs_daily", ticker) #Check

            # Connect to TWS (or IB Gateway)
            app.connect("127.0.0.1", 7497, clientId=3)

            # Create a contract
            contract = create_contract(ticker)

            # Initialize threading
            api_thread = threading.Thread(target=app.run, daemon=True)
            api_thread.start()

            # Give it a moment to connect
            time.sleep(2)

            # Request historical data for the contract
            end_date_time = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d 23:59:59')
            app.reqHistoricalData(1, contract, end_date_time, "1 Y", "1 day", "TRADES", 0, 1, False, [])

            #app.reqHistoricalData(1, contract, "", "1 M", "1 hour", "TRADES", 0, 1, False, [])
            #app.reqHistoricalData(1, contract, "", "1 Y", "1 day", "TRADES", 0, 1, False, [])

            # Allow time for processing
            time.sleep(2)

        except Exception as e:
            logging.error(f"Error getting data for {ticker}: {e}")
            continue

        finally:
            # Disconnect after each request to respect pacing rules
            if app and app.isConnected():
                app.disconnect()

        # Pause between each request to not overstep pacing rules
        #time.sleep(10)

if __name__ == "__main__":
    main()