"""
Stocks related stuff
"""

import time
import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
import libs.technical_indicators
from pprint import pprint
from fbprophet import Prophet
import talib
import logging
logging.getLogger('fbprophet').setLevel(logging.WARNING)


class RESOURCE(object):
    """Single resource"""

    def __init__(self, symbol='', price_type='close'):
        self.symbol = symbol
        self.price_type = price_type
        self.prices = dict()
        self.history = dict()
        self.df = None

        self.price_header = 'Close'

        self.msg = list()
        self.buy = 0
        self.sell = 0

    def fix_alpha_columns(self):
        df = self.prices
        df = df.rename(index=str, columns={'3. low': 'Low'})
        df = df.rename(index=str, columns={'2. high': 'High'})
        df = df.rename(index=str, columns={'1. open': 'Open'})
        df = df.rename(index=str, columns={'4. close': 'Close'})
        df = df.rename(index=str, columns={'6. volume': 'Volume'})
        df = df.rename(index=str, columns={'5. adjusted close': 'Adjusted close'})

        self.prices = df
        self.df = df.reset_index()

    def fix_alpha_history_columns(self):
        df = self.history
        df = df.rename(index=str, columns={'3. low': 'Low'})
        df = df.rename(index=str, columns={'2. high': 'High'})
        df = df.rename(index=str, columns={'1. open': 'Open'})
        df = df.rename(index=str, columns={'4. close': 'Close'})
        df = df.rename(index=str, columns={'6. volume': 'Volume'})
        df = df.rename(index=str, columns={'5. adjusted close': 'Adjusted close'})
        self.history = df
        self.prices = self.history.tail(200)

    def get_history_from_alpha(self, key='', cachedir='history', cacheage=3600*24*365*10):
        if not os.path.isdir(cachedir):
            os.mkdir(cachedir)
        filename = self.symbol + '.csv'
        filepath = os.path.join(cachedir, filename)
        if os.path.isfile(filepath):
            age = time.time() - os.path.getmtime(filepath)
            if age > cacheage:
                os.remove(filepath)
            else:
                data = pd.read_csv(filepath, index_col='date')
                self.history = data
                return data

        ts = TimeSeries(key=key, output_format='pandas')
        data, meta_data = ts.get_daily_adjusted(symbol=self.symbol, outputsize='full')
        data.to_csv(filepath)
        time.sleep(10)

        self.history = data
        return data

    def get_prices_from_alpha(self, key='', cachedir='cache', cacheage=3600*8):
        if not os.path.isdir(cachedir):
            os.mkdir(cachedir)
        filename = self.symbol + '.csv'
        filepath = os.path.join(cachedir, filename)
        if os.path.isfile(filepath):
            age = time.time() - os.path.getmtime(filepath)
            if age > cacheage:
                os.remove(filepath)
            else:
                data = pd.read_csv(filepath, index_col='date')
                self.prices = data
                return data

        ts = TimeSeries(key=key, output_format='pandas')
        data, meta_data = ts.get_daily_adjusted(symbol=self.symbol, outputsize='compact')
        data.to_csv(filepath)
        time.sleep(10)

        self.prices = data
        return data

    def get_prophet_prediction(self, periods=30):

        dfraw = self.prices
        dfraw = dfraw.reset_index()

        df = pd.DataFrame(dfraw['date'])
        df = df.rename({'date': 'ds'}, axis=1)
        df['y'] = dfraw['Adjusted close']

        last = df['y'].tail(1).values[0]

        m = Prophet()
        m.fit(df)

        future = m.make_future_dataframe(periods=periods)

        forecast = m.predict(future)

        stats = forecast['yhat'].tail(periods).describe()

        max = stats['max']
        profit = round(100 * (max - last) / last, 2)

        self.msg.append('Profit: ' + str(profit))

        return profit

    def get_last_price(self):
        prices = self.prices[self.price_header].tail(1)
        return prices.to_frame().iloc[0, 0]

    def get_ema_last(self, period=20, name='Adjusted close'):
        pricedata = self.prices
        output = talib.EMA(pricedata[name].values, timeperiod=period)
        return output[-1]

    def get_sma_last(self, period=20, name='Adjusted close'):
        pricedata = self.prices
        output = talib.SMA(pricedata[name].values, timeperiod=period)
        return output[-1]

    def ema50_close_to_ema100(self):
        ema100 = self.get_ema_last(period=100)
        ema50 = self.get_ema_last(period=50)
        price = self.get_last_price()
        rez = 0

        if (ema50 > ema100) and abs(ema100 - ema50) < price * 0.01:
            self.msg.append('BUY: EMA50 {} close to EMA100 {}'.format(ema50, ema100))
            rez = 1

        return rez

    def price_above_sma100(self):
        sma200 = self.get_sma_last(period=100)
        price = self.get_last_price()
        rez = 0

        if price > sma200:
            self.msg.append('BUY: Price {} above SMA100 {}'.format(price, sma200))
            rez = 1

        return rez

    def ema50_close_to_ema200(self):
        ema200 = self.get_ema_last(period=200)
        ema50 = self.get_ema_last(period=50)
        price = self.get_last_price()
        rez = 0

        if (ema50 > ema200) and abs(ema200 - ema50) < price * 0.01:
            self.msg.append('BUY: EMA50 {} close to EMA200 {}'.format(ema50, ema200))
            rez = 1

        return rez

    def price_above_sma200(self):
        ma = self.get_sma_last(period=200)
        price = self.get_last_price()
        rez = 0

        if price > ma:
            self.msg.append('BUY: Price {} above SMA200 {}'.format(price, ma))
            rez = 1

        return rez

    def price_above_ema200(self):
        ma = self.get_ema_last(period=200)
        price = self.get_last_price()
        rez = 0

        if price > ma:
            self.msg.append('BUY: Price {} above EMA200 {}'.format(price, ma))
            rez = 1

        return rez

    def price_above_ema100(self):
        ma = self.get_ema_last(period=100)
        price = self.get_last_price()
        rez = 0
        if price > ma:
            self.msg.append('BUY: Price {} above EMA100 {}'.format(price, ma))
            rez = 1

        return rez

