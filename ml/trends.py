"""
R&D
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
from fbprophet import Prophet
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

df = pd.DataFrame(dfraw['date'])
df = df.rename({'date': 'ds'}, axis=1)
df['y'] = dfraw['Adjusted close']

last = df['y'].tail(1).values[0]

m = Prophet(weekly_seasonality=True, changepoint_prior_scale=0.05)
m.fit(df)

future = m.make_future_dataframe(periods=90)

# print(m.changepoints.tail(5))

forecast = m.predict(future)

stats = forecast['yhat'].tail(90).describe()

max = stats['max']
profit = round(100 * (max - last) / last, 2)

print(sybmol, last, profit)

fig1 = m.plot(forecast)
plt.show()

fig2 = m.plot_components(forecast)
plt.show()
