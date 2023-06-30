import os
import datetime
import pandas as pd
import time
import numpy as np
import matplotlib.pyplot as plt


from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

import tensorflow as tf
from tensorflow.keras.models import load_model
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout
import pytz


import passwords
from databaseClass import DB
from utils import generate_df_from_sql_file, generate_list_from_sql_file
from utils import DataProcessor
from utils import ModelBuilder
from utils import Predictor


userName = passwords.userName
userPass = passwords.userPass
dataBaseName = passwords.dataBaseName
host = 'localhost'

db = DB(userName=userName, userPass=userPass, dataBaseName=dataBaseName, host=host, docker=False)

# input_sql_file='sql_files/test.sql'
df = db.DBtoDF(f"SELECT * FROM tickdata_jun29")

def main_build_model(df, look_ahead=5, TIME_STEPS=60):
    
    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC') #adding this to update to utc

    # Create a DataProcessor instance
    processor = DataProcessor(df) 
    # Process the df
    processor.process_df()
    
    # Scale and shift the data
    scaler, close_scaler = processor.scale_shift_data(look_ahead)
    # Create the X and y datasets
    X, y = processor.scaled_df, processor.shifted_df['Close']
    # Create train test split
    X_train, X_test, y_train, y_test = processor.create_train_test_split(X, y)
    # Create final train and test datasets
    # TIME_STEPS = 60
    X_train, y_train = processor.create_dataset(X_train, y=y_train, time_steps=TIME_STEPS, for_training=True, look_ahead=look_ahead)
    X_test, y_test = processor.create_dataset(X_test, y=y_test, time_steps=TIME_STEPS, for_training=True, look_ahead=look_ahead)
    # Number of features in the data
    n_features = X_train.shape[2]
    
    # Create a ModelBuilder instance and build the model
    builder = ModelBuilder(n_features, TIME_STEPS)
    # Train the model
    model, history = builder.train_model(X_train, y_train, X_test, y_test, epochs=20, batch_size=64)
    # Save the model
    model_path = 'models/model.h5'
    builder.save_model(model_path)
    # Plot loss
    # builder.plot_loss(history) #this needs to save vs show

if __name__ == "__main__":
    main_build_model(df, look_ahead=5, TIME_STEPS=60)