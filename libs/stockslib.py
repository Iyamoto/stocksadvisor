"""
Stocks related stuff
"""

import time
import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
# from fbprophet import Prophet
import talib
import pandas_datareader as pdr
import logging
from datetime import datetime, timedelta
from pprint import pprint
logging.getLogger('fbprophet').setLevel(logging.WARNING)


class RESOURCE(object):
    """Single resource"""

    def __init__(self, symbol='', price_header='Adjusted close'):
        self.symbol = symbol
        self.prices = dict()
        self.history = dict()
        self.df = None

        self.price_header = price_header

        self.msg = list()
        self.buy = 0
        self.sell = 0
        self.turn_weight = 2

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

    def fetch_alpha(self, key='demo', size='compact', timeout=5):
        ts = TimeSeries(key=key, output_format='pandas')
        retry = 0
        while True:
            try:
                data, meta_data = ts.get_daily_adjusted(symbol=self.symbol, outputsize=size)
                break
            except:
                retry += 1
                if retry > 10:
                    exit('Can not fetch ' + self.symbol)
                time.sleep(timeout)
                continue
        return data

    def get_history_from_alpha(self, key='demo', cachedir='history', cacheage=3600*24*365*10):
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

        data = self.fetch_alpha(key=key, size='full')
        data.to_csv(filepath)

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

        data = self.fetch_alpha(key=key, size='compact')
        data.to_csv(filepath)

        self.prices = data
        return data

    def fetch_moex(self, days=100, timeout=1):

        date_N_days_ago =datetime.now() - timedelta(days=days)
        start = date_N_days_ago.strftime('%m/%d/%Y')

        df = pdr.get_data_moex(self.symbol, pause=timeout, start=start)
        df = df.reset_index()
        df = df.query('BOARDID == "TQBR"')

        filtered = pd.DataFrame()
        filtered['date'] = df['TRADEDATE']
        filtered['Open'] = df['OPEN']
        filtered['Low'] = df['LOW']
        filtered['High'] = df['HIGH']
        filtered['Close'] = df['CLOSE']
        filtered['Volume'] = df['VOLUME']

        return filtered

    def get_prices_from_moex(self, cachedir='cache-m', cacheage=3600*24*8, timeout=3, days=100):
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
                self.prices = data.tail(days)
                self.history = data
                return data

        data = self.fetch_moex(days=days, timeout=timeout)
        filepath = os.path.join(cachedir, filename)
        data.to_csv(filepath)

        time.sleep(timeout)

        return data

    def get_prophet_prediction(self, periods=30):

        dfraw = self.prices
        dfraw = dfraw.reset_index()

        df = pd.DataFrame(dfraw['date'])
        df = df.rename({'date': 'ds'}, axis=1)
        df['y'] = dfraw[self.price_header]

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

    def get_ema_last(self, period=20, name=''):
        if not name:
            name = self.price_header
        pricedata = self.prices
        p = pricedata[name].values
        p = p.astype(float)
        output = talib.EMA(p, timeperiod=period)
        return output[-1]

    def get_sma_last(self, period=20, name=''):
        if not name:
            name = self.price_header
        pricedata = self.prices
        output = talib.SMA(pricedata[name].values, timeperiod=period)
        return output[-1]

    def max_close_to_may(self, indicator='EMA', x=50, y=100):
        indicator = indicator.lower()
        method = getattr(self, 'get_{}_last'.format(indicator))
        max = method(period=x)
        may = method(period=y)
        price = self.get_last_price()
        rez = 0

        if (max > may) and abs(max - may) < price * 0.01:
            self.msg.append('BUY: {}{} {} close to {}{} {}'.
                            format(indicator, x, max, indicator, y, may))
            rez = 1

        return rez

    def ema50_close_to_ema100(self):
        return self.max_close_to_may(indicator='EMA', x=50, y=100)

    def ema50_close_to_ema200(self):
        return self.max_close_to_may(indicator='EMA', x=50, y=200)

    def ema20_close_to_ema50(self):
        return self.max_close_to_may(indicator='EMA', x=20, y=50)

    def get_last_price(self):
        prices = self.prices[self.price_header].tail(1)
        return prices.to_frame().iloc[0, 0]

    def price_above_ma(self, indicator='SMA', period=100):
        indicator = indicator.lower()
        method = getattr(self, 'get_{}_last'.format(indicator))
        ma = method(period=period)
        price = self.get_last_price()
        rez = 0
        if float(price) > ma:
            self.msg.append('BUY: Price {} above {}{} {}'.format(price, indicator, period, ma))
            rez = 1

        return rez

    def price_above_sma100(self):
        return self.price_above_ma(indicator='SMA', period=100)

    def price_above_sma200(self):
        return self.price_above_ma(indicator='SMA', period=200)

    def price_above_ema200(self):
        return self.price_above_ma(indicator='EMA', period=200)

    def price_above_ema100(self):
        return self.price_above_ma(indicator='EMA', period=100)

    def price_above_ema50(self):
        return self.price_above_ma(indicator='EMA', period=50)

    def get_rsi_last(self, period=5, name=''):
        if not name:
            name = self.price_header
        pricedata = self.prices
        p = pricedata[name].values
        p = p.astype(float)
        output = talib.RSI(p, timeperiod=period)
        return output[-1]

    def rsi_bellow_x(self, period=5, x=40):
        rsi = self.get_rsi_last(period=period)
        rez = 0

        if rsi < x:
            # print('RSI BUY', self.symbol, rsi, x)
            self.msg.append('BUY: RSI{} bellow {}'.format(period, x))
            rez = self.turn_weight

        return rez

    def rsi5_bellow_40(self):
        return self.rsi_bellow_x(period=5, x=40)

    def rsi14_bellow_40(self):
        return self.rsi_bellow_x(period=14, x=40)

    def rsi14_bellow_30(self):
        return self.rsi_bellow_x(period=14, x=33)

    def rsi_above_x(self, period=5, x=70):
        rsi = self.get_rsi_last(period=period)
        rez = 0

        if rsi > x:
            # print('RSI SELL', self.symbol, rsi, x)
            self.msg.append('SELL: RSI{} above {}'.format(period, x))
            rez = -2

        return rez

    def rsi14_above_70(self):
        return self.rsi_above_x(period=14, x=70)

    def price_bellow_kc(self):
        rez = 0
        low = self.prices['Low'].values
        low = low.astype(float)
        high = self.prices['High'].values
        high = high.astype(float)
        close = self.prices[self.price_header].values
        close = close.astype(float)
        output = talib.ATR(high, low, close, timeperiod=10)
        atr = output[-1]
        output = talib.EMA(close, timeperiod=20)
        ema = output[-1]
        output = talib.EMA(close, timeperiod=50)
        ema50 = output[-1]
        price = self.get_last_price()
        kc = ema - 1.4 * atr
        if price < kc and ema > ema50:
            rez = self.turn_weight
            print('KC buy', self.symbol, price, ema, atr, kc)
            self.msg.append('BUY: Price {} bellow Keltner channel {}'.format(price, kc))

        return rez

    def price_above_kc(self):
        rez = 0
        low = self.prices['Low'].values
        low = low.astype(float)
        high = self.prices['High'].values
        high = high.astype(float)
        close = self.prices[self.price_header].values
        close = close.astype(float)
        output = talib.ATR(high, low, close, timeperiod=10)
        atr = output[-1]
        output = talib.EMA(close, timeperiod=20)
        ema = output[-1]
        price = self.get_last_price()
        kc = ema + 1.4 * atr

        if price > kc:
            rez = -2
            # print('KC Sell', self.symbol, price, ema, atr, kc)
            self.msg.append('SELL: Price {} above Keltner channel {}'.format(price, kc))

        return rez

    def macd_hist_close_zero(self):
        rez = 0
        close = self.prices[self.price_header].values
        close = close.astype(float)
        macd, macdsign, macdhist = talib.MACD(close)
        macd = macd[-1]
        macdsign = macdsign[-1]
        macdhist = macdhist[-1]
        price = self.get_last_price()
        if abs(macdhist) <= 0.075 * price:
            rez = 1
            # print('MACD Buy', self.symbol, price, macd)
            self.msg.append('BUY: MACD_Hist {} is close to zero'.format(macdhist))

        return rez

    def macd_uptrend(self):
        rez = 0
        close = self.prices[self.price_header].values
        close = close.astype(float)
        macd, macdsign, macdhist = talib.MACD(close)
        output = talib.EMA(macd, timeperiod=20)
        ema20 = output[-1]

        output = talib.EMA(macd, timeperiod=5)
        ema5 = output[-1]

        macd = macd[-1]
        macdsign = macdsign[-1]

        if (macd > macdsign) and (ema5 > ema20):
            rez = 1
            self.msg.append('BUY: MACD is in up trend')

        return rez

    def is_anomaly(self):
        rez = False
        low = self.prices['Low'].values
        low = low.astype(float)
        high = self.prices['High'].values
        high = high.astype(float)
        close = self.prices[self.price_header].values
        close = close.astype(float)
        output = talib.ATR(high, low, close, timeperiod=10)
        atr = output[-1]
        output = talib.EMA(close, timeperiod=20)
        ema = output[-1]
        price = self.get_last_price()

        if price < (ema - 2 * atr):
            rez = True
            print('Anomaly detected', self.symbol, price, (ema - 2 * atr))
            self.msg.append('Anomaly: Price {} bellow 2*ATR'.format(price))

        return rez
