"""
R&D
https://www.kaggle.com/andreipopovici/forecasting-stocks/notebook
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
# import tensorflow as tf
import configs.alphaconf
import libs.stockslib as sl
import libs.technical_indicators as ti
from pprint import pprint
import pandas as pd
import numpy as np
from fbprophet import Prophet
from fbprophet.diagnostics import cross_validation
import matplotlib.pyplot as plt

sybmol = 'ABBV'

res = sl.RESOURCE(symbol=sybmol)
res.get_prices_from_alpha(key=configs.alphaconf.key, cacheage=3600*24*1, cachedir='..\cache')
res.get_history_from_alpha(key=configs.alphaconf.key, cacheage=3600*24, cachedir='..\history')
res.fix_alpha_columns()
res.fix_alpha_history_columns()

# Prepare data for the Prophet

dfraw = res.history
dfraw = dfraw.reset_index()

# split into train/test 90/10
df_size = len(dfraw)
train_size = round(df_size*95/100)
test_size = round(df_size*5/100)

df_train = dfraw[:train_size]
df_test = dfraw[-test_size:]

# init Prophet dataframe
train = pd.DataFrame()
# convert to Prophet required form
train[['ds', 'y']] = df_train[['date', 'Adjusted close']]

# Init & fit model
model = Prophet()
model.fit(train)

forecast_frame = model.make_future_dataframe(periods=test_size)

forecast = model.predict(forecast_frame)
pprint(forecast.tail())

validation = cross_validation(model, horizon='30 days', period='30 days', initial='1800 days')
# last 5 entries
pprint(validation.tail())

mean_error = np.mean(np.abs((validation['y'] - validation['yhat']) / validation['y'])) * 100
print(mean_error)

model.plot(forecast)
plt.show()
