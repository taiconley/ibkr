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

def paper_trade(app, api_thread, contract, preprocessor, model_builder, predictor, time_steps, look_ahead):

    # Get current time
    now = datetime.datetime.now(pytz.UTC)

    # Get the time one minute ago
    one_minute_ago = now - datetime.timedelta(minutes=1)
    
    # Get the time five minutes ago
    five_minutes_ago = now - datetime.timedelta(minutes=5)
        
    # Query the database for all rows from the 5 minutes minute
    new_data = app.db.DBtoDF(f"SELECT * FROM tickdata_jun21 WHERE timestamp BETWEEN '{five_minutes_ago}' AND '{now}'")
    #new_data['timestamp'] = pd.to_datetime(new_data['timestamp'])
    new_data['timestamp'] = new_data['timestamp'].dt.tz_localize('UTC')
    print("Step 1")
    print(new_data.head())
    new_data.to_csv(f"testdata/new_data_{now}.csv")


    # Process new_data into the proper format for the model
    preprocessor.df = new_data
    preprocessor.process_df()
    print("step 2")
    print(preprocessor.processed_df.head())
    preprocessor.processed_df.to_csv(f"testdata/processed_data_{now}.csv")
    # After preprocessing and filling, trim data to only last 60 records
    preprocessor.processed_df = preprocessor.processed_df.tail(60)
    # print("Step 3")
    # print(preprocessor.processed_df.head())

    # preprocessor.scale_shift_data(look_ahead)
    
#     X, y = preprocessor.scaled_df, preprocessor.shifted_df['Close']
#     print("Step 4")
#     print(X[0:5])
#     print(y[0:5])
#     print(X.shape)
#     print(y.shape)
#     X, y = preprocessor.create_dataset(X, y, time_steps)
#     print("Step 5")
#     print(X[0:5])
#     print(y[0:5])

#     # Load the model
#     model_builder.load_model("models/model.h5")

#     # Assign the model to the predictor
#     predictor.model = model_builder.model

#     # Predict the next 'look_ahead' steps
#     predictions = predictor.predict(look_ahead, time_steps)
#     print("step 6")
#     print(predictions[0:5])

#     # Rescale predictions back to the original scale
#     rescaled_predictions = predictor.rescale_prediction(predictions)
#     print("Step 7:")
#     print(rescaled_predictions[0:5])

#     # Fetch the last predicted value
#     price = rescaled_predictions[-1][0]
#     print("Step 8")
#     print(price)

#     print("Step 9")
#    # print(new_data['price_4'][-1])
#     if price > preprocessor.processed_df['Close'][-1]:
#         # Buy if the predicted price is higher than the current price
#         #app.placeOrder(app.nextOrderId(), order, Order(action="BUY", totalQuantity=1, orderType="LMT", lmtPrice=price))
#         print(f"expected price: {price} Action: buy, {preprocessor.processed_df['Close'][-1]}")

#     elif price < preprocessor.processed_df['Close'][-1]:
#         # Sell if the predicted price is lower than the current price
#         #app.placeOrder(app.nextOrderId(), order, Order(action="SELL", totalQuantity=1, orderType="LMT", lmtPrice=price))
#         print(f"expected price: {price} Action: sell, {preprocessor.processed_df['Close'][-1]}")

        
def app_connect():
    db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host='localhost', docker=False)
    app = App(db, tableName="tickdata_jun15")
    app.connect("127.0.0.1", 7496, 11)
    # time.sleep(5) #use for paper trading
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
    app, api_thread, contract = app_connect()
    preprocessor = DataProcessor(df=None)
    model_builder = ModelBuilder(n_features=5, time_steps=60)
    predictor = Predictor(model=None, preprocessor=preprocessor)
    while True:
        paper_trade(app, api_thread, contract, preprocessor, model_builder, predictor, time_steps=60, look_ahead=5)
        time.sleep(30)