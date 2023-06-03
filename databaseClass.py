import psycopg2
import psycopg2.extras as extras

import pandas as pd
import io
import json

class DB:

    def __init__(self, userName, userPass, dataBaseName, host):
        self.userName = userName
        self.userPass = userPass
        self.dataBaseName = dataBaseName
        self.host = host
        # self.dbEngineText = 'postgresql+psycopg2://'+self.userName + \
        #     ':'+self.userPass+'db:5432/'+self.dataBaseName

        self.dbEngineText = 'postgresql+psycopg2://'+self.userName + \
            ':'+self.userPass+'@'+self.host+':5434/'+self.dataBaseName

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
        conn = psycopg2.connect(dbname=self.dataBaseName, user=self.userName, password=self.userPass, host=self.host, port=5434)
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

    
if __name__ == '__main__':
    pass