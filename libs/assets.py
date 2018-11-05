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

class ASSET(object):
    """Single asset"""

    def __init__(self, symbol='', source='moex', asset_type='stock', key='demo', min_goal=0.1,
                 volumefield='VOLUME', atr_multiplier=5, cacheage=3600*24*5, cachebase=''):
        """
        source: moex, alpha
        type: stock, futures
        """
        self.symbol = symbol
        self.asset_type = asset_type
        self.source = source
        self.volumefield = volumefield
        self.cacheage = cacheage
        self.key = key
        self.cachebase = cachebase
        self.min_goal = min_goal
        self.atr_multiplier = atr_multiplier

        if self.asset_type == 'stock':
            self.boardid = 'TQBR'
        if self.asset_type == 'futures':
            self.boardid = 'RFUD'

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

    def __str__(self):
        result = self.get_results()
        out = json.dumps(result, indent=4)
        return out

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
        stop_loss, bust = self.get_stoploss()
        if stop_loss <= 0:
            self.get_results()
            print(self)
            raise ValueError('Negative stop-loss')  # Debug

        # Calculate trend
        trend = self.detect_trend()

        # Count anomalies
        anomalies = self.count_anomalies()

        if printoutput:
            print('Last price:', self.lastprice)
            print('Exit price:', self.goalprice)
            print('Bust:', self.stoplosspercent)
            print('Stop loss:', self.stoploss)
            print('Trend:', trend)
            print('Anomalies:', anomalies)

    def get_results(self):
        result = dict()
        result[self.symbol] = collections.OrderedDict()
        result[self.symbol]['last_price'] = self.lastprice
        result[self.symbol]['stop_loss'] = self.stoploss
        result[self.symbol]['exit_price'] = self.goalprice
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

    def get_prices_from_alpha(self, key='', cachedir='cache'):
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
        data.to_csv(filepath)

        self.df = data
        return data

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
        filepath = os.path.join(cachedir, filename)
        data.to_csv(filepath, index=False)

        time.sleep(timeout)

        return data

    def plot(self):
        columns = self.df.columns
        df = pd.concat([self.df['date'], self.df['Close'], self.df['Volume']], axis=1)
        df.date = pd.to_datetime(df['date'], format='%Y-%m-%d')
        df = df.set_index('date')
        df['Close'] = df.Close.replace(to_replace=0, method='ffill')
        df['Volume'] = df.Volume.replace(to_replace=0, method='ffill')
        fig = plt.figure(figsize=(15, 8))
        plt.subplot2grid((4, 1), (0, 0), rowspan=2)
        plt.title(self.symbol)

        plt.plot(df.index, df.Close, 'k', label='Price')

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
            plt.fill_between(df.index, df.KC_LOW, df.KC_HIGH, color='b', alpha=0.2)

        if self.stoploss > 0:
            plt.axhline(y=self.stoploss, color='m', linestyle=':', label='StopLoss')

        if self.goalprice > 0:
            plt.axhline(y=self.goalprice, color='c', linestyle=':', label='Goal')

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
        self.df['KC_LOW'] = self.df['EMA' + str(period)] - 2 * self.df['ATR']
        self.df['KC_HIGH'] = self.df['EMA' + str(period)] + 2 * self.df['ATR']

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

        # print(mc.data[1].describe())
        # print(mc.data)

        if plot:
            mc.plot(title=self.symbol, figsize=(15, 5))

        return self.bust_chance, self.goal_chance

    def count_anomalies(self, period=5, ratio=2):
        low = self.df['Low'].values
        low = low.astype(float)
        high = self.df['High'].values
        high = high.astype(float)
        close = self.df['Close'].values
        close = close.astype(float)
        atr = talib.ATR(high, low, close, timeperiod=period)
        ema = talib.EMA(close, timeperiod=period)

        ema = ema[period:]
        atr = atr[period:]
        close = close[period:]

        count = (close < (ema - ratio * atr)).sum()
        count += (close > (ema + ratio * atr)).sum()
        self.anomalies = count

        return count

    def detect_trend(self):
        # EMA5 > EMA20 means up trend
        self.df['UpTrend'] = self.df.EMA5.fillna(0) >= self.df.EMA20.fillna(0)
        self.df['DownTrend'] = self.df.EMA5.fillna(0) <= self.df.EMA20.fillna(0)

        if self.df['UpTrend'].sum() >= 0.85 * len(self.df['UpTrend']):
            trend = 'Up'
        elif self.df['DownTrend'].sum() >= 0.85 * len(self.df['DownTrend']):
            trend = 'Down'
        else:
            trend = 'Sideways'

        self.trend = trend
        return trend
