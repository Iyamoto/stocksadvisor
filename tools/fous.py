"""
Testing fous strategy
"""

import sys
import os
import json
sys.path.insert(0, os.path.abspath('..'))
import libs.assets
import pandas as pd
import configs.alphaconf
from pprint import pprint
import numpy as np


def trendline(data, order=1):
    coeffs = np.polyfit(data.index.values, list(data), order)
    return coeffs


def get_assettype(datatype='ms'):
    if datatype == 'ms':
        watchdata = configs.alphaconf.symbols_m
        source = 'moex'
        asset_type = 'stock'
    if datatype == 'a':
        watchdata = configs.alphaconf.symbols
        source = 'alpha'
        asset_type = 'stock'
    if datatype == 'mc':
        watchdata = configs.alphaconf.symbols_mc
        source = 'moex'
        asset_type = 'currency'
    if datatype == 'mf':
        watchdata = configs.alphaconf.symbols_mf
        source = 'moex'
        asset_type = 'futures'
    if datatype == 'me':
        watchdata = configs.alphaconf.symbols_me
        source = 'moex'
        asset_type = 'etf'
    return watchdata, source, asset_type


if __name__ == "__main__":
    pd.options.display.max_rows = 200

    watchdata, source, asset_type = get_assettype(datatype='ms')
    # watchdata, source, asset_type = get_assettype(datatype='a')
    for item in watchdata:
        symbol, entry_price, limit, dividend = configs.alphaconf.get_symbol(item)
        print(symbol)
        # symbol = 'HAS'
        asset = libs.assets.ASSET(symbol=symbol, source=source, key=configs.alphaconf.key, cacheage=3600*24)
        asset.get_data()
        asset.static_analysis()
        asset.find_event()
        if asset.df.Max.sum() > 0 and asset.df.Max[asset.df.Max >= asset.lastprice].sum() > 0:
            event_index = asset.df.Max[asset.df.Max >= asset.lastprice][-1:].index.values[0]
            taillen = len(asset.df) - event_index
            if taillen >= 5:
                trend = trendline(asset.df['Close'].tail(taillen))
                angle = trend[0]
                if angle > 0:
                    print('Fair price based on divs:', asset.get_fair_price(dividend=dividend))

                    asset.get_bust_chance(bust=asset.stoplosspercent, sims=10000, plot=False, taillen=taillen)
                    print('Bust chance:', round(asset.bust_chance, 2))
                    print('Goal chance:', round(asset.goal_chance, 2))
                    asset.get_reward_risk_ratio()
                    print('Reward-Risk ratio:', asset.rewardriskratio)

                    asset.plot_fous()
