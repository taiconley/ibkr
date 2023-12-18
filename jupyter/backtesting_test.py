import sys
#sys.path.append("/ibkr")
sys.path.append("..")

import os
import datetime
import pandas as pd
import time
import numpy as np
import matplotlib.pyplot as plt


from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from statsmodels.tsa.stattools import coint
import itertools

import pytz

import backtrader as bt
import statsmodels.api as sm

import passwords
from databaseClass import DB
from utils import generate_df_from_sql_file, generate_list_from_sql_file
from utils import DataProcessor
from utils import ModelBuilder
from utils import Predictor


userName = passwords.userName
userPass = passwords.userPass
dataBaseName = passwords.dataBaseName
host = passwords.host

db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host=host, docker=False)

df = db.DBtoDF("SELECT * FROM pairs")
dates_to_drop = ['2022-08-08', '2022-08-09', '2023-08-08', '2023-08-09']  # Replace with the actual dates you want to drop
df = df[~df['date'].isin(dates_to_drop)]  # This will remove rows with specified dates
df.set_index('date', inplace=True)


# 2. Extract SPY data and calculate returns
spy_df = df[df['ticker'] == 'SPY']
spy_df = spy_df.sort_values(by='date')  # Ensure data is sorted by date
spy_df['daily_return'] = spy_df['close'].pct_change()  # Compute daily returns
spy_returns = spy_df['daily_return'].tolist()[1:]  # Convert to list and exclude the first NaN value

# 3. Remove SPY from the original dataframe
df = df[df['ticker'] != 'SPY']

def build_pairs(df, correlation_threshold, coint_p_value_threshold):

#     df = df.set_index('date')

    # Reshape the dataframe so that each column is a ticker's close prices
    df_close = df.pivot(columns='ticker', values='close')

    # Calculate the correlation matrix
    corr_matrix = df_close.corr()

    # Find pairs of tickers where correlation is above correlation_threshold
    correlated_pairs = []
    for i in range(corr_matrix.shape[0]):
        for j in range(i+1, corr_matrix.shape[1]):
            if corr_matrix.iloc[i, j] > correlation_threshold:
                correlated_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j]))    
    
    # Apply the cointegration test to these pairs
    cointegrated_pairs = []
    for pair in correlated_pairs:
        if df_close[pair[0]].isnull().any() or df_close[pair[1]].isnull().any() or np.isinf(df_close[pair[0]]).any() or np.isinf(df_close[pair[1]]).any():
            #print(df_close[pair[0]])
            #print("DataFrame contains NaN or inf values.")
            continue
        score, pvalue, _ = coint(df_close[pair[0]], df_close[pair[1]])
        if pvalue < coint_p_value_threshold:
            cointegrated_pairs.append((pair[0], pair[1], pvalue))
            
    # Sort the cointegrated pairs by their p-value in ascending order
    cointegrated_pairs.sort(key=lambda x: x[2])

    return correlated_pairs, cointegrated_pairs

correlated_pairs, cointegrated_pairs = build_pairs(df, .98, .01)
### below is a modification of above, where I calculate daily pnl, my own alpha, beta, and my own sharpe

initial_investment=100000

def main_function(lookback, thresh, exit_thresh, num_pairs, initial_investment=100000):

    class MeanReversion(bt.Strategy):
        params = {
            'lookback': lookback,
            'thresh': thresh,
            'exit_thresh': exit_thresh,
            'pair_index': 0 

        }

        def __init__(self):
            self.data0 = self.getdatabyname(f"{self.params.pair_index}_0")
            self.data1 = self.getdatabyname(f"{self.params.pair_index}_1")

            self.spread = self.data0.close / self.data1.close
            self.mean = bt.indicators.SimpleMovingAverage(self.spread, period=self.params.lookback)
            self.std = bt.indicators.StdDev(self.spread, period=self.params.lookback)    
            self.daily_values = []
            
        def next(self):
            if self.getposition(self.data0).size:
                if abs(self.spread[0] - self.mean[0]) < self.params.exit_thresh * self.std[0]:
                    self.close(data=self.data0)
                    self.close(data=self.data1)
            elif self.spread[0] > self.mean[0] + self.params.thresh * self.std[0]:
                self.sell(data=self.data0, size=1000/self.data0.open[0])
                self.buy(data=self.data1, size=1000/self.data1.open[0])
            elif self.spread[0] < self.mean[0] - self.params.thresh * self.std[0]:
                self.buy(data=self.data0, size=1000/self.data0.open[0])
                self.sell(data=self.data1, size=1000/self.data1.open[0])    
                
            self.daily_values.append(self.broker.getvalue())
        
    def recursive_merge_dicts(dict1, dict2):
        """Merge two dictionaries recursively."""
        for key, value in dict2.items():
            if key in dict1:
                if isinstance(value, dict) and isinstance(dict1[key], dict):
                    recursive_merge_dicts(dict1[key], value)
                else:
                    dict1[key] += value
            else:
                dict1[key] = value
        return dict1
    
    def calculate_metrics(daily_values, risk_free_rate=0.01/252):

        daily_returns = [(daily_values[i] / daily_values[i-1]) - 1 for i in range(1, len(daily_values))]
        mean_return = np.mean(daily_returns)
        std_return = np.std(daily_returns)
        sharpe_ratio = (mean_return - risk_free_rate) / std_return
        return sharpe_ratio
    
        
    def calculate_alpha_beta(daily_values, spy_returns, risk_free_rate=0.01/252):
        daily_returns = [(daily_values[i] / daily_values[i-1]) - 1 for i in range(1, len(daily_values))]
        if len(daily_returns) != len(spy_returns):
            raise ValueError("Length mismatch between strategy returns and benchmark returns.")

        excess_returns = np.array(daily_returns) - risk_free_rate
        excess_benchmark = np.array(spy_returns) - risk_free_rate

        X = sm.add_constant(excess_benchmark)
        model = sm.OLS(excess_returns, X).fit()
        alpha, beta = model.params

        return alpha, beta


    def run_cumulative_backtest(pairs, starting_cash, spy_returns):
        cerebro = bt.Cerebro()
        for idx, pair in enumerate(pairs):
            data1 = bt.feeds.PandasData(dataname=df[df['ticker'] == pair[0]], plot=False, name=f"{idx}_0")
            data2 = bt.feeds.PandasData(dataname=df[df['ticker'] == pair[1]], plot=False, name=f"{idx}_1")

            cerebro.adddata(data1)
            cerebro.adddata(data2)
            cerebro.addstrategy(MeanReversion, pair_index=idx)

        cerebro.broker.setcash(starting_cash)
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='mysharpe')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='mytrades')

        results = cerebro.run()

        # Collate the results
        final_value = cerebro.broker.getvalue()
        all_daily_values = []
        for r in results:
            all_daily_values.extend(r.daily_values)

        all_daily_pnl = [all_daily_values[i] - all_daily_values[i-1] for i in range(1, len(all_daily_values))]
        sharpe_ratio = calculate_metrics(all_daily_values)
        alpha, beta = calculate_alpha_beta(all_daily_values, spy_returns)

        trade_analysis = {}
        for r in results:
            trade_analysis = recursive_merge_dicts(trade_analysis, r.analyzers.mytrades.get_analysis())

        return {
            "final_value": final_value,
            "alpha": alpha,
            "beta": beta,
            "sharpe_ratio": sharpe_ratio,
            "trade_analysis": trade_analysis
        }



    result = run_cumulative_backtest(cointegrated_pairs[0:num_pairs], initial_investment, spy_returns)
    return result


