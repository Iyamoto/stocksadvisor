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


class RESOURCE(object):
    """Single resource"""

    def __init__(self, symbol='', price_type='close'):
        self.symbol = symbol
        self.price_type = price_type
        self.prices = dict()
        self.history = dict()

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
        self.prices = df

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

    def get_last_price(self):
        prices = self.prices[self.price_header].tail(1)
        return prices.to_frame().iloc[0, 0]

    def get_sma(self, period=20, points=1):
        pricedata = self.prices[self.price_header]
        sma = pricedata.rolling(window=period).mean()
        return sma.tail(points)

    def get_sma_last(self, period=20):
        sma = self.get_sma(period=period, points=1)
        sma = sma.to_frame().iloc[0, 0]
        return sma

    def check_price_close_sma(self, period=20):
        rez = 0
        buy_treshold = 2

        sma = self.get_sma_last(period=period)
        price = self.get_last_price()

        if price > sma and abs(price / sma - 1) * 100 < buy_treshold:
            self.msg.append('BUY: Price is close to SMA_' + str(period))
            rez = 1
            self.buy += rez

        self.buy += rez
        return rez

    def check_price_above_sma(self, period=20):
        rez = 0

        sma = self.get_sma_last(period=period)
        price = self.get_last_price()

        if price > sma:
            self.msg.append('BUY: Price is above SMA_' + str(period))
            rez = 1

        self.buy += rez
        return rez

    def check_sma20_above_sma100(self):
        sma20 = self.get_sma_last(period=20)
        sma100 = self.get_sma_last(period=100)

        if sma20 > sma100:
            self.msg.append('BUY: SMA20 above SMA100 (midterm bullish)')
            rez = 1
        else:
            self.msg.append('Warning: SMA20 bellow SMA100')
            rez = -1

        self.buy += rez
        return rez

    def get_ema_last(self, period=20):
        pricedata = self.prices
        ema = libs.technical_indicators.exponential_moving_average(pricedata.reset_index(), period)
        ema = ema.to_frame()
        ema = ema.tail(1).iloc[0, 0]
        return ema

    def check_price_above_ema(self, period=50):
        rez = 0

        ema = self.get_ema_last(period=period)
        price = self.get_last_price()

        if price > ema:
            self.msg.append('BUY: Price is above EMA_' + str(period))
            rez = 1

        self.buy += rez
        return rez

    def check_ema5_above_ema20(self):
        ema5 = self.get_ema_last(period=5)
        ema20 = self.get_ema_last(period=20)

        if ema5 > ema20:
            self.msg.append('BUY: EMA5 above EMA20 (shortterm bullish)')
            rez = 1
        else:
            self.msg.append('Warning: EMA5 bellow EMA20')
            rez = -1

        self.buy += rez
        return rez

    def check_ema20_above_ema50(self):
        ema20 = self.get_ema_last(period=20)
        ema50 = self.get_ema_last(period=50)

        if ema20 > ema50:
            self.msg.append('BUY: EMA20 above EMA50 (midterm bullish)')
            rez = 1
        else:
            self.msg.append('Warning: EMA20 bellow EMA50')
            rez = -1

        self.buy += rez
        return rez

    def get_last_rsi(self, period=5):
        """https://stackoverflow.com/questions/20526414/relative-strength-index-in-python-pandas"""
        data = self.prices[self.price_header]

        delta = data.diff().dropna()

        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0

        roll_up = up.rolling(window=period).mean()
        roll_down = down.abs().rolling(window=period).mean()

        rs = roll_up / roll_down
        rsi = 100.0 - (100.0 / (1.0 + rs))

        return rsi.tail(1).to_frame().iloc[0, 0]

    def get_rsi2(self, period=5, points=5):
        """https://stackoverflow.com/questions/20526414/relative-strength-index-in-python-pandas"""
        pricedata = self.prices
        rsi2 = libs.technical_indicators.relative_strength_index(pricedata.reset_index(), period)

        return rsi2.tail(points).to_dict()

    def check_rsi_buy(self, period=5):
        rsi = self.get_last_rsi(period=period)
        rez = 0
        buy_treshold = 35
        sell_treshold = 50
        oversell_treshold = 70

        if rsi < buy_treshold:
            self.msg.append('BUY: RSI_' + str(period))
            rez += 2

        if rsi > sell_treshold:
            self.msg.append('Warning: RSI_' + str(period))
            rez -= 1

        if rsi > oversell_treshold:
            self.msg.append('Warning: RSI_' + str(period))
            rez -= 1

        self.buy += rez
        return rez

    def check_rsi_sell(self, period=5):
        rsidata = self.get_last_rsi(period=period)
        rez = 0
        sell_treshold = 65
        buy_treshold = 50
        for rsi in rsidata:
            if rsidata[rsi] > sell_treshold:
                self.msg.append('SELL: RSI_' + str(period))
                rez += 4

            if rsidata[rsi] < buy_treshold:
                self.msg.append('Warning: RSI_' + str(period))
                rez -= 2

        self.buy += rez
        return rez

    def get_last_macd(self):
        pricedata = self.prices
        data = libs.technical_indicators.macd(pricedata.reset_index())
        data = data.set_index('date')
        data = data.tail(1)[['MACD', 'MACD_Sign', 'MACD_Hist']]

        macddata = {
            'macd': data.tail(1)[['MACD', 'MACD_Sign', 'MACD_Hist']].iloc[0, 0],
            'macd_signal': data.tail(1)[['MACD', 'MACD_Sign', 'MACD_Hist']].iloc[0, 1],
            'macd_diff': data.tail(1)[['MACD', 'MACD_Sign', 'MACD_Hist']].iloc[0, 2]
        }
        return macddata

    def check_macd(self):
        """
        https://mindspace.ru/abcinvest/shozhdenie-rashozhdenie-skolzyashhih-srednih-moving-average-convergence-divergence-macd/
        https://mindspace.ru/abcinvest/aleksandr-elder-o-rashozhdeniyah-tseny-i-macd/
        https://mindspace.ru/30305-kak-ispolzovat-divergentsii-macd-dlya-vyyavleniya-razvorota-na-rynke/
        """
        data = libs.technical_indicators.macd(self.prices.reset_index())
        data = data.set_index('date')
        macddata = data.tail(5).to_dict()

        last = None
        rez = 0
        grows = 0

        for macd_date in macddata['MACD_Hist']:
            macd_hist_value = macddata['MACD_Hist'][macd_date]
            if not last:
                last = macd_hist_value
                continue

            if last < 0 < macd_hist_value:
                self.msg.append('BUY: MACD crossed signal line from DOWN')
                rez += 4

            if last > 0 > macd_hist_value:
                self.msg.append('Warning: MACD crossed signal line from UP')
                rez -= 4

            if macd_hist_value > 0 and macddata['MACD'][macd_date] > 0:
                self.msg.append('Short grows: MACD and Hist are positive')
                grows = 1
            else:
                self.msg.append('Warning: MACD and Hist are negative')
                grows = -2

            last = macd_hist_value

        self.buy += rez + grows
        return rez + grows
