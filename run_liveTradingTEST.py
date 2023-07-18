from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.account_summary_tags import AccountSummaryTags
import threading
import time
import datetime
import pandas as pd
from databaseClass import DB
import passwords
from utils import DataProcessor
from utils import ModelBuilder
from utils import Predictor
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import sklearn
import pytz
from joblib import dump, load
from ibapi.utils import iswrapper
from ibapi.order_state import OrderState
from ibapi.contract import Contract
from sql_files import queries

userName = passwords.userName
userPass = passwords.userPass
dataBaseName = passwords.dataBaseName
host = 'localhost'

class App(EWrapper, EClient):
    def __init__(self, db, tableName):
        EClient.__init__(self, self)
        self.db = db
        self.tableName = tableName
        self.nextOrderId = None 
        self.contract = None
    
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

    def error(self, reqId: int, errorCode: int, errorString: str):
        print(f"Error. Id: {reqId}, Code: {errorCode}, Msg: {errorString}")


    def get_buying_power(self):
        query = '''
        SELECT 
        val
        FROM public.account_summary
        where "key" = 'BuyingPower'
        order by "timestamp" desc
        limit 1
        '''
        buying_power = self.db.DBtoValue(query)
        return buying_power
    

    def get_ES_positions(self):
        query = '''
        SELECT 
        pos
        FROM public.positions
        where "symbol" = 'ES'
        order by "timestamp" desc
        limit 1
        '''
        total_ES_positions = self.db.DBtoValue(query)
        return total_ES_positions

    def create_order(self, action: str, quantity: int) -> Order:
        """Create an order"""
        order = Order()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = "MKT"
        order.eTradeOnly = False
        order.firmQuoteOnly = False
        self.placeOrder(self.nextOrderId, self.contract, order) # change contract to self.contract
        self.nextOrderId += 1
        return order

def paper_trade(app, api_thread, contract, preprocessor, model_builder, predictor, time_steps, look_ahead):
    # Check account details

    buying_power = float(app.get_buying_power())
    total_ES_positions = int(app.get_ES_positions())

    # Get current time
    now = datetime.datetime.now(pytz.UTC)

    # Get the time five minutes ago
    five_minutes_ago = now - datetime.timedelta(minutes=5)

    # Process data
    new_data = app.db.DBtoDF(f"SELECT * FROM {queries.tickdata_date}WHERE timestamp BETWEEN '{five_minutes_ago}' AND '{now}'")
    preprocessor.df = new_data
    preprocessor.process_df()
    preprocessor.processed_df = preprocessor.processed_df.tail(250) #do more here to decide how much data to include (ie, everthing after nulls)
    preprocessor.scale_shift_data(look_ahead=0, for_training=False)
    X = preprocessor.scaled_df
    X = preprocessor.create_dataset(X, y=None, time_steps=60, look_ahead=0, for_training=False) #look_ahead 0 means we aren't shifting data at all

    # Work on model
    model_builder.load_model("models/model.h5")

    # Assign the model to the predictor
    predictor.model = model_builder.model
    # Predict the next 'look_ahead' steps
    predictions = predictor.predict(time_steps=60, for_training=False)
    rescaled_predictions = predictor.rescale_prediction(predictions)
    price = rescaled_predictions[-1][0]

    current_price = preprocessor.processed_df['Close'][-1]
    # Determine action based on predicted price
    # if price > current_price * 1.001 and buying_power > 5000 and total_ES_positions <=3:
    if price > current_price and buying_power > 5000 and total_ES_positions < 3: # Only limit buying when the number of positions reaches a certain level
        action = "BUY"
        app.db.addPrediction(now, float(current_price), float(price), action)
        app.create_order(action, 1)
        print(action)
    elif price < current_price and total_ES_positions > 0: # Allow selling regardless of the number of positions
        action = "SELL"
        app.db.addPrediction(now, float(current_price), float(price), action)
        app.create_order(action, 1)
        print(action)
    else:
        action = "NONE"
        app.db.addPrediction(now, float(current_price), float(price), action)
        print(action)


def app_connect(tableName, tws_connect_num, connect_thread):
    db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host='localhost', docker=False)
    app = App(db, tableName)
    app.connect("127.0.0.1", tws_connect_num, connect_thread)
    #time.sleep(5) #use for paper trading
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


def main():
    app, api_thread, contract = app_connect(queries.tickdata_date, 7497, 28)
    app.contract = contract
    preprocessor = DataProcessor(df=None)
    model_builder = ModelBuilder(n_features=5, time_steps=60)
    predictor = Predictor(model=None, preprocessor=preprocessor)
    while True:
        paper_trade(app, api_thread, contract, preprocessor, model_builder, predictor, time_steps=60, look_ahead=5)
        time.sleep(5)

if __name__ == "__main__":
    main()
