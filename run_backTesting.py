import sys
import os
import datetime
import pandas as pd
import time
import numpy as np
import matplotlib.pyplot as plt


from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

import tensorflow as tf
from tensorflow.keras.models import load_model
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout


import passwords
from databaseClass import DB
from utils import generate_df_from_sql_file, generate_list_from_sql_file
from utils import DataProcessor, ModelBuilder, Predictor
pd.set_option('display.max_rows', None)

userName = passwords.userName
userPass = passwords.userPass
dataBaseName = passwords.dataBaseName
host = passwords.host

db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host=host, docker=False)

class Backtester:
    def __init__(self, raw_data, initial_balance, preprocessor, model_builder, predictor, time_steps, look_ahead, num_runs):
        self.raw_data = raw_data
        self.initial_balance = initial_balance
        self.preprocessor = preprocessor
        self.model_builder = model_builder
        self.predictor = predictor
        self.time_steps = time_steps
        self.look_ahead = look_ahead
        self.num_runs = num_runs
        self.data = pd.DataFrame({
            'Actual': np.zeros(len(self.raw_data)),  # Initialize as zeros
            'Predicted': np.zeros(len(self.raw_data)),
            'Order': np.zeros(len(self.raw_data)),
            'Holdings': np.zeros(len(self.raw_data)),
            'Cash': np.full(len(self.raw_data), initial_balance),
            'Total': np.full(len(self.raw_data), initial_balance)
        }, index=self.raw_data.index).copy()
        self.model_builder.load_model("models/model.h5")
        self.predictor.model = self.model_builder.model

    def run(self):
        position = 0
        max_position = 3 
        # Preprocess the entire raw data
        self.preprocessor.df = self.raw_data.copy()
        self.preprocessor.process_df()
        self.preprocessor.scale_shift_data(look_ahead=0, for_training=False)
        for i in range(self.time_steps, len(self.data)):
            # Get the preprocessed data for the past 'time_steps' periods
            
            new_data = self.preprocessor.processed_df.iloc[i - self.time_steps : i]
            new_data.to_csv(f"newdata/{i}.csv")
            if new_data.empty:
                continue

            # Assume that your preprocessed data now has a 'Close' column
            actual_price_now = new_data['Close'].iloc[-1]  # Get the latest 'Close' price
            self.data.iat[i, self.data.columns.get_loc('Actual')] = actual_price_now  # Update 'Actual' price
            
            X = self.preprocessor.scaled_df
            X = self.preprocessor.create_dataset(X, y=None, time_steps=self.time_steps, look_ahead=0, for_training=False)
            predictions = self.predictor.predict(time_steps=self.time_steps, for_training=False, batch_size=6925)
            rescaled_predictions = self.predictor.rescale_prediction(predictions)
            price = rescaled_predictions[-1][0]
            self.data.iat[i, self.data.columns.get_loc('Predicted')] = price

            actual_price_now = self.data.iat[i, self.data.columns.get_loc('Actual')]
            # Buy condition
            # if price > actual_price_now and position != 1:
            #     self.data.iat[i, self.data.columns.get_loc('Order')] = 1
            #     self.data.iat[i, self.data.columns.get_loc('Cash')] -= actual_price_now
            #     position = 1
            if price > actual_price_now and position < max_position:
                self.data.iat[i, self.data.columns.get_loc('Order')] = 1
                self.data.iat[i, self.data.columns.get_loc('Cash')] -= actual_price_now
                position += 1  # increment position


            # Sell condition
            # elif price < actual_price_now and position != -1:
            #     self.data.iat[i, self.data.columns.get_loc('Order')] = -1
            #     self.data.iat[i, self.data.columns.get_loc('Cash')] += actual_price_now
            #     position = -1
            elif price < actual_price_now and position > -max_position:
                self.data.iat[i, self.data.columns.get_loc('Order')] = -1
                self.data.iat[i, self.data.columns.get_loc('Cash')] += actual_price_now
                position -= 1  # decrement position

            self.data.iat[i, self.data.columns.get_loc('Holdings')] = position * actual_price_now
            self.data.iat[i, self.data.columns.get_loc('Total')] = self.data.iat[i, self.data.columns.get_loc('Cash')] + self.data.iat[i, self.data.columns.get_loc('Holdings')]
            # Copy Cash and Holdings to the next row
            if i < len(self.data) - 1:
                self.data.iat[i + 1, self.data.columns.get_loc('Cash')] = self.data.iat[i, self.data.columns.get_loc('Cash')]
                self.data.iat[i + 1, self.data.columns.get_loc('Holdings')] = self.data.iat[i, self.data.columns.get_loc('Holdings')]
        self.data.iat[-1, self.data.columns.get_loc('Total')] = self.data.iat[-1, self.data.columns.get_loc('Cash')] + self.data.iat[-1, self.data.columns.get_loc('Holdings')]
        return self.data


    def calculate_metrics(self):
        total_profit = self.data['Total'].iloc[-1] - self.initial_balance
        num_positive_trades = len(self.data[self.data['Order'] > 0])
        num_negative_trades = len(self.data[self.data['Order'] < 0])
        total_trades = num_positive_trades + num_negative_trades
        win_ratio = num_positive_trades / total_trades if total_trades != 0 else 0
        avg_profit_per_trade = total_profit / total_trades if total_trades != 0 else 0
        return_on_investment = total_profit / self.initial_balance
        daily_returns = self.data['Total'].pct_change().dropna()
        sharpe_ratio = np.sqrt(252) * (daily_returns.mean() / daily_returns.std())
        metrics = {
            'Total Profit': total_profit,
            'Number of Positive Trades': num_positive_trades,
            'Number of Negative Trades': num_negative_trades,
            'Win Ratio': win_ratio,
            'Average Profit per Trade': avg_profit_per_trade,
            'Return on Investment': return_on_investment,
            'Sharpe Ratio': sharpe_ratio,
        }
        return metrics

    def plot_portfolio_values(self):
        fig, ax1 = plt.subplots(figsize=(10, 5))
        color = 'tab:blue'
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Actual Prices', color=color)
        ax1.plot(self.data['Actual'], color=color)
        ax1.tick_params(axis='y', labelcolor=color)
        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
        color = 'tab:red'
        ax2.set_ylabel('Total Value', color=color)
        ax2.plot(self.data['Total'], color=color)
        ax2.tick_params(axis='y', labelcolor=color)
        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        plt.title('Actual Prices and Portfolio Value Over Time')
        plt.savefig('portfolio_values.png')  # Save figure as .png

