import sys
sys.path.append("..")



import time
import pandas as pd
from databaseClass import DB
import passwords
from sql_files import queries
from datetime import datetime


userName = passwords.userName
userPass = passwords.userPass
dataBaseName = passwords.dataBaseName
host = passwords.host
tableName = 'pairs_live_trading'

db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host=host, docker=False)

