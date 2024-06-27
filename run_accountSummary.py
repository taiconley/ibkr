from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import TickerId
from databaseClass import DB
import passwords
import datetime
import pytz
import time


userName = passwords.userName
userPass = passwords.userPass
dataBaseName = passwords.dataBaseName
host = 'localhost'

class App(EWrapper, EClient):
    def __init__(self, db):
        EClient.__init__(self, self)
        self.db = db
    
    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str):
        timestamp = datetime.datetime.now(pytz.UTC)
        self.db.addAccountSummary(timestamp, key, val, currency, accountName)
        print(f"updateAccountValue. Key: {key}, Value: {val}, Currency: {currency}, AccountName: {accountName}")


    def updatePortfolio(self, contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL, accountName):
        timestamp = datetime.datetime.now(pytz.UTC)
        self.db.addPortfolio(timestamp, contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL, accountName)
        print(f"updatePortfolio. Contract: Symbol={contract.symbol}, SecType={contract.secType}, Currency={contract.currency}, Exchange={contract.exchange}, Position: {position}, MarketPrice: {marketPrice}, MarketValue: {marketValue}, AverageCost: {averageCost}, UnrealizedPNL: {unrealizedPNL}, RealizedPNL: {realizedPNL}, AccountName: {accountName}")


    def positionMulti(self, reqId: int, account: str, modelCode: str, contract, pos: float, avgCost: float):
        timestamp = datetime.datetime.now(pytz.UTC)
        self.db.addPosition(timestamp, reqId, account, modelCode, contract, pos, avgCost)
        print(f"Position. ReqId: {reqId}, Account: {account}, ModelCode: {modelCode}, Contract: Symbol={contract.symbol}, SecType={contract.secType}, Currency={contract.currency}, Exchange={contract.exchange}, Position: {pos}, AvgCost: {avgCost}")


def main():
    db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host='localhost', docker=False)
    app = App(db)
    app.connect("127.0.0.1", 7497, clientId=20) # adjust as needed

    app.reqAccountUpdates(True, "") # This will request real-time account updates.
    app.reqPositionsMulti(1, "", "") # This will request real-time position updates for all accounts.

    # time.sleep(3)
    app.run()

if __name__ == "__main__":
    main()