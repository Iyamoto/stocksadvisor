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
    symbol = 'T'
    asset = libs.assets.ASSET(symbol=symbol, source='alpha', key=configs.alphaconf.key, cacheage=3600*12)
    asset.get_data()
    asset.get_ema(period=13)
    asset.df = find_event(df=asset.df)
    pprint(asset.df)

    plot(in_df=asset.df, symbol=symbol)
