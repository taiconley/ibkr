import sys
sys.path.append("/ibkr")
import passwords
from databaseClass import DB
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
	last_tick = db.DBtoValue("SELECT timestamp FROM tickdata_jul13 ORDER BY timestamp DESC LIMIT 1")
	ticks_in_last_5_seconds = db.DBtoValue("SELECT COUNT(*) FROM tickdata_jul13")
	
	#buying_power, total_ES_positions = db.DBtoValue("SELECT buying_power, total_ES_positions FROM account_summary ORDER BY timestamp DESC LIMIT 1")
	#current_live_price, current_predicted_price = db.DBtoValue("SELECT current_live_price, current_predicted_price FROM predictions ORDER BY timestamp DESC LIMIT 1")
	
	buying_power = 4000
	total_ES_positions = 2
	current_live_price = 2750
	current_predicted_price = 2751

	return jsonify({
        'getData': {
            'last_tick': last_tick,
            'ticks_in_last_5_seconds': ticks_in_last_5_seconds
        },
        'accountSummary': {
            'buying_power': buying_power,
            'total_ES_positions': total_ES_positions
        },
        'liveTrading': {
            'current_live_price': current_live_price,
            'current_predicted_price': current_predicted_price
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8005, debug=True)
