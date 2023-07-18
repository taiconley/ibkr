import sys
sys.path.append("/ibkr")
import passwords
from databaseClass import DB
from sql_files import queries
from flask import Flask, jsonify, render_template



userName = passwords.userName
userPass = passwords.userPass
dataBaseName = passwords.dataBaseName
host = passwords.host

app = Flask(__name__)

# Replace these with your actual PostgreSQL credentials
db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host='ibkr_db', docker=True)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/monitor', methods=['GET'])
def monitor():
    last_tick = db.DBtoValue(queries.sql_last_tick)
    total_ticks = "{:,.0f}".format(db.DBtoValue(queries.sql_total_ticks))
    buying_power = "${:,.2f}".format(float(db.DBtoValue(queries.sql_buying_power)))
    total_ES_positions = db.DBtoValue(queries.sql_total_ES_positions)
    gross_position_value = "${:,.2f}".format(float(db.DBtoValue(queries.sql_gross_position_value)))
    current_live_price = db.DBtoValue(queries.sql_current_live_price)
    current_predicted_price = db.DBtoValue(queries.sql_current_predicted_price)
    current_predicted_price_ratio = round((current_predicted_price / current_live_price) * 100, 2) if current_live_price else None
    current_predicted_price = "${:,.2f}".format(current_predicted_price) 
    unrealized_pnl = "${:,.2f}".format(float(db.DBtoValue(queries.sql_unrealized_pnl)))
    realized_pnl = "${:,.2f}".format(float(db.DBtoValue(queries.sql_realized_pnl)))
    cash_balance = "${:,.2f}".format(float(db.DBtoValue(queries.sql_cash_balance)))


    return jsonify({
        'getData': {
            'last_tick': last_tick,
            'total_ticks': total_ticks
        },
        'accountSummary': {
            'buying_power': buying_power,
            'total_ES_positions': total_ES_positions,
            'gross_position_value': gross_position_value,
            'unrealized_pnl': unrealized_pnl,
            'realized_pnl': realized_pnl,
            'cash_balance': cash_balance
        },
        'liveTrading': {
            'current_live_price': current_live_price,
            'current_predicted_price': current_predicted_price,
            'predicted_live_price_ratio': current_predicted_price_ratio
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8003, debug=True)
