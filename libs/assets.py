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
import numpy as np
import requests


class ASSET(object):
    """Single asset"""

    def __init__(self, symbol='', source='moex', asset_type='stock', key='demo', min_goal=0.1,
                 volumefield='VOLUME', atr_multiplier=5, cacheage=3600*12, cachebase='',
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

        if self.asset_type == 'stock':
            self.boardid = 'TQBR'
        if self.asset_type == 'futures':
            self.boardid = 'RFUD'
        if self.asset_type == 'currency':
            self.boardid = 'CETS'
            self.volumefield = 'VOLRUR'
        if self.asset_type == 'etf':
            self.boardid = 'TQTF'

        self.df = None
        self.trend = ''
        self.anomalies = 0
        self.lastprice = 0
        self.stoploss = 0
        self.stoplosspercent = 0  # AKA Bust
        self.bust_chance = 0
        self.goalprice = 0
        self.goal_chance = 0
        self.rewardriskratio = 0
        self.anomaly_filter_up = None
        self.anomaly_filter_down = None
        self.trendline = None
        self.blackswan_chance = 0.005
        self.dividend_level = dict()
        self.dividend_level['alpha'] = 1.8  # Acceptable dividend lvl for USD
        self.dividend_level['moex'] = 4  # Acceptable dividend lvl for RUB
        self.fairprice = 0

    def __str__(self):
        result = self.get_results()
        out = json.dumps(result, indent=4)
        return out

    def get_fair_price(self, dividend=0):
        self.fairprice = round(100 * dividend/self.dividend_level[self.source], 2)
        return self.fairprice

    def get_reward_risk_ratio(self):
        self.df['RewardRiskRatio'] = self.goal_chance * self.min_goal * (self.goalprice - self.df['Close']) / \
                                      (self.bust_chance * (self.df['Close'] - self.df['StopLoss']))

        self.rewardriskratio = round(self.df['RewardRiskRatio'].mean(), 2)
        return self.rewardriskratio

    def static_analysis(self, printoutput=True):
        # Calculate some stats
        self.get_lastprice()
        self.get_goalprice()
        self.get_atr(period=5)
        self.get_ema(period=5)
        self.get_ema(period=20)
        self.get_kc()

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
        self.goalprice = round(self.lastprice * (1 + self.min_goal), 2)
        return self.goalprice

    def get_stoploss(self):
        """Returns stop loss and stop loss percent"""
        self.df['StopLoss'] = self.df['Close'] - self.atr_multiplier * self.df['ATR']
        self.df['StopLossPercent'] = 1 - self.df['StopLoss'] / self.df['Close']
        self.stoplosspercent = self.df['StopLossPercent'].max()
        self.stoploss = round(self.df.Close[-1:].values[0] * (1 - self.stoplosspercent), 2)

        return self.stoploss, self.stoplosspercent

    def get_lastprice(self):
        self.lastprice = float(round(self.df.Close[-1:].values[0], 2))
        return self.lastprice

    def get_data(self):
        if self.source == 'moex':
            self.get_data_from_moex(cachedir=os.path.join(self.cachebase, 'cache-m'))
        if self.source == 'alpha':
            self.get_prices_from_alpha(key=self.key, cachedir=os.path.join(self.cachebase, 'cache'))
            self.fix_alpha_columns()
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

        r = requests.get(url=url)
        data = r.json()
        last = data['Meta Data']['3: Last Refreshed']
        ema200 = data['Technical Analysis: EMA'][last]['EMA']
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
        df = pd.concat([self.df['date'], self.df['Close'], self.df['Volume'], self.df['BreakoutUp'],
                        self.df['BreakoutDown']], axis=1)
        df.date = pd.to_datetime(df['date'], format='%Y-%m-%d')
        df = df.set_index('date')
        df['Close'] = df.Close.replace(to_replace=0, method='ffill')
        df['Volume'] = df.Volume.replace(to_replace=0, method='ffill')
        fig = plt.figure(figsize=(15, 8))
        plt.subplot2grid((4, 1), (0, 0), rowspan=2)
        plt.title(msg + ' ' + self.symbol + ' RRR: ' + str(self.rewardriskratio))

        plt.plot(df.index, df.Close, 'k', label='Price', linewidth=2.0)

        if 'ATR' in columns:
            df['ATR'] = self.df.ATR.values

        if 'EMA5' in columns:
            df['EMA5'] = self.df.EMA5.values
            plt.plot(df.index, df.EMA5, 'b', label='EMA5', linestyle='--')

        if 'EMA20' in columns:
            df['EMA20'] = self.df.EMA20.values
            plt.plot(df.index, df.EMA20, 'r', label='EMA20', linestyle='--')

        if 'KC_LOW' in columns:
            df['KC_LOW'] = self.df.KC_LOW.values

        if 'KC_HIGH' in columns:
            df['KC_HIGH'] = self.df.KC_HIGH.values

        if 'KC_LOW' in columns and 'KC_HIGH' in columns:
            plt.fill_between(df.index, df.KC_LOW, df.KC_HIGH, color='b', alpha=0.1)

        if self.stoploss > 0:
            plt.axhline(y=self.stoploss, color='m', linestyle=':', label='StopLoss')

        if self.goalprice > 0:
            plt.axhline(y=self.goalprice, color='c', linestyle=':', label='Goal')

        if self.anomaly_filter_up.any():
            plt.scatter(df[df['BreakoutUp']].index, df[df['BreakoutUp']].Close, marker='^', color='b',
                        label='BreakoutUp')

        if self.anomaly_filter_down.any():
            plt.scatter(df[df['BreakoutDown']].index, df[df['BreakoutDown']].Close, marker='v', color='r',
                        label='BreakoutDown')

        if self.trendline is not None:
            polynomial = np.poly1d(self.trendline)
            x = np.linspace(0, len(df.index)-1, num=len(df.index))
            y = polynomial(x)
            plt.plot(df.index, y, color='g', label='Trend', linestyle='-.', linewidth=1.0)

        plt.legend()
        plt.grid()

        ax1 = plt.subplot2grid((4, 1), (2, 0), rowspan=1)

        ax1.plot(df.index, df.Volume, 'g', label='Volume')
        ax1.set_ylabel('Volume', color='g')

        if 'Openpositions' in columns:
            ax2 = ax1.twinx()
            df['Openpositions'] = self.df.Openpositions.values
            ax2.plot(df.index, df.Openpositions, 'b', label='Openpositions')
            ax2.legend()

        ax1.grid()

        if 'ATR' in columns:
            plt.subplot2grid((4, 1), (3, 0), rowspan=1)
            plt.plot(df.index, df.ATR, 'r', label='ATR')
            plt.legend()
            plt.grid()

        fig.tight_layout()
        plt.show()

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

    def get_kc(self, period=5):
        self.df['KC_LOW'] = self.df['EMA' + str(period)] - self.kc_channel * self.df['ATR']
        self.df['KC_HIGH'] = self.df['EMA' + str(period)] + self.kc_channel * self.df['ATR']

    def get_bust_chance(self, sims=1000, bust=0.1, goal=0.1, plot=False):
        # Monte-Carlo
        self.df['Return'] = self.df['Close'].pct_change().fillna(0)

        # print('Real returns stats:')
        # pprint(self.df['Return'].describe())
        # print()

        mc = self.df['Return'].montecarlo(sims=sims, bust=-1 * bust, goal=goal)

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

        self.anomalies = self.anomaly_filter_up.sum() + self.anomaly_filter_down.sum()

        return self.anomalies

    def detect_trend(self):
        # EMA5 > EMA20 means up trend?
        self.df['UpTrend'] = self.df.EMA5.fillna(0) >= self.df.EMA20.fillna(0)
        self.df['DownTrend'] = self.df.EMA5.fillna(0) <= self.df.EMA20.fillna(0)

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
