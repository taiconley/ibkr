import os
from datetime import datetime
from joblib import dump, load
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dropout, Dense
from tensorflow.keras.models import load_model
from tensorflow.keras.callbacks import TensorBoard
from keras_tuner import HyperModel, RandomSearch




def generate_sql(input_sql_file):
    with open(input_sql_file, 'r') as file:
        sql = file.read()
        return sql

def generate_df_from_sql_file(input_sql_file, db):
    sql = (generate_sql(input_sql_file))
    df = db.DBtoDF(sql)
    return df

def generate_list_from_sql_file(input_sql_file, db):
    sql = (generate_sql(input_sql_file))
    lst = db.DBtoList(sql)
    return lst


class DataProcessor:
    def __init__(self, df):
        self.df = df
        self.processed_df = None
        self.scaled_df = None
        self.look_ahead = None  # add this line
        self.scaler = MinMaxScaler(feature_range=(0, 1))  # for entire dataset
        self.close_scaler = MinMaxScaler(feature_range=(0, 1))  # for 'Close' column only



    def process_df(self):
        # Set 'timestamp' as the index
        #df['timestamp'] = df['timestamp'].dt.tz_localize('UTC') 
        self.df = self.df.set_index('timestamp')
        
        # Pivot the table and also include 'volume' where ticktype is 5
        df_pivot = self.df.pivot_table(index=self.df.index, columns='ticktype', values=['price', 'volume'])
        df_pivot.columns = ['_'.join(map(str,i)) for i in df_pivot.columns]
        
        # Resample the data per second and fill forward any NaN values
        df_resampled = df_pivot.resample('1S').agg({'price_1': 'last', 'price_2': 'last', 'price_4': 'last', 'volume_5': 'sum'}).ffill()
        
        # Reshape
        df_resampled['Open'] = df_resampled['price_1']
        df_resampled['High'] = df_resampled[['price_1', 'price_2', 'price_4']].max(axis=1)
        df_resampled['Low'] = df_resampled[['price_1', 'price_2', 'price_4']].min(axis=1)
        df_resampled['Close'] = df_resampled['price_4']
        df_resampled['Volume'] = df_resampled['volume_5']
        self.processed_df = df_resampled[['Open', 'High', 'Low', 'Close', 'Volume']]

    def create_train_test_split(self, X, y, train_ratio=0.8):
        train_size = int(len(X) * train_ratio)
        test_size = len(X) - train_size

        X_train, X_test = X.iloc[0:train_size], X.iloc[train_size:len(X)]
        y_train, y_test = y.iloc[0:train_size], y.iloc[train_size:len(y)]

        return X_train, X_test, y_train, y_test


    def scale_shift_data(self, look_ahead, for_training=True):
        # Normalize the dataset
        scaled = self.scaler.fit_transform(self.processed_df)
        self.close_scaler.fit(self.processed_df[['Close']])  # fit the close_scaler

        # Save the scalers
        dump(self.scaler, 'scaler.joblib')
        dump(self.close_scaler, 'close_scaler.joblib')

        # Convert scaled array into dataframe
        self.scaled_df = pd.DataFrame(scaled, index=self.processed_df.index, columns=self.processed_df.columns)

        if for_training:
            # Shift the dataframe to create the labels
            self.shifted_df = self.scaled_df.shift(-look_ahead)

            # Drop the last 'look_ahead' rows
            self.scaled_df = self.scaled_df.iloc[:-look_ahead]
            self.shifted_df = self.shifted_df.iloc[:-look_ahead]
            self.look_ahead = look_ahead 

        return self.scaler, self.close_scaler  # return both scalers
    
    def create_dataset(self, X, time_steps, for_training=True, y=None, look_ahead=None):
        Xs, ys = [], []
        if for_training:
            if y is None or look_ahead is None:
                raise ValueError("y and look_ahead must not be None in training mode")
            for i in range(len(X) - time_steps - look_ahead):
                v = X.iloc[i:(i + time_steps)].values
                Xs.append(v)        
                ys.append(y.iloc[i + time_steps + look_ahead])
            return np.array(Xs), np.array(ys) # Return X and y in training context
        else:
            for i in range(len(X) - time_steps):
                v = X.iloc[i:(i + time_steps)].values
                Xs.append(v)
            return np.array(Xs)  # Return only X in prediction context


