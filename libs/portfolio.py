"""
Portfolio class
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import json
import pandas as pd
import libs.assets
import configs.alphaconf


class PORTFOLIO(object):
    """PORTFOLIO class"""

    def __init__(self, name='No name', money=100000, caching=True, cacheage=3600 * 48):
        self.name = name
        self.initial_money = money
        self.money = money
        self.profit = 0
        self.data = dict()
        self.key = configs.alphaconf.key
        self.caching = caching
        self.cacheage = cacheage

        pd.options.display.max_rows = 200
        self.df = pd.DataFrame()
        self.values = pd.DataFrame()

    def add(self, symbol='', asset_type='etf', source='moex', share=0):
        """
        Add an asset to the portfolio

        Args:
            symbol: Asset ticker
            asset_type: Type, ETF
            source: Data source, MOEX
            share: The asset share in the portfolio, %
        """
        asset = libs.assets.ASSET(symbol=symbol, source=source, asset_type=asset_type, key=self.key,
                                  cacheage=self.cacheage, caching=self.caching)
        self.data[symbol] = dict()
        self.data[symbol]['asset'] = asset
        self.data[symbol]['share'] = share

        asset.get_data()

        if self.df.empty:
            self.df = pd.concat([asset.df['date'], asset.df['Close']], axis=1)
            self.df.date = pd.to_datetime(self.df['date'], format='%Y-%m-%d')
            self.df = self.df.set_index('date')
            self.df = self.df.rename(columns={'Close': symbol})
        else:
            tmp_df = asset.df
            tmp_df.date = pd.to_datetime(tmp_df['date'], format='%Y-%m-%d')
            tmp_df = tmp_df.set_index('date')
            self.df[symbol] = tmp_df['Close']

        price = float(round(self.df[symbol][0:1].values[0], 2))
        self.data[symbol]['count'] = int(self.initial_money * (share / 100) / price)
        self.data[symbol]['value'] = round(self.data[symbol]['count'] * price, 2)
        self.money -= self.data[symbol]['value']

    def run(self):

        final_money = self.money

        for symbol in self.data.keys():
            self.df[symbol + '_value'] = self.df[symbol] * self.data[symbol]['count']
            price = float(round(self.df[symbol][-1:].values[0], 2))
            self.data[symbol]['value'] = round(self.data[symbol]['count'] * price, 2)
            final_money += self.data[symbol]['value']

        self.profit = round(final_money - self.initial_money, 2)

    def __str__(self):
        data = dict()
        data[self.name] = dict()
        data[self.name]['money'] = self.money
        data[self.name]['profit'] = self.profit
        data[self.name]['profit_pct'] = round(100 * self.profit / self.money, 1)
        symbols = self.data.keys()

        for symbol in symbols:
            data[self.name][symbol] = dict()
            data[self.name][symbol]['share'] = self.data[symbol]['share']
            data[self.name][symbol]['count'] = self.data[symbol]['count']
            data[self.name][symbol]['value'] = self.data[symbol]['value']

        rez = json.dumps(data, indent=4)
        return rez
