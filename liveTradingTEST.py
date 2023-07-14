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

userName = passwords.userName
userPass = passwords.userPass
dataBaseName = passwords.dataBaseName
host = 'localhost'

class App(EWrapper, EClient):
    def __init__(self, db, tableName):
        EClient.__init__(self, self)
        self.db = db
        self.tableName = tableName



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

def paper_trade(app, api_thread, contract, preprocessor, model_builder, predictor, time_steps, look_ahead):
    # Check account details

    buying_power = float(app.get_buying_power())
    total_ES_positions = int(app.get_ES_positions())

    # Do not proceed if not enough margin or too many ES positions
    if buying_power < 5000 or total_ES_positions >= 3:
        return

    # Get current time
    now = datetime.datetime.now(pytz.UTC)

    # Get the time five minutes ago
    five_minutes_ago = now - datetime.timedelta(minutes=5)

    # Process data
    new_data = app.db.DBtoDF(f"SELECT * FROM tickdata_jul13 WHERE timestamp BETWEEN '{five_minutes_ago}' AND '{now}'")
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
    if price > current_price * 1.05 and buying_power > 5000 and total_ES_positions <=3:
        action = "BUY"
        app.db.addPrediction(now, float(current_price), float(price), action)
        order = Order()
        order.action = action
        order.totalQuantity = 1
        order.orderType = "MKT"
        app.placeOrder(app.nextOrderId(), contract, order)
    elif price < current_price * 0.95 and total_ES_positions > 0:
        action = "SELL"
        app.db.addPrediction(now, float(current_price), float(price), action)
        order = Order()
        order.action = action
        order.totalQuantity = total_ES_positions
        order.orderType = "MKT"
        app.placeOrder(app.nextOrderId(), contract, order)


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
    app, api_thread, contract = app_connect("tickdata_jul13", 7497, 21)
    preprocessor = DataProcessor(df=None)
    model_builder = ModelBuilder(n_features=5, time_steps=60)
    predictor = Predictor(model=None, preprocessor=preprocessor)
    while True:
        paper_trade(app, api_thread, contract, preprocessor, model_builder, predictor, time_steps=60, look_ahead=5)
        time.sleep(60)

if __name__ == "__main__":
    main()
