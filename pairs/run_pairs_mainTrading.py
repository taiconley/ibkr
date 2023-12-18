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


userName = passwords.userName
userPass = passwords.userPass
dataBaseName = passwords.dataBaseName
host = 'localhost'
# tableName = 'pairs_live_trading'
tableName = 'pairs'
lookback = 3
threshold = 0.5
trade_percentage = 0.4
max_multiplier = 2.0
stop_loss_percentage = 0.03
take_profit_percentage = 0.04



# Define pairs to paper trade
pairs = [('DCOM', 'NWBI'), ('TCMD', 'TPH')]  # Add or modify as needed


class PairsTradingApp(EWrapper, EClient):
    def __init__(self, db, tableName, pairs):
        EClient.__init__(self, self)
        self.db = db
        self.tableName = tableName
        self.pairs = pairs
        self.nextOrderId = None 
        self.contracts = {stock: None for pair in pairs for stock in pair}
        self.initial_investment = 10000
        self.total_cash = 10000

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

    # def error(self, reqId: int, errorCode: int, errorString: str):
    #     print(f"Error. Id: {reqId}, Code: {errorCode}, Msg: {errorString}")
    def error(self, reqId: TickerId, errorCode: int, errorString: str, contract: Contract = None):
        if contract:
            print(f"Error related to contract: {contract.symbol}, {contract.secType} @ {contract.exchange}")
        print(f"Error. Id: {reqId}, Code: {errorCode}, Msg: {errorString}")


    def fetch_latest_data(self, stock, limit=lookback):
        """Fetch the latest data for the given stock from the database."""
        query = f"SELECT * FROM {self.tableName} WHERE ticker = '{stock}' ORDER BY date DESC LIMIT {limit}"
        df = self.db.DBtoDF(query)
        return df.sort_values(by='date')

    def create_order(self, stock: str, action: str, quantity: int) -> Order:
        """Create an order"""
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

    def trade_pairs_strategy(self, lookback, threshold, trade_percentage, max_multiplier, stop_loss_percentage, take_profit_percentage):
        peak_portfolio_value = self.initial_investment
        entry_portfolio_value = self.initial_investment

        for stock1, stock2 in self.pairs:
            df_stock1 = self.fetch_latest_data(stock1, lookback * 2) #multiply by 2 for a buffer to count summary stats.  not sure if this is right
            df_stock2 = self.fetch_latest_data(stock2, lookback * 2)
                       
            # Calculate the spread
            df = df_stock1.set_index('date').join(df_stock2.set_index('date'), lsuffix='_stock1', rsuffix='_stock2')
            df['spread'] = df['close_stock1'] - df['close_stock2']

            # Calculate z-score
            df['mean_spread'] = df['spread'].rolling(window=lookback).mean()
            df['std_spread'] = df['spread'].rolling(window=lookback).std()
            df['z_score'] = (df['spread'] - df['mean_spread']) / df['std_spread']     


            # Determine trading signals based on z-score and threshold
            df['signal'] = None
            df.loc[df['z_score'] > threshold, 'signal'] = f'Buy {stock1}, Sell {stock2}'
            df.loc[df['z_score'] < -threshold, 'signal'] = f'Sell {stock1}, Buy {stock2}'

            # Compute the current portfolio value before making any trades
            portfolio_value_before_trade = self.total_cash + self.stock1_qty_cumulative * df_stock1['close'].iloc[-1] + self.stock2_qty_cumulative * df_stock2['close'].iloc[-1]
            
            # Adaptive trade size based on z-score
            base_trade_size = portfolio_value_before_trade * trade_percentage
            adaptive_trade_size = base_trade_size * min(abs(df['z_score'].iloc[-1]), max_multiplier)

            # Execute trading signals based on the most recent signal
            if df['signal'].iloc[-1] == 'Buy ' + stock1 + ', Sell ' + stock2:
                stock1_qty = adaptive_trade_size / 2 / df_stock1['close'].iloc[-1]
                stock2_qty = -adaptive_trade_size / 2 / df_stock2['close'].iloc[-1]
                self.create_order(stock1, "BUY", stock1_qty)
                self.create_order(stock2, "SELL", stock2_qty)
            elif df['signal'].iloc[-1] == 'Sell ' + stock1 + ', Buy ' + stock2:
                stock1_qty = -adaptive_trade_size / 2 / df_stock1['close'].iloc[-1]
                stock2_qty = adaptive_trade_size / 2 / df_stock2['close'].iloc[-1]
                self.create_order(stock1, "SELL", stock1_qty)
                self.create_order(stock2, "BUY", stock2_qty)

            # Stop-loss and Take-profit logic
            if portfolio_value_before_trade <= (1 - stop_loss_percentage) * peak_portfolio_value:
                # Stop-loss hit, close all positions
                self.create_order(stock1, "SELL", self.stock1_qty_cumulative)
                self.create_order(stock2, "SELL", self.stock2_qty_cumulative)
                peak_portfolio_value = portfolio_value_before_trade  # Resetting peak value
            elif portfolio_value_before_trade >= (1 + take_profit_percentage) * entry_portfolio_value:
                # Take-profit hit, close all positions
                self.create_order(stock1, "SELL", self.stock1_qty_cumulative)
                self.create_order(stock2, "SELL", self.stock2_qty_cumulative)
                entry_portfolio_value = portfolio_value_before_trade  # Resetting entry value

        # You might also want to update your portfolio after trades, e.g.:
        self.update_portfolio(stock1, stock2)      

        def update_portfolio(self, stock1, stock2):
        # Placeholder method to update your portfolio after trades. You'll need to define 
        # how exactly this updates your stored portfolio values, e.g., self.total_cash, 
        # self.stock1_qty_cumulative, and self.stock2_qty_cumulative.
            pass


def app_connect(tableName, tws_connect_num, connect_thread, pairs):
    db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host='localhost', docker=False)
    app = PairsTradingApp(db, tableName, pairs)
    app.connect("127.0.0.1", tws_connect_num, connect_thread)

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
    # Connect the application
    app, api_thread = app_connect(tableName, 7497, 0, pairs)  # Add or modify pairs as needed
    app.trade_pairs_strategy(lookback, threshold, trade_percentage, max_multiplier, stop_loss_percentage, take_profit_percentage)