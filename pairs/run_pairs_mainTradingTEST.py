import sys
sys.path.append("..")


from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import TickerId
from ibapi.common import RealTimeBar
from ibapi.utils import iswrapper
from ibapi.order import Order
from ibapi.order_state import OrderState
from ibapi.contract import Contract
import logging
from decimal import Decimal
import threading
import time
import pandas as pd
from databaseClass import DB
import passwords
from sql_files import queries
from datetime import datetime
import numpy as np


userName = passwords.userName
userPass = passwords.userPass
dataBaseName = passwords.dataBaseName
host = 'localhost'
tableName = 'pairs_live_trading'


class PairsTradingApp(EWrapper, EClient):
    def __init__(self, db, tableName, pairs):
        EClient.__init__(self, self)
        self.db = db
        self.tableName = tableName
        self.pairs = pairs
        self.nextOrderId = None 
        self.contracts = {stock: None for pair in pairs for stock in pair}


    @iswrapper
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextOrderId = orderId
    
    def orderStatus(self, orderId: int, status: str, filled: float,
                    remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,
                    whyHeld: str, mktCapPrice: float):
        print(f"OrderStatus. Id: {orderId}, Status: {status}, Filled: {filled}, Remaining: {remaining}, LastFillPrice: {lastFillPrice}")

    def openOrder(self, orderId: int, contract: Contract, order: Order,
                orderState: OrderState):
        print(f"OpenOrder. ID: {orderId}, {contract.symbol}, {contract.secType} @ {contract.exchange}: {order.action}, {order.orderType} {order.totalQuantity}, state: {orderState.status}")


    def error(self, reqId: TickerId, errorCode: int, errorString: str, contract: Contract = None):
        if contract:
            print(f"Error related to contract: {contract.symbol}, {contract.secType} @ {contract.exchange}")
        print(f"Error. Id: {reqId}, Code: {errorCode}, Msg: {errorString}")


    def fetch_latest_data(self, stock, limit):
        """Fetch the latest data for the given stock from the database."""
        query = f"SELECT * FROM {self.tableName} WHERE ticker = '{stock}' ORDER BY date DESC LIMIT {limit}"
        df = self.db.DBtoDF(query)
        return df.sort_values(by='date')

    def fetch_latest_portfolio_cash(self):
        """Fetch the latest data for the given portfolio data from Account Summary table."""

        query = f"SELECT val FROM public.account_summary where key = 'AvailableFunds' ORDER BY timestamp DESC LIMIT 1"
        value = self.db.DBtoValue(query)
        return float(value)

    def fetch_latest_portfolio(self):
        """Fetch the latest data from positions table and from pairs_live_trading data for real time prices.
           Joins both together to output a dataframe with current portfolio positions and live price data
        """

        query_real_time_positions = '''
        SELECT t1.latest_timestamp, t1.contract_symbol AS ticker, p.position, p.marketvalue, p.averagecost
            FROM (
                SELECT MAX(timestamp) AS latest_timestamp, contract_symbol
                FROM portfolio
                WHERE CAST(timestamp AS DATE) = CURRENT_DATE
                GROUP BY contract_symbol
            ) AS t1
            JOIN portfolio p ON p.contract_symbol = t1.contract_symbol AND p.timestamp = t1.latest_timestamp
            '''

        df_real_time_positions = self.db.DBtoDF(query_real_time_positions)
        df_real_time_positions['ticker'] = df_real_time_positions['ticker'].str.strip()

        query_real_time_prices = f'''
        SELECT max(date) as latest_timestamp, ticker, max(close) as close
            FROM {self.tableName}
            GROUP BY ticker
            ORDER BY ticker
        '''
        
        df_real_time_prices = self.db.DBtoDF(query_real_time_prices)
        df_real_time_positions = pd.merge(df_real_time_positions, df_real_time_prices[['ticker', 'close']], on='ticker', how='left')
        df_real_time_positions['updated_marketvalue'] = np.where(
            df_real_time_positions['close'].notna(),  
            df_real_time_positions['position'] * df_real_time_positions['close'], 
            df_real_time_positions['marketvalue']  
        )
        df_real_time_positions['total_cost'] = df_real_time_positions['position'] * df_real_time_positions['averagecost']
        df_real_time_positions['pnl_percent'] = (df_real_time_positions['updated_marketvalue'] - df_real_time_positions['total_cost']) / df_real_time_positions['total_cost']

        return df_real_time_positions

    def create_order(self, stock: str, action: str, quantity: int):
        if self.nextOrderId is None:
            raise ValueError("Order ID not initialized")
        order = Order()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = "MKT"
        order.eTradeOnly = False
        order.firmQuoteOnly = False
        contract = self.contracts[stock]
        self.placeOrder(self.nextOrderId, contract, order)
        self.nextOrderId += 1
        return order

    def trade_pairs_strategy(self, limit, lookback, threshold, trade_percentage, max_multiplier, stop_loss_percentage, take_profit_percentage):
        # Wait until nextOrderId is populated
        max_wait_time = 10  # seconds
        wait_time = 0
        while self.nextOrderId is None and wait_time < max_wait_time:
            time.sleep(1)  # wait for 1 second
            wait_time += 1
    
        if self.nextOrderId is None:
            print("Failed to get a valid order ID.")
            return

        self.create_order("IR", "BUY", 1)
    #     total_cash = self.fetch_latest_portfolio_cash()
    #     df_real_time_positions = self.fetch_latest_portfolio()
    #     df_real_time_positions.to_csv("real_time_positions.csv")

    #     def close_all_positions():
    #         if stock1_current_qty < 0:
    #             self.create_order(stock1, "BUY", stock1_current_qty)
    #         elif stock1_current_qty > 0:
    #             self.create_order(stock1, "SELL", stock1_current_qty)
    #         if stock2_current_qty < 0:
    #             self.create_order(stock2, "BUY", stock2_current_qty)
    #         elif stock2_current_qty > 0:
    #             self.create_order(stock2, "SELL", stock2_current_qty)
            

        # for stock1, stock2 in self.pairs:
        #     df_stock1 = self.fetch_latest_data(stock1, limit)
        #     #df_stock1.to_csv("stock1.csv")
        #     df_stock2 = self.fetch_latest_data(stock2, limit)
        #     #df_stock2.to_csv("stock2.csv")           

        #     # Calculate the spread
        #     df = df_stock1.set_index('date').join(df_stock2.set_index('date'), lsuffix='_stock1', rsuffix='_stock2')
        #     #df.to_csv("stock1and2.csv")
        #     df['spread'] = df['close_stock1'] - df['close_stock2']

        #     # Calculate z-score
        #     df['mean_spread'] = df['spread'].rolling(window=lookback).mean()
        #     df['std_spread'] = df['spread'].rolling(window=lookback).std()
        #     df['z_score'] = (df['spread'] - df['mean_spread']) / df['std_spread']     

        #     #prep to floats
        #     df['volume_stock1'] = df['volume_stock1'].astype(float)
        #     df['count_stock1'] = df['count_stock1'].astype(float)
        #     df['volume_stock2'] = df['volume_stock2'].astype(float)
        #     df['count_stock2'] = df['count_stock2'].astype(float)

        #     # Determine trading signals based on z-score and threshold
        #     df['signal'] = "None"
        #     df.loc[df['z_score'] > threshold, 'signal'] = f'Buy {stock1}, Sell {stock2}'
        #     df.loc[df['z_score'] < -threshold, 'signal'] = f'Sell {stock1}, Buy {stock2}'
        #     #df = df.round(2)

        #     # Reset the index to turn the date index into a column
        #     df.reset_index(inplace=True)

        #     # Optionally, if the new column doesn't have a descriptive name, rename it
        #     df.rename(columns={'index': 'date'}, inplace=True)
        #     df.to_csv("real_time_metrics.csv")
        #     self.db.DFRowtoDB(df.iloc[-1:], "pairs_live_calculated_metrics")
        #     print(df.iloc[-1:])
 

        #     # Compute the current portfolio value before making any trades
        #     #portfolio_value_before_trade = total_cash + self.stock1_qty_cumulative * df_stock1['close'].iloc[-1] + self.stock2_qty_cumulative * df_stock2['close'].iloc[-1]
        #     portfolio_value_before_trade = total_cash + df_real_time_positions['updated_marketvalue'].sum()


        #     # Adaptive trade size based on z-score
        #     base_trade_size = portfolio_value_before_trade * trade_percentage
        #     adaptive_trade_size = base_trade_size * min(abs(df['z_score'].iloc[-1]), max_multiplier)

        #     stock1_current_qty = df_real_time_positions[df_real_time_positions['ticker'] == stock1]['position'].sum()
        #     stock2_current_qty = df_real_time_positions[df_real_time_positions['ticker'] == stock2]['position'].sum()
        #     # Execute trading signals based on the most recent signal
        #     # first if is when to buy stock1 and sell stock2
        #     # second if is when to sell stock1 and buy stock1
        #     # third if is to exit position because signal is lost
        #     signal = df['signal'].iloc[-1]
        #     print(signal)
        #     if signal == 'None':
        #         if 
        #     elif (df['signal'].iloc[-1] == 'Buy ' + stock1 + ', Sell ' + stock2) and (stock1_current_qty == 0) and (stock2_current_qty == 0):                
        #         stock1_tobuy_qty = int(round(adaptive_trade_size / 2 / df_stock1['close'].iloc[-1], 0))
        #         stock2_tobuy_qty = int(round(adaptive_trade_size / 2 / df_stock2['close'].iloc[-1], 0))
        #         self.create_order(stock1, "BUY", stock1_tobuy_qty)
        #         self.create_order(stock2, "SELL", stock2_tobuy_qty)
        #     elif (df['signal'].iloc[-1] == 'Sell ' + stock1 + ', Buy ' + stock2) and (stock1_current_qty ==0) and (stock2_current_qty == 0):
        #         stock1_tobuy_qty = round(adaptive_trade_size / 2 / df_stock1['close'].iloc[-1], 0)
        #         stock2_tobuy_qty = round(adaptive_trade_size / 2 / df_stock2['close'].iloc[-1], 0)
        #         self.create_order(stock1, "SELL", stock1_tobuy_qty)
        #         self.create_order(stock2, "BUY", stock2_tobuy_qty)
        #     elif df['signal'].iloc[-1] == 'None':
        #         if (stock1_current_qty == 0) and (stock2_current_qty == 0):
        #             break
        #         elif (stock1_current_qty != 0) and (stock2_current_qty != 0):
        #             close_all_positions()
        #         # if stock1_current_qty < 0:
        #         #     self.create_order(stock1, "BUY", stock1_current_qty)
        #         # elif stock1_current_qty > 0:
        #         #     self.create_order(stock1, "SELL", stock1_current_qty)
        #         # if stock2_current_qty < 0:
        #         #     self.create_order(stock2, "BUY", stock2_current_qty)
        #         # elif stock2_current_qty > 0:
        #         #     self.create_order(stock2, "SELL", stock2_current_qty)
                


        #     # Stop-loss and Take-profit logic

        #     # check pnl %. If <= stop_loss_percentage, then exit position. 
        #     # if >= take_profit_percentage, then exit position
        #     # need to think about what pnl means in a pair.  do i consider each position seperately, or combined

        #     stock1_pnl = df_real_time_positions[df_real_time_positions['ticker'] == stock1]['pnl_percent'][0]
        #     stock2_pnl = df_real_time_positions[df_real_time_positions['ticker'] == stock2]['pnl_percent'][0]

        #     if (stock1_pnl < (-stop_loss_percentage)) or (stock2_pnl < (-stop_loss_percentage)):
        #         close_all_positions()

        #     if (stock1_pnl > take_profit_percentage) or (stock2_pnl > take_profit_percentage):
        #         close_all_positions()




