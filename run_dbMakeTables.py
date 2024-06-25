from databaseClass import DB
import passwords
from sql_files import queries

userName = passwords.userName
userPass = passwords.userPass
dataBaseName = passwords.dataBaseName
host = passwords.host

db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host=host, docker=False)

# db.dropTable(queries.tickdata_date)

# fieldList = '''(
#             tickType INT,
#             Price FLOAT,
#             Volume INT,
#             timestamp TIMESTAMP
# )
# '''

# db.buildTable(queries.tickdata_date, fieldList)

# db.dropTable(f"{queries.tickdata_date}_l2")
# fieldList_l2table = '''(
#             position INT,
#             operation INT,
#             side INT,
#             price FLOAT,
#             size INT,
#             timestamp TIMESTAMP
# )
# '''

# db.buildTable(f"{queries.tickdata_date}_l2", fieldList_l2table)


# db.dropTable("pairs")
# fieldList_historical_pairs_data = '''(
#             date TIMESTAMP,
#             ticker VARCHAR(10),
#             open FLOAT,
#             high FLOAT,
#             low FLOAT,
#             close FLOAT,
#             volume INT,
#             count INT,
#             WAP FLOAT
# )'''
# db.buildTable("pairs", fieldList_historical_pairs_data)

# db.dropTable("pairs_daily")
# fieldList_historical_pairs_data = '''(
#             date TIMESTAMP,
#             ticker VARCHAR(10),
#             open FLOAT,
#             high FLOAT,
#             low FLOAT,
#             close FLOAT,
#             volume INT,
#             count INT,
#             WAP FLOAT
# )'''
# db.buildTable("pairs_daily", fieldList_historical_pairs_data)




# db.dropTable("pairs_hourly")
# fieldList_historical_pairs_hourly = '''(
#             date TIMESTAMP,
#             ticker VARCHAR(10),
#             open FLOAT,
#             high FLOAT,
#             low FLOAT,
#             close FLOAT,
#             volume INT,
#             count INT,
#             WAP FLOAT
# )'''
# db.buildTable("pairs_hourly", fieldList_historical_pairs_hourly)

db.dropTable("pairs_live_calculated_metrics")
fieldList_pairs_live_calculated_metrics = '''(
                        date TIMESTAMP,
                        ticker_stock1 VARCHAR(10),
                        open_stock1	FLOAT,
                        high_stock1	FLOAT,
                        low_stock1	FLOAT,
                        close_stock1 FLOAT,
                        volume_stock1 FLOAT,
                        count_stock1 FLOAT,
                        wap_stock1	FLOAT,
                        ticker_stock2	VARCHAR(10),
                        open_stock2	FLOAT,
                        high_stock2 FLOAT,
                        low_stock2 FLOAT,
                        close_stock2 FLOAT,
                        volume_stock2 FLOAT,
                        count_stock2 FLOAT,
                        wap_stock2 FLOAT,
                        spread FLOAT,
                        mean_spread FLOAT,
                        std_spread FLOAT,
                        z_score FLOAT,
                        signal VARCHAR(30)
)'''
db.buildTable("pairs_live_calculated_metrics", fieldList_pairs_live_calculated_metrics)



# db.dropTable("pairs_live_trading")
# fieldList_pairs_live_trading = '''(
#             date TIMESTAMP,
#             ticker VARCHAR(10),
#             open FLOAT,
#             high FLOAT,
#             low FLOAT,
#             close FLOAT,
#             volume INT,
#             count INT,
#             WAP FLOAT
# )'''
# db.buildTable("pairs_live_trading", fieldList_pairs_live_trading)

# db.dropTable("pairs_live_analyzed_data_30_seconds")
# db.dropTable("pairs_live_analyzed_data_300_seconds")

# fieldList_pairs_live_analyzed_data = '''(
#             timestamp TIMESTAMP,
#             Ticker1 VARCHAR(10),
#             Ticker2	VARCHAR(10),
#             open_ticker1_mean FLOAT,
#             open_ticker1_std FLOAT,
#             volume_ticker1_mean FLOAT,
#             volume_ticker1_std FLOAT,
#             count_ticker1_mean FLOAT,
#             count_ticker1_std FLOAT,
#             wap_ticker1_mean FLOAT,
#             wap_ticker1_std FLOAT,
#             open_ticker2_mean FLOAT,
#             open_ticker2_std FLOAT,
#             volume_ticker2_mean FLOAT,
#             volume_ticker2_std FLOAT,
#             count_ticker2_mean FLOAT,
#             count_ticker2_std FLOAT,
#             wap_ticker2_mean FLOAT,
#             wap_ticker2_std FLOAT,
#             open_ratio_mean FLOAT,
#             open_ratio_std FLOAT,
#             wap_ratio_mean FLOAT,
#             wap_ratio_std FLOAT
            
# )'''
# db.buildTable("pairs_live_analyzed_data_30_seconds", fieldList_pairs_live_analyzed_data)
# db.buildTable("pairs_live_analyzed_data_300_seconds", fieldList_pairs_live_analyzed_data)




# print(db.tables)

# db.dropTable("predictions")

# fieldList_predictions = '''
#     (
#     timestamp TIMESTAMP NOT NULL,
#     current_price FLOAT,
#     predicted_price FLOAT,
#     decision CHAR(50)
#     )
# '''
# db.buildTable('predictions', fieldList_predictions)

# db.dropTable("account_summary")
# db.dropTable("positions")
# db.dropTable("portfolio")

# account_summary_field_list = '''
#     (
#     timestamp TIMESTAMP NOT NULL,
#     key CHAR(50),
#     val CHAR(50),
#     currency CHAR(10),
#     accountName CHAR(100)
#     )
# '''

# db.buildTable('account_summary', account_summary_field_list)

# portfolio_field_list = '''
#     (
#     timestamp TIMESTAMP NOT NULL,
#     contract_symbol CHAR(50),
#     contract_secType CHAR(10),
#     contract_currency CHAR(10),
#     contract_exchange CHAR(50),
#     position FLOAT,
#     marketPrice FLOAT,
#     marketValue FLOAT,
#     averageCost FLOAT,
#     unrealizedPNL FLOAT,
#     realizedPNL FLOAT, 
#     accountName CHAR(50)
#     )
# '''
# db.buildTable('portfolio', portfolio_field_list)


# positions_field_list = '''
#     (
#     timestamp TIMESTAMP NOT NULL,
#     reqId INT, 
#     account CHAR(50), 
#     modelCode CHAR(50), 
#     symbol CHAR(50),
#     secType CHAR(10),
#     currency CHAR(10),
#     exchange CHAR(50),
#     pos FLOAT, 
#     avgCost FLOAT
#     )
# '''
# db.buildTable('positions', positions_field_list)

