#used for historical data

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time

class App(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def error(self, reqId, errorCode, errorString):
        print("Error: ", reqId, " ", errorCode, " ", errorString)

    def historicalData(self, reqId, bar):
        print("HistoricalData. ", reqId, " Date:", bar.date, "Open:", bar.open,
              "High:", bar.high, "Low:", bar.low, "Close:", bar.close, "Volume:", bar.volume,
              "Count:", bar.barCount, "WAP:", bar.average)

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        print("HistoricalDataEnd ", reqId, " ", start, " ", end)
        self.disconnect()

    def realTimeBar(self, reqId, time, open, high, low, close, volume, wap, count):
        print("RealTimeBar. ", reqId, " Time:", time, "Open:", open,
              "High:", high, "Low:", low, "Close:", close, "Volume:", volume,
              "Count:", count, "WAP:", wap)

    # def reqRealtimeBar(self, reqId, time, open_, high, low, close, volume, wap, count):
    #     super().realtimeBar(reqId, time, open_, high, low, close, volume, wap, count)
    #     print("RealTimeBar. TickerId:", reqId, RealTimeBar(time, -1, open_, high, low, close, volume, wap, count))
    
    def tickPrice(self, reqId, tickType, price, attrib):
        print("Tick Price. Ticker Id:", reqId, "tickType:", tickType, "Price:", price)



def get_historicalData():
    # fill in here

def get_realTimeData():
    # fill in here


def main():
    app = App()
    app.connect("127.0.0.1", 7496, 10)
    contract = Contract()
    contract.symbol = "ES"
    contract.secType = "FUT"
    contract.exchange = "CME"
    contract.currency = "USD"
    contract.lastTradeDateOrContractMonth = "202306" # Please check the contract month

    # Start the socket in a thread
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()

    # Request historical bars
    # app.reqHistoricalData(1, contract, "", "600 S", "1 min", "TRADES", 0, 2, False, [])
    
    # #Wait for disconnection
    # while app.isConnected():
    #     time.sleep(1)

#    # Request real time bars
#     app.reqRealTimeBars(1, contract, 5, "BID", True, []) 
#     # Run for 1 minute then stop
#     time.sleep(60)

#     # Cancel real time bars and disconnect
#     app.cancelRealTimeBars(1)
#     app.disconnect()

    # Request Market Data
    app.reqMktData(1, contract, "", False, False, [])

    # Let it run for a minute
    time.sleep(60) 

    # Disconnect
    app.disconnect()



if __name__ == "__main__":
    main()
