# # used for real time data

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time

class TestApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def error(self, reqId, errorCode, errorString):
        print("Error: ", reqId, " ", errorCode, " ", errorString)

    def tickPrice(self, reqId, tickType, price, attrib):
        print("Tick Price. Ticker Id:", reqId, "tickType:", tickType, "Price:", price)


def main():
    app = TestApp()

    app.connect("127.0.0.1", 7496, 5)

    contract = Contract()
    contract.symbol = "ES"
    contract.secType = "FUT"
    contract.exchange = "CME"
    contract.currency = "USD"
    contract.lastTradeDateOrContractMonth = "202306"

    # Start the socket in a thread
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()

    # Request Market Data
    app.reqMktData(1, contract, "", False, False, [])

    # Let it run for a minute
    time.sleep(60) 

    # Disconnect
    app.disconnect()


if __name__ == "__main__":
    main()