def app_connect(tableName, tws_connect_num, connect_thread, pairs, max_retries=5):
    db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host='localhost', docker=False)
    app = PairsTradingApp(db, tableName, pairs)

    retry_count = 0
    while retry_count < max_retries:
        try:
            app.connect("127.0.0.1", tws_connect_num, connect_thread)
            print(f"Successfully connected with thread ID: {connect_thread}")
            break  # Exit loop if connection is successful
        except Exception as e:
            print(f"Connection failed on thread {connect_thread}: {str(e)}")
            connect_thread += 1  # Increment thread ID after a failed attempt
            retry_count += 1
            time.sleep(2)  # Wait a bit before retrying
    
    if retry_count == max_retries:
        print("Failed to connect after maximum retries.")
        return None  # Or handle it some other way

    for stock in [stock for pair in pairs for stock in pair]:
        contract = Contract()
        contract.symbol = stock
        contract.secType = "STK"  # Assuming stocks for pairs trading
        contract.exchange = "SMART"
        contract.currency = "USD"
        app.contracts[stock] = contract

    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()
    return app, api_thread
    

if __name__ == "__main__":
    limit = 600 # limit is the set of datapoints collected from the database.  example 30 means the last 30 data points.  This should be same or larger than lookback
    lookback = 30 # lookback is the number of datapoints used when calculating metrics, after it is collected from database with limit
    threshold = 0.5
    trade_percentage = 0.1
    max_multiplier = 2.0
    stop_loss_percentage = 0.03
    take_profit_percentage = 0.04
    # Define pairs to paper trade
    #pairs = [('EPAC', 'SPXC'), ('QTWO', 'WAB')]  # Add or modify as needed
    pairs = [('IR', 'LRCX')]

    # Connect the application
    app, api_thread = app_connect(tableName, 7497, 10, pairs)  # Add or modify pairs as needed


    while app.isConnected():
        app.trade_pairs_strategy(limit, lookback, threshold, trade_percentage, max_multiplier, stop_loss_percentage, take_profit_percentage)
        time.sleep(3)


        app.disconnect()