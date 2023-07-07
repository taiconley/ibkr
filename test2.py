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

db.buildTable("TickData_jul6", fieldList)

#db.dropTable("TickData_jun14")

print(db.tables)