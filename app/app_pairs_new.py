import sys
sys.path.append("..")

from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from databaseClass import DB  # Your custom database class
import passwords

app = Flask(__name__)

# Database setup
db = DB(userName=passwords.userName, userPass=passwords.userPass, dataBaseName=passwords.dataBaseName, host=passwords.host)

@app.route('/', methods=['GET', 'POST'])
def index():
    pairs = get_all_pairs()  # Fetch all available pairs for dropdown
    selected_pair = request.args.get('pair', default=f"{pairs[0]['ticker_stock1']},{pairs[0]['ticker_stock2']}")  # Default to the first pair
    ticker1, ticker2 = selected_pair.split(',')
    
    if request.method == 'POST':
        # This endpoint could be used for Ajax calls to update data
        z_scores = get_z_scores(ticker1, ticker2, 30)  # Get last 30 z_scores for selected pair
        return jsonify(z_scores)
    
    # On initial page load or when not an Ajax request
    z_scores = get_z_scores(ticker1, ticker2, 30)
    last_z_scores = get_last_z_scores()  # Get last z_score for all pairs
    
    return render_template('index_app_pairs_new.html', pairs=pairs, z_scores=z_scores, last_z_scores=last_z_scores, selected_pair=selected_pair)

def get_all_pairs():
    query = "SELECT DISTINCT ticker_stock1, ticker_stock2 FROM pairs_live_calculated_metrics"
    df = db.DBtoDF(query)
    return df.to_dict(orient='records')

def get_z_scores(ticker1, ticker2, limit):
    query = f"""
        SELECT date, z_score FROM pairs_live_calculated_metrics
        WHERE ticker_stock1 = '{ticker1}' AND ticker_stock2 = '{ticker2}'
        ORDER BY date DESC LIMIT {limit}
    """
    df = db.DBtoDF(query)
    return df.sort_values('date').to_dict(orient='records')

def get_last_z_scores():
    query = """
        SELECT ticker_stock1, ticker_stock2, z_score FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY ticker_stock1, ticker_stock2 ORDER BY date DESC) as rn
            FROM pairs_live_calculated_metrics
        ) t WHERE rn = 1
    """
    df = db.DBtoDF(query)
    return df.to_dict(orient='records')

@app.route('/update_chart')
def update_chart():
    selected_pair = request.args.get('pair')
    ticker1, ticker2 = selected_pair.split(',')
    z_scores = get_z_scores(ticker1, ticker2, 30)  # Function to fetch the last 30 z_score entries
    return jsonify(z_scores)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8001)