def display_result(result, initial_investment):
    print("="*40)
    print("Backtest Results")
    print("="*40)
    print(f"Final Value: ${result['final_value']:.2f}")
    
    total_return = ((result['final_value'] / initial_investment) - 1) * 100
    print(f"Total Return: {total_return:.2f}%")
    print(f"Sharpe Ratio: {result['sharpe_ratio']:.2f}")
    print("-"*40)

    trades = result['trade_analysis']

    print("Trade Analysis:")
    print("-"*40)
    print(f"Total Trades: {trades['total']['total']}")
    print(f"Open Trades: {trades['total']['open']}")
    print(f"Closed Trades: {trades['total']['closed']}")
    print(f"Longest Winning Streak: {trades['streak']['won']['longest']}")
    print(f"Longest Losing Streak: {trades['streak']['lost']['longest']}")
    print("-"*40)

    print("Profit/Loss Analysis:")
    print("-"*40)
    print(f"Total Gross Profit/Loss: ${trades['pnl']['gross']['total']:.2f}")
    print(f"Total Net Profit/Loss: ${trades['pnl']['net']['total']:.2f}")
    print(f"Total Winning Trades Value: ${trades['won']['pnl']['total']:.2f}")
    print(f"Total Losing Trades Value: ${trades['lost']['pnl']['total']:.2f}")
    print("-"*40)

    print("Trade Length Analysis:")
    print("-"*40)
    print(f"Total Trade Length: {trades['len']['total']}")
    print(f"Average Trade Length: {trades['len']['average']:.2f}")
    print(f"Max Trade Length: {trades['len']['max']}")
    print(f"Min Trade Length: {trades['len']['min']}")
    print("-"*40)

    print("Trade Types Analysis:")
    print("-"*40)
    print(f"Total Long Trades: {trades['long']['total']}")
    print(f"Total Short Trades: {trades['short']['total']}")
    print(f"Winning Long Trades: {trades['long']['won']}")
    print(f"Losing Long Trades: {trades['long']['lost']}")
    print(f"Winning Short Trades: {trades['short']['won']}")
    print(f"Losing Short Trades: {trades['short']['lost']}")

    print("="*40)
    
# Define parameter grid
lookback_values = [10, 20, 30, 40, 50]
thresh_values = [1, 1.5, 2, 2.5]
exit_thresh_values = [0.5, 1, 1.5, 2]
num_pairs_values = [10, 20, 25]


# Store best values
best_sharpe = float('-inf')
best_params = {}
results_list = []

# Grid search
for lookback in lookback_values:
    for thresh in thresh_values:
        for exit_thresh in exit_thresh_values:
            for num_pairs in num_pairs_values:
                
                # Run main_function with the current parameters
                result = main_function(lookback, thresh, exit_thresh, num_pairs)
                
                # Store the results
                results_list.append({
                    'lookback': lookback,
                    'thresh': thresh,
                    'exit_thresh': exit_thresh,
                    'num_pairs': num_pairs,
                    'sharpe_ratio': result['sharpe_ratio'],
                    'full_result': result   # Storing the entire result

                })
                
                # Update best parameters if current run is better
                if result['sharpe_ratio'] > best_sharpe:
                    best_sharpe = result['sharpe_ratio']
                    best_params = {
                        'lookback': lookback,
                        'thresh': thresh,
                        'exit_thresh': exit_thresh,
                        'num_pairs': num_pairs
                    }
                    
df_results = pd.DataFrame(results_list)
df_results = df_results.sort_values(by='sharpe_ratio', ascending=False)
print("Best Parameters:", best_params)


for _, row in df_results.head(5).iterrows():
    print("\n==============================")
    print(f"Parameters: Lookback={row['lookback']}, Thresh={row['thresh']}, Exit Thresh={row['exit_thresh']}, Num Pairs={row['num_pairs']}")
    print("==============================")
    display_result(row['full_result'], initial_investment)