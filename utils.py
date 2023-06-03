from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time
import pandas as pd

class App(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = []

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
    
    def tickPrice(self, reqId, tickType, price, attrib):
        print("Tick Price. Ticker Id:", reqId, "tickType:", tickType, "Price:", price)

    # def tickPrice(self, reqId, tickType, price, attrib):
    #     # Capture the latest prices for BID, ASK, and LAST
    # this is used for testing making a window function
    #     if tickType in [1, 2, 4]:  # BID, ASK, and LAST
    #         timestamp = pd.Timestamp.now(tz='UTC')
    #         self.data.append((reqId, tickType, price, timestamp))

    def format_realTimeData(app):
        # Assume that the last price is the close, the highest price is the high, etc.
        # (In practice, you may want to track these values over time instead)
        close = max([price for reqId, tickType, price in app.data if tickType == 4], default=0)
        high = max([price for reqId, tickType, price in app.data if tickType == 2], default=0)
        low = min([price for reqId, tickType, price in app.data if tickType == 1], default=0)
        volume = 0  # Not available from tick data
        count = 0  # Not available from tick data
        wap = 0  # Not available from tick data

        print("RealTimeData. 1", "Date:", time.strftime("%Y%m%d %H:%M:%S"), 
            "Open:", close, "High:", high, "Low:", low, "Close:", close, 
            "Volume:", volume, "Count:", count, "WAP:", wap)




def app_connect():
    app = App()
    app.connect("127.0.0.1", 7496, 11)
    contract = Contract()
    contract.symbol = "ES"
    contract.secType = "FUT"
    contract.exchange = "CME"
    contract.currency = "USD"
    contract.lastTradeDateOrContractMonth = "202306" # Please check the contract month

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
    time.sleep(60) 
    # Disconnect
    app.disconnect()

def build_format_realTimeData(app):
    # Create a DataFrame from the data
    df = pd.DataFrame(app.data, columns=['reqId', 'tickType', 'value', 'timestamp'])

    # Group by 'reqId', 'tickType', and 30-second windows
    grouped_df = df.groupby(['reqId', 'tickType', pd.Grouper(key='timestamp', freq='30S')]).last().reset_index()

    # Pivot the DataFrame so that each row corresponds to a single request ID and timestamp,
    # and each column corresponds to a single tick type
    pivoted_df = grouped_df.pivot(index=['reqId', 'timestamp'], columns='tickType', values='value')

    # Rename the columns for clarity
    pivoted_df.rename(columns={1: 'bid', 2: 'ask', 4: 'last', 5: 'last_size', 6: 'wap', 8: 'volume'}, inplace=True)

    return pivoted_df


def main():
    app, api_thread, contract = app_connect()
    # get_realTimeData(app, contract)
    # get_historicalData(app, contract)
    get_realTimeData(app, contract)
    # real_time_data_df = build_format_realTimeData(app)
    # print(real_time_data_df)

if __name__ == "__main__":
    main()
