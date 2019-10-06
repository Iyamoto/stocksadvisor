"""
Research FXIT

"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd
import configs.alphaconf
import configs.fxit
import libs.assets
import numpy as np
from fbprophet import Prophet
from fbprophet.diagnostics import cross_validation
import matplotlib.pyplot as plt


if __name__ == "__main__":

    asset = libs.assets.ASSET(symbol='MSFT', source='alpha', asset_type='stock', key=configs.alphaconf.key)

    asset.get_data()

    df_size = len(asset.df)
    train_size = round(df_size * 95 / 100)
    test_size = round(df_size * 5 / 100)

    df_train = asset.df[:train_size]
    df_test = asset.df[-test_size:]

    train = pd.DataFrame()

    # Convert to Prophet required form
    train[['ds', 'y']] = df_train[['date', 'Close']]

    # Init & fit model
    model = Prophet(yearly_seasonality=False, daily_seasonality=False, weekly_seasonality=False,
                    interval_width=0.95)
    model.fit(train)

    forecast_frame = model.make_future_dataframe(periods=test_size)

    forecast = model.predict(forecast_frame)
    print(forecast.tail(test_size))
    print(df_test[['date', 'Close']])

    # validation = cross_validation(model, horizon='5 days')
    #
    # # last 5 entries
    # print(validation.tail())
    #
    # mean_error = np.mean(np.abs((validation['y'] - validation['yhat']) / validation['y'])) * 100
    # print(mean_error)

    model.plot(forecast)
    # model.plot_components(forecast)
    plt.show()
