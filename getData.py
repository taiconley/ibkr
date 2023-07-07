from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time
import pandas as pd
from databaseClass import DB
import passwords

userName = passwords.userName
userPass = passwords.userPass
dataBaseName = passwords.dataBaseName
host = passwords.host

class App(EWrapper, EClient):
    def __init__(self, db, tableName):
        EClient.__init__(self, self)
        self.db = db
        self.tableName = tableName

    def error(self, reqId, errorCode, errorString):
        print("Error: ", reqId, " ", errorCode, " ", errorString)

    def historicalData(self, reqId, bar):
        print("HistoricalData. ", reqId, " Date:", bar.date, "Open:", bar.open,
              "High:", bar.high, "Low:", bar.low, "Close:", bar.close, "Volume:", bar.volume,
              "Count:", bar.barCount, "WAP:", bar.average)

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        print("HistoricalDataEnd ", reqId, " ", start, " ", end)
        self.disconnect()

    # def realTimeBar(self, reqId, time, open, high, low, close, volume, wap, count):
    #     print("RealTimeBar. ", reqId, " Time:", time, "Open:", open,
    #           "High:", high, "Low:", low, "Close:", close, "Volume:", volume,
    #           "Count:", count, "WAP:", wap)

    def realTimeBar(self, reqId, time, open, high, low, close, volume, wap, count):
        super().realtimeBar(reqId, time, open, high, low, close, volume, wap, count)
        print("RealTimeBars. ", reqId, ": time -", time, ", open -", open, ", high -", high, ", low -", low, ", close -", close, ", volume -", volume)
    
    def tickSize(self, reqId, tickType, size):
        if tickType == 5 and size != -1:
            timestamp = pd.Timestamp.now(tz='UTC')  # current timestamp in UTC
            data = pd.DataFrame({'tickType': [tickType], 'Price': 0, 'Volume': [size], 'timestamp': [timestamp]})
            self.db.DFtoDB(data, self.tableName)  # Insert data into database
            print(data)
        else:
            print(f'Skipped tickType: {tickType}')  # For debugging purposes, you may want to know when data is skipped

    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType in [1, 2, 4, 5] and price != -1:
            timestamp = pd.Timestamp.now(tz='UTC')  # current timestamp in UTC
            data = pd.DataFrame({'tickType': [tickType], 'Price': [price], 'Volume': 0, 'timestamp': [timestamp]})
            self.db.DFtoDB(data, self.tableName)  # Insert data into database
            print(data)
        else:
            print(f'Skipped tickType: {tickType}')  # For debugging purposes, you may want to know when data is skipped

def app_connect(tableName, tws_connect_num, connect_thread):
    db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host=host, docker=False)
    app = App(db, tableName)
    app.connect("127.0.0.1", tws_connect_num, connect_thread)
    time.sleep(5) #use for paper trading
    contract = Contract()
    contract.symbol = "ES"
    contract.secType = "FUT"
    contract.exchange = "CME"
    contract.currency = "USD"
    contract.lastTradeDateOrContractMonth = "202309" # Please check the contract month

    # Start the socket in a thread
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()
    return app, api_thread, contract

def get_historicalData(app, contract):
    # Request historical bars
    app.reqHistoricalData(1, contract, "", "600 S", "1 min", "TRADES", 0, 2, False, [])
    #Wait for disconnection
    while app.isConnected():
        time.sleep(1)

def get_realTimeData(app, contract):
    # Request Market Data
    app.reqMktData(1, contract, "", False, False, [])
    # Let it run for a minute
    time.sleep(6000) 
    # Disconnect
    app.disconnect()

def get_realTimeBars(app, contract):
    reqId = 1 # Unique identifier for the request
    barSize = 5  # Bar size in seconds (5 seconds in this case)
    whatToShow = "TRADES"  # Type of data to return, "TRADES", "BID", "ASK", "MIDPOINT", etc.
    useRTH = 0  # Use Regular Trading Hours only? 0 means no, 1 means yes
    realtime = 0  # Whether to return real-time data, 1 for real-time, 0 for delayed

    app.reqRealTimeBars(reqId, contract, barSize, whatToShow, useRTH, [])
    
    # Let it run for a minute
    time.sleep(30) 
    # Disconnect
    app.disconnect()


def main():
    app, api_thread, contract = app_connect("tickdata_jul6", 7496, 8)
    get_realTimeData(app, contract)
    #get_historicalData(app, contract)
    #get_realTimeBars(app, contract)  # call this function with app and contract as arguments


if __name__ == "__main__":
    main()
