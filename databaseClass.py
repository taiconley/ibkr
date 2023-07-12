import psycopg2
import psycopg2.extras as extras

import pandas as pd
import io
import json

class DB:

    def __init__(self, userName, userPass, dataBaseName, host, docker=False):
        self.userName = userName
        self.userPass = userPass
        self.dataBaseName = dataBaseName
        self.host = host
        self.docker = docker
        if self.docker:
            self.dbEngineText = 'postgresql+psycopg2://'+self.userName+':'+self.userPass+'@'+self.host+':5432/'+self.dataBaseName
        else:
            self.dbEngineText = 'postgresql+psycopg2://'+self.userName+':'+self.userPass+'@'+self.host+':5434/'+self.dataBaseName
        

        def get_connection(self):
            return create_engine(self.dbEngineText)

        def lstTables(self):
            query_listTables = '''
            SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'
            '''
            conn = self.connect()
            cur = conn.cursor()
            cur.execute(query_listTables)
            # conn.commit()
            tables = cur.fetchall()
            tables = [table[0] for table in tables]
            conn.close()
            return tables
        self.tables = lstTables(self)
            

    def connect(self):
        if self.docker:
            conn = psycopg2.connect(dbname=self.dataBaseName, user=self.userName, password=self.userPass, host="ibkr_db", port="5432")
        else: 
            conn = psycopg2.connect(dbname=self.dataBaseName, user=self.userName, password=self.userPass, host=self.host, port="5434")
        return conn

    def buildTable(self, tableName, fieldList):
        '''builds a new table in database
           fieldList example below:
            fieldList = triplequotesgohere(
            FIRST_NAME CHAR(20) NOT NULL,
            LAST_NAME CHAR(20),
            AGE INT,
            SEX CHAR(1),
            INCOME FLOAT
            )triplequotesgohere
        '''
        if fieldList is None:
            print('There is no schema')
        else:
            query_make_table = '''
            CREATE TABLE {}{};
            '''.format(tableName, fieldList)
            conn = self.connect()
            cur = conn.cursor()
            cur.execute(query_make_table)
            conn.commit()
            conn.close()


    def dropTable(self, tableName):
        '''remove database table
        tableName is the table to drop'''
        query_drop = '''
        DROP TABLE {}
        '''.format(tableName)
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(query_drop)
        conn.commit()
        conn.close()


    def DFtoDB(self, df, tableName):
        """
        Using psycopg2.extras.execute_values() to insert the dataframe
        """
        # Create a list of tupples from the dataframe values
        tuples = [tuple(x) for x in df.to_numpy()]
        # Comma-separated dataframe columns
        cols = ','.join(list(df.columns))
        # SQL quert to execute
        query  = "INSERT INTO %s(%s) VALUES %%s" % (tableName, cols)
        conn = self.connect()
        cursor = conn.cursor()
        try:
            extras.execute_values(cursor, query, tuples)
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: %s" % error)
            conn.rollback()
            cursor.close()
            return 1
        #print("execute_values() done")
        cursor.close()


    def DBtoDF(self, query):
        '''runs query and returns df'''
        conn = self.connect()
        df = pd.read_sql_query(query, con=conn)
        return df

    def DBtoList(self, query):
        '''runs query and returns a list'''
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        list_result = [list(row) for row in rows]
        return list_result

    def addPrediction(self, timestamp, current_price, predicted_price, decision):
        query = f'''
        INSERT INTO predictions
        (timestamp, current_price, predicted_price, decision)
        VALUES
        (%s, %s, %s, %s)
        '''
        conn = self.connect()
        cur = conn.cursor()
        # convert numpy data types to native Python data types
        cur.execute(query, (timestamp, float(current_price), float(predicted_price), decision))
        conn.commit()
        conn.close()



    def addAccountSummary(self, timestamp, key, val, currency, accountName):
        query = f'''
        INSERT INTO account_summary
        (timestamp, key, val, currency, accountName)
        VALUES
        (%s, %s, %s, %s, %s)
        '''
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(query, (timestamp, key, val, currency, accountName))
        conn.commit()
        conn.close()

    def addPortfolio(self, timestamp, contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL, accountName):
        query = f'''
        INSERT INTO portfolio 
        (timestamp, contract_symbol, contract_secType, contract_currency, contract_exchange, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL, accountName) 
        VALUES 
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

        conn = self.connect()
        cur = conn.cursor()
        cur.execute(query, (timestamp, contract.symbol, contract.secType, contract.currency, contract.exchange, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL, accountName))
        conn.commit()
        conn.close()

    def addPosition(self,timestamp, reqId, account, modelCode, contract, pos, avgCost):
        query = f'''
        INSERT INTO positions
        (timestamp, reqId, account, modelCode, symbol, secType, currency, exchange, pos, avgCost)
        VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(query, (timestamp, reqId, account, modelCode, contract.symbol, contract.secType, contract.currency, contract.exchange, pos, avgCost))
        conn.commit()
        conn.close()

    
            
if __name__ == '__main__':
    pass