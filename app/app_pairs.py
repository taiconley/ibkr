import sys
# sys.path.append("/ibkr")
sys.path.append("..")

import passwords
from databaseClass import DB
from sql_files import queries
from flask import Flask, jsonify, render_template
import pandas as pd
import numpy as np
import datetime

userName = passwords.userName
userPass = passwords.userPass
dataBaseName = passwords.dataBaseName
host = passwords.host

app = Flask(__name__)

# Replace these with your actual PostgreSQL credentials
# db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host='ibkr_db', docker=True)
db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host=host, docker=False)

pairs = db.DBtoDF(queries.sql_pairs_tickers)

def get_data_for_real_time(n):
    '''
    n is the number of rows to include for each ticker.  each row represents 5 seconds of aggregated data
    '''
    
    query = f'''
                SELECT * FROM (
                    SELECT *, ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) as rn
                    FROM pairs_live_trading
                ) t
                WHERE t.rn <= {n}
                '''.format(n)

    df = db.DBtoDF(query)
    
    dates = df['date'].drop_duplicates().to_list()
    pairs = db.DBtoDF('SELECT * FROM pairs_ticker_list')
    
    #expanding the pairs for each ticker pair and each timeframe
    expanded_pairs = pairs.loc[np.repeat(pairs.index.values, len(dates))]
    expanded_pairs['Date'] = np.tile(dates, len(pairs))
    expanded_pairs = expanded_pairs.rename(columns={'ticker1': 'Ticker1',
                                                    'ticker2': 'Ticker2'})

    merged = pd.merge(expanded_pairs, df, left_on=['Ticker1', 'Date'], right_on=['ticker', 'date'], how='left')
    merged = merged.rename(columns={
                                'open': 'open_ticker1',
                                'high': 'high_ticker1',
                                'low': 'low_ticker1',
                                'close': 'close_ticker1',
                                'volume': 'volume_ticker1',
                                'count': 'count_ticker1',
                                'wap': 'wap_ticker1',
                                'rn': 'rn_ticker1',

                            })

    merged = pd.merge(merged, df, left_on=['Ticker2', 'Date'], right_on=['ticker', 'date'], how='left')
    merged = merged.rename(columns={
                                'open': 'open_ticker2',
                                'high': 'high_ticker2',
                                'low': 'low_ticker2',
                                'close': 'close_ticker2',
                                'volume': 'volume_ticker2',
                                'count': 'count_ticker2',
                                'wap': 'wap_ticker2',
                                'rn': 'rn_ticker2',

                            })
    merged = merged.drop(['date_x', 'ticker_x', 'date_y', 'ticker_y'], axis=1)
    merged['open_ratio'] = merged['open_ticker1'] / merged['open_ticker2']
    merged['high_ratio'] = merged['high_ticker1'] / merged['high_ticker2']
    merged['low_ratio'] = merged['low_ticker1'] / merged['low_ticker2']
    merged['wap_ratio'] = merged['wap_ticker1'] / merged['wap_ticker2']
    columns_to_aggregate = [col for col in merged.columns if col not in ['Ticker1', 'Ticker2', 'Date']]
    aggregation_functions = {col: ['mean', 'std'] for col in columns_to_aggregate}
    aggregated_df = merged.groupby(['Ticker1', 'Ticker2']).agg(aggregation_functions)
    aggregated_df.columns = ['_'.join(col).strip() for col in aggregated_df.columns.values]
    aggregated_df.reset_index(inplace=True)
    aggregated_df = aggregated_df.drop(['rn_ticker1_mean', 'rn_ticker1_std', 'rn_ticker2_mean', 'rn_ticker2_std',
                                        'high_ticker1_mean', 'high_ticker1_std', 'high_ticker2_mean', 'high_ticker2_std',
                                        'low_ticker1_mean', 'low_ticker1_std', 'low_ticker2_mean', 'low_ticker2_std',
                                        'close_ticker1_mean', 'close_ticker1_std', 'close_ticker2_mean', 'close_ticker2_std',
                                        'high_ratio_mean', 'high_ratio_std',
                                        'low_ratio_mean', 'low_ratio_std' 
                                        # 'close_ratio_mean', 'close_ratio_std'
                                        ], 
                                        axis=1)
    timestamp = pd.Timestamp.now(tz='UTC')
    aggregated_df['timestamp'] = timestamp
    return aggregated_df



@app.route('/')
def home():
    df5 = get_data_for_real_time(5)
    df30 = get_data_for_real_time(30)

    db.DFtoDB(df5, 'pairs_live_analyzed_data_30_seconds') 
    db.DFtoDB(df30, 'pairs_live_analyzed_data_300_seconds') 

    df5_html = df5.to_html(classes='table table-striped')
    df30_html = df30.to_html(classes='table table-striped')

    return render_template('index_2.html', tables=[df5_html, df30_html])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)