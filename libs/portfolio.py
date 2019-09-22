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
        self.money = money
        self.data = dict()
        self.key = configs.alphaconf.key
        self.caching = caching
        self.cacheage = cacheage

        pd.options.display.max_rows = 200
        self.df = pd.DataFrame()

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

    def __str__(self):
        data = dict()
        data[self.name] = dict()
        data[self.name]['money'] = self.money
        symbols = self.data.keys()

        for symbol in symbols:
            data[self.name][symbol] = self.data[symbol]['share']

        rez = json.dumps(data, indent=4)
        return rez
