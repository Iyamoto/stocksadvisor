"""
RND
"""

import sys
import os
import json
sys.path.insert(0, os.path.abspath('..'))
import libs.assets
import pandas as pd
import configs.alphaconf
from pprint import pprint
from datetime import datetime
import fire
import matplotlib.pyplot as plt
from scipy.signal import argrelextrema
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


def plot(in_df=None, symbol=''):
    columns = in_df.columns
    df = pd.concat([in_df['date'], in_df['Close'], in_df['Volume'], in_df['Max']], axis=1)
    df.date = pd.to_datetime(df['date'], format='%Y-%m-%d')
    df['Close'] = df.Close.replace(to_replace=0, method='ffill')
    df['Volume'] = df.Volume.replace(to_replace=0, method='ffill')
    fig = plt.figure(figsize=(15, 8))
    plt.subplot2grid((4, 1), (0, 0), rowspan=2)
    plt.title(symbol)
    plt.plot(df.index, df.Close, 'k', label='Price', linewidth=2.0)

    if 'EMA13' in columns:
        df['EMA13'] = in_df.EMA13.values
        plt.plot(df.index, df.EMA13, 'b', label='EMA13', linestyle='--')

    plt.scatter(df.index, df['Max'], c='g')

    plt.legend()
    plt.grid()

    ax1 = plt.subplot2grid((4, 1), (2, 0), rowspan=1)
    ax1.plot(df.index, df.Volume, 'g', label='Volume')
    ax1.set_ylabel('Volume', color='g')

    fig.tight_layout()
    plt.show()


def find_event(df=None, points=5):
    std = round(asset.df['Volume'].std(), 1)
    mean = round(asset.df['Volume'].mean(), 1)
    event_filter = df.Volume > mean + 2*std
    df['Event'] = event_filter

    df['tmp'] = df.iloc[argrelextrema(df.Close.values, np.greater_equal, order=points)[0]]['Close']
    df['Max'] = df.tmp[df.Event == True]
    df = df.drop(['Event'], axis=1)
    df = df.drop(['tmp'], axis=1)

    return df


if __name__ == "__main__":
    pd.options.display.max_rows = 200

    watchdata, source, asset_type = get_assettype(datatype='ms')
    for item in watchdata:
        symbol, entry_price, limit, dividend = configs.alphaconf.get_symbol(item)
        print(symbol)
        # symbol = 'HAS'
        asset = libs.assets.ASSET(symbol=symbol, source=source, key=configs.alphaconf.key, cacheage=3600*24)
        asset.get_data()
        asset.get_lastprice()
        asset.get_ema(period=13)
        asset.df = find_event(df=asset.df)
        if asset.df.Max.sum() > 0 and asset.df.Max[asset.df.Max >= asset.lastprice].sum() > 0:
            event_index = asset.df.Max[asset.df.Max >= asset.lastprice][-1:].index.values[0]
            if len(asset.df) - event_index >= 5:
                trend = trendline(asset.df['Close'].tail(len(asset.df) - event_index))
                angle = trend[0]
                if angle > 0:
                    plot(in_df=asset.df, symbol=symbol)

        # break
