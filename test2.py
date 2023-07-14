from databaseClass import DB
import passwords

userName = passwords.userName
userPass = passwords.userPass
dataBaseName = passwords.dataBaseName
host = passwords.host

db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host=host, docker=False)


fieldList = '''(
            tickType INT,
            Price FLOAT,
            Volume INT,
            timestamp TIMESTAMP
)
'''

db.buildTable("TickData_jul13", fieldList)

#db.dropTable("TickData_jun14")

# print(db.tables)

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

