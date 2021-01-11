"""Main assets class"""

import time
import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd
import pandas_datareader as pdr
from datetime import datetime, timedelta
from pprint import pprint
import matplotlib.pyplot as plt
import talib
import pandas_montecarlo
from alpha_vantage.timeseries import TimeSeries
import collections
import json
from scipy.signal import argrelextrema
import numpy as np
import requests
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()


class ASSET(object):
    """Single asset"""

    def __init__(self, symbol='', source='moex', asset_type='stock', key='demo', min_goal=0.1,
                 volumefield='VOLUME', atr_multiplier=2, cacheage=3600*12, cachebase='',
                 kc_channel=2, caching=True):
        """
        source: moex, alpha
        type: stock, futures
        """
        self.symbol = symbol
        self.asset_type = asset_type
        self.source = source
        self.volumefield = volumefield
        self.cacheage = cacheage
        self.caching = caching
        self.key = key
        self.cachebase = cachebase
        self.min_goal = min_goal
        self.atr_multiplier = atr_multiplier
        self.kc_channel = kc_channel
        # http://ftp.moex.com/pub/ClientsAPI/ASTS/docs/ASTS_Markets_and_Boards.pdf
        if self.asset_type == 'stock':
            self.boardid = 'TQBR'
        if self.asset_type == 'futures':
            self.boardid = 'RFUD'
        if self.asset_type == 'currency':
            self.boardid = 'CETS'
            self.volumefield = 'VOLRUR'
        if self.asset_type == 'etf':
            self.boardid = 'TQTF'
        if self.asset_type == 'etfusd':
            self.boardid = 'TQTD'

        self.df = None
        self.trend = ''
        self.anomalies = 0
        self.lastprice = 0
        self.stoploss = 0
        self.stoplosspercent = 0  # AKA Bust
        self.bust_chance = 0
        self.goalprice = 0
        self.lastrsi = 0
        self.goal_chance = 0
        self.rewardriskratio = 0
        self.anomaly_filter_up = None
        self.anomaly_filter_down = None
        self.trendline = None
        self.blackswan_chance = 0.005
        self.volume_limit = 0
        self.dividend_level = dict()
        self.dividend_level['alpha'] = 2.5  # Acceptable dividend lvl for USD
        self.dividend_level['moex'] = 4  # Acceptable dividend lvl for RUB
        self.fairprice = 0
        self.breakout_level = 0
        self.phase1_start = 0
        self.phase1_end = 0
        self.phase1_len = 0
        self.lastema13 = 0
        self.lastema50 = 0
        self.lastema100 = 0
        self.is_under_accumulation = False

    def __str__(self):
        result = self.get_results()
        out = json.dumps(result, indent=4)
        return out

    @staticmethod
    def get_trendline(data, order=1):
        coeffs = np.polyfit(data.index.values, list(data), order)
        return coeffs

    def get_fair_price(self, dividend=0):
        self.fairprice = round(100 * dividend/self.dividend_level[self.source], 2)
        return self.fairprice

    def get_reward_risk_ratio(self):
        self.rewardriskratio = round(self.goal_chance * (self.goalprice - self.lastprice) /
                                     (self.bust_chance * (self.lastprice - self.stoploss)), 2)

        return self.rewardriskratio

    def compare_volumes(self, days=0):
        self.df['UpDay'] = self.df.Volume[self.df['Close'] >= self.df['Open']]
        updays_volume = self.df['UpDay'].tail(days).sum()
        self.df = self.df.drop(['UpDay'], axis=1)

        self.df['DownDay'] = self.df.Volume[self.df['Close'] < self.df['Open']]
        downdays_volume = self.df['DownDay'].tail(days).sum()
        self.df = self.df.drop(['DownDay'], axis=1)

        if updays_volume > downdays_volume:
            self.is_under_accumulation = True

    # def get_money_flow_index(self, days=0):
    #     self.df['UpDay'] = self.df.Volume[self.df['Close'] >= self.df['Open']]
    #     self.df['MoneyFlow'] = self.df.UpDay * (self.df.Close + self.df.High + self.df.Low) / 3
    #     up_money_flow = self.df['MoneyFlow'].tail(days).sum()
    #     self.df = self.df.drop(['UpDay'], axis=1)
    #     self.df = self.df.drop(['MoneyFlow'], axis=1)
    #
    #     self.df['DownDay'] = self.df.Volume[self.df['Close'] < self.df['Open']]
    #     self.df['MoneyFlow'] = self.df.DownDay * (self.df.Close + self.df.High + self.df.Low) / 3
    #     down_money_flow = self.df['MoneyFlow'].tail(days).sum()
    #     self.df = self.df.drop(['DownDay'], axis=1)
    #     self.df = self.df.drop(['MoneyFlow'], axis=1)
    #
    #     money_flow_ratio = up_money_flow / down_money_flow
    #     money_flow_index = round(100 - (100/(1 + money_flow_ratio)), 1)
    #     return money_flow_index

    def static_analysis(self, printoutput=True):
        # Calculate some stats
        self.get_lastprice()
        self.get_goalprice()
        self.get_atr(period=5)
        self.get_ema(period=5)
        self.get_ema(period=13)
        self.get_ema(period=20)
        self.get_rsi(period=14)
        self.get_mfi(period=14)
        self.get_lastrsi()
        self.get_kc()
        self.get_lastema50()
        self.get_lastema100()

        # Stop loss
        self.get_stoploss()

        # if stop_loss <= 0:
        #     self.get_results()
        #     print(self)
        #     raise ValueError('Negative stop-loss')  # Debug

        # Calculate trend
        self.detect_trend()

        # Count anomalies
        self.count_anomalies()

        if printoutput:
            print('Last price:', self.lastprice)
            print('Exit price:', self.goalprice)
            print('Bust:', self.stoplosspercent)
            print('Stop loss:', self.stoploss)
            print('Trend:', self.trend)
            print('Anomalies:', self.anomalies)

    def get_results(self):
        result = dict()
        result[self.symbol] = collections.OrderedDict()
        result[self.symbol]['last_price'] = self.lastprice
        result[self.symbol]['stop_loss'] = self.stoploss
        result[self.symbol]['exit_price'] = self.goalprice
        result[self.symbol]['fair_price'] = float(self.fairprice)
        result[self.symbol]['success_chance'] = round(self.goal_chance, 2)
        result[self.symbol]['bust'] = round(self.stoplosspercent, 2)
        result[self.symbol]['bust_chance'] = round(self.bust_chance, 2)
        result[self.symbol]['reward_risk_ratio'] = self.rewardriskratio
        result[self.symbol]['trend'] = self.trend
        result[self.symbol]['anomalies'] = float(self.anomalies)
        return result

    def get_goalprice(self):
        self.goalprice = round(self.lastprice * (1 + self.min_goal), 6)
        return self.goalprice

    def get_stoploss(self):
        """Returns stop loss and stop loss percent"""
        self.df['StopLoss'] = self.df['Close'] - self.atr_multiplier * self.df['ATR']
        self.df['StopLossPercent'] = 1 - self.df['StopLoss'] / self.df['Close']
        self.stoplosspercent = round(self.df['StopLossPercent'].max(), 2)
        self.stoploss = round(self.df.Close[-1:].values[0] * (1 - self.stoplosspercent), 6)

        return self.stoploss, self.stoplosspercent

    def get_lastprice(self):
        self.lastprice = float(round(self.df.Close[-1:].values[0], 2))
        return self.lastprice

    def get_lastema50(self):
        self.get_ema(period=50)
        self.lastema50 = float(round(self.df.EMA50[-1:].values[0], 6))
        self.df = self.df.drop(['EMA50'], axis=1)
        return self.lastema50

    def get_lastema100(self):
        self.get_ema(period=100)
        self.lastema100 = float(round(self.df.EMA100[-1:].values[0], 6))
        self.df = self.df.drop(['EMA100'], axis=1)
        return self.lastema100

    def get_lastema13(self):
        self.lastema13 = float(round(self.df.EMA13[-1:].values[0], 6))
        return self.lastema13

    def get_lastrsi(self):
        self.lastrsi = float(round(self.df.RSI[-1:].values[0], 2))
        return self.lastrsi

    def get_data(self):
        if self.source == 'moex':
            self.get_data_from_moex(cachedir=os.path.join(self.cachebase, 'cache-m'))
        if self.source == 'alpha':
            self.get_prices_from_alpha(key=self.key, cachedir=os.path.join(self.cachebase, 'cache'))
            self.fix_alpha_columns()
            self.df = self.df[::-1].reset_index(drop=True)
        self.df = self.df.fillna(method='ffill')
        self.df = self.df.fillna(method='bfill')

    def get_prices_from_alpha(self, key='', cachedir='cache'):
        if self.caching:
            if not os.path.isdir(cachedir):
                os.mkdir(cachedir)
            filename = self.symbol + '.csv'
            filepath = os.path.join(cachedir, filename)
            if os.path.isfile(filepath):
                age = time.time() - os.path.getmtime(filepath)
                if age > self.cacheage:
                    os.remove(filepath)
                else:
                    data = pd.read_csv(filepath, index_col='date')
                    self.df = data
                    return data

        data = self.fetch_alpha(key=key, size='compact')
        if self.caching:
            data.to_csv(filepath)

        self.df = data
        return data

    def get_ema200_alpha(self, key='demo'):
        url = 'https://www.alphavantage.co/query?function=' + \
            'EMA&symbol={}&interval=daily&time_period=200&series_type=close&apikey={}'.format(self.symbol, key)
        try:
            r = requests.get(url=url)
            data = r.json()
            last = data['Meta Data']['3: Last Refreshed']
            ema200 = float(data['Technical Analysis: EMA'][last]['EMA'])
        except:
            ema200 = None
        return ema200

    def fetch_alpha(self, key='demo', size='compact', timeout=5):
        ts = TimeSeries(key=key, output_format='pandas')
        retry = 0
        while True:
            try:
                if self.symbol == 'TCS':
                    symbol = 'LON:TCS'
                else:
                    symbol = self.symbol
                data, meta_data = ts.get_daily_adjusted(symbol=symbol, outputsize=size)
                break
            except:
                retry += 1
                if retry > 10:
                    exit('Can not fetch ' + self.symbol)
                time.sleep(timeout)
                continue
        return data

    def fix_alpha_columns(self):
        df = self.df
        df = df.rename(index=str, columns={'3. low': 'Low'})
        df = df.rename(index=str, columns={'2. high': 'High'})
        df = df.rename(index=str, columns={'1. open': 'Open'})
        df = df.rename(index=str, columns={'4. close': 'Close'})
        df = df.rename(index=str, columns={'6. volume': 'Volume'})
        df = df.rename(index=str, columns={'5. adjusted close': 'Adjusted close'})

        self.df = df
        self.df = df.reset_index()

    def fetch_moex(self, days=100, timeout=1):
        date_N_days_ago = datetime.now() - timedelta(days=days)
        start = date_N_days_ago.strftime('%m/%d/%Y')

        df = pdr.get_data_moex(self.symbol, pause=timeout, start=start)
        df = df.reset_index()
        df = df.query('BOARDID == @self.boardid')
        filtered = pd.DataFrame()
        filtered['date'] = df['TRADEDATE']
        filtered['Open'] = df['OPEN']
        filtered['Low'] = df['LOW']
        filtered['High'] = df['HIGH']
        filtered['Close'] = df['CLOSE']
        filtered['Volume'] = df[self.volumefield]
        if self.boardid =='RFUD':
            filtered['Openpositions'] = df['OPENPOSITION']
            filtered['Openpositionsvalue'] = df['OPENPOSITIONVALUE']

        return filtered

    def get_data_from_moex(self, cachedir='cache-m', timeout=3, days=100):
        if self.caching:
            if not os.path.isdir(cachedir):
                os.mkdir(cachedir)
            filename = self.symbol + '.csv'
            filepath = os.path.join(cachedir, filename)
            if os.path.isfile(filepath):
                age = time.time() - os.path.getmtime(filepath)
                if age > self.cacheage:
                    os.remove(filepath)
                else:
                    data = pd.read_csv(filepath)
                    self.df = data
                    return data

        data = self.fetch_moex(days=days, timeout=timeout)
        self.df = data
        if self.caching:
            filepath = os.path.join(cachedir, filename)
            data.to_csv(filepath, index=False)

        time.sleep(timeout)
        return data

    def plot(self, msg=''):
        columns = self.df.columns
        df = pd.concat([self.df['date'], self.df['Close'], self.df['Volume']], axis=1)
        df.date = pd.to_datetime(df['date'], format='%Y-%m-%d')
        df = df.set_index('date')
        df['Close'] = df.Close.replace(to_replace=0, method='ffill')
        df['Volume'] = df.Volume.replace(to_replace=0, method='ffill')
        fig = plt.figure(figsize=(15, 8))
        plt.subplot2grid((4, 1), (0, 0), rowspan=2)
        plt.title(msg + ' ' + self.symbol)

        plt.plot(df.index, df.Close, 'k', label='Price', linewidth=2.0)

        if 'EMA13' in columns:
            df['EMA13'] = self.df.EMA13.values
            plt.plot(df.index, df.EMA13, 'g', label='EMA13', linestyle='--')

        if 'KC_LOW' in columns:
            df['KC_LOW'] = self.df.KC_LOW.values

        if 'KC_HIGH' in columns:
            df['KC_HIGH'] = self.df.KC_HIGH.values

        if 'KC_LOW' in columns and 'KC_HIGH' in columns:
            plt.fill_between(df.index, df.KC_LOW, df.KC_HIGH, color='b', alpha=0.1)

        if 'Phase1' in columns:
            df['Phase1'] = self.df.Phase1.values
            plt.scatter(df.index, df['Phase1'], c='r')

        if 'Max' in columns:
            df['Max'] = self.df.Max.values
            plt.scatter(df.index, df['Max'], c='g')

            if self.breakout_level > 0:
                horiz_line_data = np.array([self.breakout_level for i in range(len(df.index))])
                plt.plot(df.index, horiz_line_data, color='b', label='Breakout', linestyle='-.', linewidth=1.0)

        # if self.trendline is not None:
        #     polynomial = np.poly1d(self.trendline)
        #     x = np.linspace(0, len(df.index)-1, num=len(df.index))
        #     y = polynomial(x)
        #     plt.plot(df.index, y, color='g', label='Trend', linestyle='-.', linewidth=1.0)

        plt.legend()
        plt.grid()

        ax1 = plt.subplot2grid((4, 1), (2, 0), rowspan=1)

        ax1.plot(df.index, df.Volume, 'g', label='Volume')
        ax1.set_ylabel('Volume', color='g')
        horiz_line_data = np.array([self.volume_limit for i in range(len(df.index))])
        ax1.plot(df.index, horiz_line_data, color='b', label='Volume limit', linestyle='-.', linewidth=1.0)

        ax1.grid()

        if 'MFI' in columns:
            df['MFI'] = self.df.MFI.values
            plt.subplot2grid((4, 1), (3, 0), rowspan=1)
            plt.plot(df.index, df.MFI, 'r', label='MFI')
            horiz_line_data = np.array([70 for i in range(len(df.index))])
            plt.plot(df.index, horiz_line_data, color='g', label='Oversold', linestyle='-.', linewidth=1.0)
            horiz_line_data = np.array([30 for i in range(len(df.index))])
            plt.plot(df.index, horiz_line_data, color='b', label='Overbought', linestyle='-.', linewidth=1.0)
            plt.legend()
            plt.grid()

        fig.tight_layout()
        plt.show()

    def get_mfi(self, period=14):
        pricedata = self.df
        high = pricedata['High'].values
        low = pricedata['Low'].values
        close = pricedata['Close'].values
        volume = pricedata['Volume'].values
        low = low.astype(float)
        high = high.astype(float)
        close = close.astype(float)
        volume = volume.astype(float)
        output = talib.MFI(high, low, close, volume, timeperiod=period)
        self.df['MFI'] = output
        return output

    def get_atr(self, period=5):
        pricedata = self.df
        high = pricedata['High'].values
        low = pricedata['Low'].values
        close = pricedata['Close'].values
        low = low.astype(float)
        high = high.astype(float)
        close = close.astype(float)
        output = talib.ATR(high, low, close, timeperiod=period)
        self.df['ATR'] = output
        return output

    def get_ema(self, period=5):
        pricedata = self.df
        close = pricedata['Close'].values
        close = close.astype(float)
        output = talib.EMA(close, timeperiod=period)
        self.df['EMA' + str(period)] = output
        return output

    def get_rsi(self, period=5):
        pricedata = self.df
        close = pricedata['Close'].values
        close = close.astype(float)
        output = talib.RSI(close, timeperiod=period)
        self.df['RSI'] = output
        return output

    def get_kc(self, period=5):
        self.df['KC_LOW'] = self.df['EMA' + str(period)] - self.kc_channel * self.df['ATR']
        self.df['KC_HIGH'] = self.df['EMA' + str(period)] + self.kc_channel * self.df['ATR']

    def get_bust_chance(self, sims=1000, bust=0.1, goal=0.1, plot=False, taillen=0):
        # Monte-Carlo
        df = self.df.tail(taillen).copy()
        df['Return'] = df['Close'].pct_change().fillna(0)

        # print('Real returns stats:')
        # pprint(self.df['Return'].describe())
        # print()

        mc = df['Return'].montecarlo(sims=sims, bust=-1 * bust, goal=goal)

        # pprint(mc.stats)
        self.bust_chance = mc.stats['bust']
        self.goal_chance = mc.stats['goal']

        # if self.goal_chance > 0.99:
        #     pprint(mc.stats)
        #     plot = True

        # print(mc.data)

        if plot:
            mc.plot(title=self.symbol, figsize=(15, 5))

        # Paranoid on
        self.bust_chance += self.blackswan_chance

        if self.goal_chance > 0.9:
            self.goal_chance = 0.9

        return self.bust_chance, self.goal_chance

    def count_anomalies(self):

        self.anomaly_filter_up = self.df.Close > (self.df.EMA5 + self.kc_channel * self.df.ATR)
        self.df['BreakoutUp'] = self.anomaly_filter_up
        self.anomaly_filter_down = self.df.Close < (self.df.EMA5 - self.kc_channel * self.df.ATR)
        self.df['BreakoutDown'] = self.anomaly_filter_down
        self.df = self.df.drop(['BreakoutDown'], axis=1)
        self.df = self.df.drop(['BreakoutUp'], axis=1)
        self.anomalies = self.anomaly_filter_up.sum() + self.anomaly_filter_down.sum()

        return self.anomalies

    def detect_trend(self):
        # EMA5 > EMA20 means up trend?
        self.df['DownTrend'] = self.df.EMA5.fillna(0) <= self.df.EMA20.fillna(0)
        self.df['UpTrend'] = self.df.EMA5.fillna(0) >= self.df.EMA20.fillna(0)

        if self.df['UpTrend'].sum() >= 0.85 * len(self.df['UpTrend']):
            ema_trend = 'Up'
        elif self.df['DownTrend'].sum() >= 0.85 * len(self.df['DownTrend']):
            ema_trend = 'Down'
        else:
            ema_trend = 'Sideways'

        # Fit poly
        def trendline(data, order=1):
            coeffs = np.polyfit(data.index.values, list(data), order)
            return coeffs

        self.trendline = trendline(self.df['Close'])
        angle = self.trendline[0]
        if angle > 0:
            fit_trend = 'Up'
        if angle < 0:
            fit_trend = 'Down'
        if angle == 0:
            fit_trend = 'Sideways'

        self.trend = ema_trend + ' ' + fit_trend
        return self.trend

    def find_event(self, points=5, diff=2.0):
        std = round(self.df['Volume'].std(), 1)
        mean = round(self.df['Volume'].mean(), 1)
        event_filter = self.df.Volume > mean + diff * std
        self.df['Event'] = event_filter

        self.df['tmp'] = self.df.iloc[argrelextrema(self.df.Close.values, np.greater_equal, order=points)[0]]['Close']
        self.df['Max'] = self.df.tmp[self.df.Event]
        self.df = self.df.drop(['Event'], axis=1)
        self.df = self.df.drop(['tmp'], axis=1)
        if self.df.Max.sum() > 0:
            self.breakout_level = self.df.Max[self.df.Max > 0].tail(1).values[0]

        return self.df

    def find_phase1(self, rsi=60, diff=1, points=3):
        """
        Volume + price
        or RSI > 60?
        """
        self.volume_limit = self.df.Volume.mean() + diff * self.df.Volume.std()
        self.df['Phase1_Price'] = self.df.RSI[self.df.RSI > rsi]
        self.df['Phase1_Volume'] = self.df.Volume[self.df.Volume >= self.volume_limit]
        self.df['Phase1'] = self.df.Close[self.df.UpTrend & self.df['Phase1_Price'] & self.df['Phase1_Volume']]
        self.df = self.df.drop(['Phase1_Price'], axis=1)
        self.df = self.df.drop(['Phase1_Volume'], axis=1)

        self.df['PCT'] = self.df['EMA13'].pct_change().fillna(0)
        self.df['PCT10'] = self.df['PCT'] > 0.001

        if self.df.Phase1.sum() > 0:
            self.phase1_start = self.df.Phase1[self.df.Phase1 > 0][-1:].index.values[0]
            self.phase1_len = len(self.df) - self.phase1_start
            tmp = self.df.tail(self.phase1_len)
            if tmp.PCT10[tmp['PCT10'] == False].count() > 0:
                self.phase1_end = tmp.PCT10[tmp['PCT10'] == False][:1].index.values[0]
                self.df = self.df.drop(['PCT'], axis=1)
                self.df = self.df.drop(['PCT10'], axis=1)
                self.phase1_len = self.phase1_end - self.phase1_start
                for i in range(self.phase1_start, self.phase1_end):
                    self.df.loc[i, 'Phase1'] = self.df.loc[self.phase1_start, 'Phase1']

                self.df['tmp'] = self.df.iloc[argrelextrema(self.df.Close.values, np.greater_equal, order=points)[0]]['Close']
                self.df['Max'] = self.df.tmp[self.df['Phase1'] == self.df.loc[self.phase1_start, 'Phase1']]
                self.df = self.df.drop(['tmp'], axis=1)

                if self.df.Max.sum() > 0:
                    self.breakout_level = self.df.Max[self.df.Max > 0].tail(1).values[0]

        return self.df
