from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.execution import ExecutionFilter
import threading
import time
import pandas as pd
import passwords
from databaseClass import DB
from sql_files import queries

userName = passwords.userName
userPass = passwords.userPass
dataBaseName = passwords.dataBaseName
host = passwords.host
table_date = queries.tickdata_date

class App(EWrapper, EClient):
    def __init__(self, db, tableName):
        EClient.__init__(self, self)
        self.db = db
        self.tableName = tableName

    def error(self, reqId, errorCode, errorString):
        print("Error: ", reqId, " ", errorCode, " ", errorString)

    def updateMktDepth(self, reqId, position, operation, side, price, size):
        timestamp = pd.Timestamp.now(tz='UTC')  # current timestamp in UTC
        data = pd.DataFrame({
                            'position': [position],
                            'operation': [operation],
                            'side': [side],
                            'price': [price],
                            'size': [size],
                            'timestamp': [timestamp]
        })
        self.db.DFtoDB(data, self.tableName)  # Insert data into database
        print(data)


def app_connect(tableName, tws_connect_num, connect_thread):
    db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host=host, docker=False)
    app = App(db, tableName)
    app.connect("127.0.0.1", tws_connect_num, connect_thread)
    time.sleep(3) #use for paper trading
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

def get_level2_data(app, contract):
    # Request Level 2 Data
    app.reqMktDepth(1, contract, 5, False, [])
    # Let it run for a minute
    time.sleep(60000) 
    # Disconnect
    app.disconnect()

def main():
    app, api_thread, contract = app_connect(table_date+"_l2", 7497, 3)
    get_level2_data(app, contract)

if __name__ == "__main__":
    main()