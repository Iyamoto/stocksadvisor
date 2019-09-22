"""
Portfolio class
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import json
import libs.assets
import configs.alphaconf


class PORTFOLIO(object):
    """PORTFOLIO class"""

    def __init__(self, name='No name', caching=True, cacheage=3600 * 48):
        self.name = name
        self.data = dict()
        self.key = configs.alphaconf.key
        self.caching = caching
        self.cacheage = cacheage

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

    def __str__(self):
        data = dict()
        data[self.name] = dict()
        symbols = self.data.keys()

        for symbol in symbols:
            data[self.name][symbol] = self.data[symbol]['share']

        rez = json.dumps(data, indent=4)
        return rez