def main():
    input_sql_file='sql_files/test.sql'
    df = generate_df_from_sql_file(input_sql_file, db)

    # start_date = '2023-07-14'
    # end_date = '2023-07-15'
    # date_mask = (df['timestamp'] >= start_date) & (df['timestamp'] < end_date)
    # time_mask = (df['timestamp'].dt.time >= pd.to_datetime('17:00:00').time()) & (df['timestamp'].dt.time <= pd.to_datetime('17:25:00').time())
    # df = df[date_mask & time_mask]
    # print(df.info())

    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC') #adding this to update to utc

    # Define your parameters
    n_features = 5
    time_steps = 60  # Define your time_steps
    look_ahead = 5  # Define your look_ahead


    # Initialize your classes
    preprocessor = DataProcessor(df)  # Use your actual preprocessor class and its parameters
    model_builder = ModelBuilder(n_features, time_steps)  # Use your actual model builder class and its parameters
    predictor = Predictor(model=None, preprocessor=preprocessor)  # Use your actual predictor class and its parameters
    backtester = Backtester(df, initial_balance=10000, preprocessor=preprocessor, model_builder=model_builder, predictor=predictor, time_steps=time_steps, look_ahead=look_ahead, num_runs=1)
    backtest_results = backtester.run()

    # Print out the backtest results
    print(backtest_results)

    # You can also calculate and print out the metrics
    metrics = backtester.calculate_metrics()
    for metric, value in metrics.items():
        print(f'{metric}: {value}')

    # And plot the portfolio values over time
    backtester.plot_portfolio_values()

if __name__ == "__main__":
    main()