class ModelBuilder:
    def __init__(self, n_features, time_steps):
        self.n_features = n_features
        self.time_steps = time_steps
        self.model = self.build_model()


    def build_model(self):
        model = Sequential()
        model.add(LSTM(units=100, return_sequences=True, input_shape=(self.time_steps, self.n_features)))
        model.add(Dropout(0.2))
        model.add(LSTM(units=100, return_sequences=True))
        model.add(Dropout(0.2))
        model.add(LSTM(units=100, return_sequences=False))
        model.add(Dropout(0.2))
        model.add(Dense(units=32, activation='relu'))
        model.add(Dense(units=1))
        model.compile(optimizer='adam', loss='mean_squared_error', run_eagerly=True)
        return model


    def build_model_with_hyperparameters(self, best_hps):
        model = Sequential()
        model.add(LSTM(units=best_hps.get('units_1'), return_sequences=True, input_shape=(self.time_steps, self.n_features)))
        model.add(Dropout(rate=best_hps.get('dropout_1')))
        model.add(LSTM(units=best_hps.get('units_2'), return_sequences=True))
        model.add(Dropout(rate=best_hps.get('dropout_2')))
        model.add(LSTM(units=best_hps.get('units_3'), return_sequences=False))
        model.add(Dropout(rate=best_hps.get('dropout_3')))
        model.add(Dense(units=best_hps.get('dense_units'), activation='relu'))
        model.add(Dense(units=1))
        model.compile(optimizer='adam', loss='mean_squared_error', run_eagerly=True)
        return model

    def train_model(self, X_train, y_train, X_test, y_test, epochs=20, batch_size=64, best_hps=None):
        if best_hps is not None:
            self.model = self.build_model_with_hyperparameters(best_hps)
        # Specify the log directory for TensorBoard logs
        log_dir = os.path.join(
            "logs",
            "fit",
            "ModelBuilder",
            datetime.now().strftime("%Y%m%d-%H%M%S"),
        )
        # Initialize the TensorBoard callback
        tensorboard_callback = TensorBoard(log_dir=log_dir, histogram_freq=1)

        history = self.model.fit(
            X_train, 
            y_train, 
            epochs=epochs, 
            batch_size=batch_size, 
            validation_data=(X_test, y_test), 
            shuffle=False, 
            callbacks=[tensorboard_callback]  # Add TensorBoard to callbacks
        )
        return self.model, history


    def save_model(self, model_path):
        self.model.save(model_path)

    def load_model(self, model_path):
        self.model = load_model(model_path)

    def plot_loss(self, history):
        plt.plot(history.history['loss'], label='train')
        plt.plot(history.history['val_loss'], label='test')
        plt.legend()
        plt.show()

    def perform_hyperparameter_tuning(self, X_train, y_train, X_test, y_test, max_trials=10, executions_per_trial=3):
        hypermodel = LSTMHyperModel(input_shape=(self.time_steps, self.n_features))

        tuner = RandomSearch(
            hypermodel,
            objective='val_loss',
            max_trials=max_trials,
            executions_per_trial=executions_per_trial,
            directory='random_search',
            project_name='stock_price_prediction'
        )

        tuner.search(x=X_train, 
                     y=y_train, 
                     epochs=5, 
                     validation_data=(X_test, y_test))

        # Get the optimal hyperparameters
        best_hps = tuner.get_best_hyperparameters(num_trials=1)[0]

        return best_hps



class Predictor:
    def __init__(self, model, preprocessor):
        self.model = model
        self.preprocessor = preprocessor

    def prepare_data(self, time_steps, for_training):
        # Load the scalers
        self.preprocessor.scaler = load('scaler.joblib')
        self.preprocessor.close_scaler = load('close_scaler.joblib')

        look_ahead = 0 if not for_training else self.preprocessor.look_ahead  # set look_ahead to 0 if not training
        self.preprocessor.scale_shift_data(look_ahead, for_training=False)
        X = self.preprocessor.scaled_df
        if for_training:
            y = self.preprocessor.shifted_df['Close']
            X = self.preprocessor.create_dataset(X, time_steps, y, look_ahead, for_training=False)

            return X, y
        else:
            X = self.preprocessor.create_dataset(X, time_steps, for_training)
            return X

    def predict(self, time_steps, for_training=False):
        X = self.prepare_data(time_steps, for_training)
        predictions = self.model.predict(X, run_eagerly=True)
        return predictions

    def rescale_prediction(self, prediction):
        prediction = prediction.reshape(-1, 1)  # ensure it's a 2D array
        rescaled_prediction = self.preprocessor.close_scaler.inverse_transform(prediction)
        return rescaled_prediction
    


class LSTMHyperModel(HyperModel):
    def __init__(self, input_shape):
        self.input_shape = input_shape

    def build(self, hp):
        model = Sequential()
        model.add(LSTM(units=hp.Int('units_1', min_value=32, max_value=512, step=32), return_sequences=True, 
                       input_shape=self.input_shape))
        model.add(Dropout(rate=hp.Float('dropout_1', min_value=0.0, max_value=0.5, step=0.05)))
        model.add(LSTM(units=hp.Int('units_2', min_value=32, max_value=512, step=32), return_sequences=True))
        model.add(Dropout(rate=hp.Float('dropout_2', min_value=0.0, max_value=0.5, step=0.05)))
        model.add(LSTM(units=hp.Int('units_3', min_value=32, max_value=512, step=32), return_sequences=False))
        model.add(Dropout(rate=hp.Float('dropout_3', min_value=0.0, max_value=0.5, step=0.05)))
        model.add(Dense(units=hp.Int('dense_units', min_value=16, max_value=128, step=16), activation='relu'))
        model.add(Dense(units=1))
        model.compile(optimizer='adam', loss='mean_squared_error', run_eagerly=True)
        return model

def main():
    pass

if __name__ == "__main__":
    main()