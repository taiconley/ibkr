from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
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

def paper_trade(app, table_name, api_thread, contract, preprocessor, model_builder, predictor, time_steps, look_ahead):

    # Get current time
    now = datetime.datetime.now(pytz.UTC)
    #now = datetime.datetime(2023, 6, 21, 20, 57, 3, 410027, pytz.UTC) # for testing


    # Get the time one minute ago
    one_minute_ago = now - datetime.timedelta(minutes=1)
    
    # Get the time five minutes ago
    five_minutes_ago = now - datetime.timedelta(minutes=5)
        
    # process data
    new_data = app.db.DBtoDF(f"SELECT * FROM {table_name} WHERE timestamp BETWEEN '{five_minutes_ago}' AND '{now}'")
    preprocessor.df = new_data
    preprocessor.process_df()
    preprocessor.processed_df = preprocessor.processed_df.tail(250) #do more here to decide how much data to include (ie, everthing after nulls)
    preprocessor.scale_shift_data(look_ahead=0, for_training=False)
    X = preprocessor.scaled_df
    X = preprocessor.create_dataset(X, y=None, time_steps=60, look_ahead=0, for_training=False) #look_ahead 0 means we aren't shifting data at all

    # work on model
    model_builder.load_model("models/model.h5")

    # Assign the model to the predictor
    predictor.model = model_builder.model
    # Predict the next 'look_ahead' steps
    predictions = predictor.predict(time_steps=60, for_training=False)
    rescaled_predictions = predictor.rescale_prediction(predictions)
    price = rescaled_predictions[-1][0]


    print("Step 9")
   # print(new_data['price_4'][-1])
    if price > preprocessor.processed_df['Close'][-1]:
        # Buy if the predicted price is higher than the current price
        #app.placeOrder(app.nextOrderId(), order, Order(action="BUY", totalQuantity=1, orderType="LMT", lmtPrice=price))
        print(f"expected price: {price} Action: buy, {preprocessor.processed_df['Close'][-1]}")

    elif price < preprocessor.processed_df['Close'][-1]:
        # Sell if the predicted price is lower than the current price
        #app.placeOrder(app.nextOrderId(), order, Order(action="SELL", totalQuantity=1, orderType="LMT", lmtPrice=price))
        print(f"expected price: {price} Action: sell, {preprocessor.processed_df['Close'][-1]}")


    # used to send to db
    if price > preprocessor.processed_df['Close'][-1]:
        decision = 'buy'
    elif price == preprocessor.processed_df['Close'][-1]:
        decision = 'hold'
    else:
        decision = 'sell'
    app.db.addPrediction(now, float(preprocessor.processed_df['Close'][-1]), float(price), decision)
        
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

if __name__ == "__main__":
    table_name = "tickdata_jul13"
    app, api_thread, contract = app_connect(table_name, 7497, 3)
    preprocessor = DataProcessor(df=None)
    model_builder = ModelBuilder(n_features=5, time_steps=60)
    predictor = Predictor(model=None, preprocessor=preprocessor)
    while True:
        paper_trade(app, table_name, api_thread, contract, preprocessor, model_builder, predictor, time_steps=60, look_ahead=5)
        # time.sleep(1)
