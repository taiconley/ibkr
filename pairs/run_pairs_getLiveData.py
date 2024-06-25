import sys
sys.path.append("..")


from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import TickerId
from ibapi.common import RealTimeBar
from decimal import Decimal
import threading
import time
import pandas as pd
from databaseClass import DB
import passwords
from sql_files import queries
from datetime import datetime


userName = passwords.userName
userPass = passwords.userPass
dataBaseName = passwords.dataBaseName
host = passwords.host
tableName = 'pairs_live_trading'

class App(EWrapper, EClient):
    def __init__(self, db, tableName):
        EClient.__init__(self, self)
        self.db = db
        self.tableName = tableName
        self.reqId_to_symbol = {}  # New attribute to store the mapping

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=None):
        print("Error: ", reqId, " ", errorCode, " ", errorString)
        if advancedOrderRejectJson:
            print("Advanced order rejection reason: ", advancedOrderRejectJson)

    def realtimeBar(self, reqId: TickerId, time: int, open_: float, high: float, low: float, close: float,
                    volume: Decimal, wap: Decimal, count: int):
        ticker = self.reqId_to_symbol.get(reqId, "Unknown Ticker")
        super().realtimeBar(reqId, time, open_, high, low, close, volume, wap, count)
        #print(f"RealTimeBar. Ticker: {ticker}, TickerId: {reqId}, Time: {time}, Open: {open_}, High: {high}, Low: {low}, Close: {close}, Volume: {volume}, WAP: {wap}, Count: {count}")
        
        datetime_value = datetime.fromtimestamp(time)
        data = pd.DataFrame({
                            'date': [datetime_value],
                            'ticker': [ticker],
                            'open': [open_],
                            'high': [high],
                            'low': [low],
                            'close': [close],
                            'volume': [volume],
                            'count': [count],
                            'wap': [wap]
        })
        self.db.DFtoDB(data, self.tableName)  # Insert data into database
        print(data)


def app_connect(tableName, tws_connect_num, connect_thread):
    db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host=host, docker=False)
    app = App(db, tableName)
    app.connect("127.0.0.1", tws_connect_num, connect_thread)
    time.sleep(5) #use for paper trading


    # Start the socket in a thread
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()
    return app, api_thread


def get_realTimeBars(app, contract, reqId):
    barSize = 5
    whatToShow = "TRADES"
    useRTH = 0
    realtime = 1

    app.reqRealTimeBars(reqId, contract, barSize, whatToShow, useRTH, [])


def main():
    app, api_thread, = app_connect(tableName, 7497, 4)
    # tickers = ['CAC','CCS','CIVB','CNOB','DCOM','FFIC','FISI','FLIC','FRME','FRST',
    #            'IBTX','JOAN','KBH','LBAI','LEN','LILA','LILAK','MDC','MHO','MNTS',
    #            'MTH','MYFW','NWBI','OCFC','PHM','PPBI','RBB','SFST','TCBK','TCMD',
    #            'THFF','TMHC','TMP','TPH','WSBC'
    # ]
    tickers =   ['EPAC',
                    'SPXC']
                    # 'QTWO',
                    # 'SPXC',
                    # 'QTWO',
                    # 'WAB',
                    # 'SKYW',
                    # 'TDG',
                    # 'IR',
                    # 'LRCX',
                    # 'SPXC',
                    # 'WAB',
                    # 'GFF',
                    # 'HLT',
                    # 'CVLT',
                    # 'TXRH']



    # unique request ID for each ticker
    for index, ticker in enumerate(tickers, start=1):  # starting from reqId=1
        contract = Contract()
        contract.symbol = ticker
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        app.reqId_to_symbol[index] = ticker  # Update the dictionary with the mapping
        print(ticker)
        get_realTimeBars(app, contract, index)

    # Disconnect after fetching data for all tickers
    # Let it run for a specified duration
    time.sleep(1800) 
    app.disconnect()

if __name__ == "__main__":
    main()