"""
Trade strategies
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import talib
from pprint import pprint
import pandas as pd


def ema50_close_to_ema200(df, pricetype='Adjusted close'):
    price = df[pricetype].values

    output = talib.EMA(price, timeperiod=50)
    EMA = pd.Series(output, name='EMA50')
    df = df.join(EMA)

    output = talib.EMA(price, timeperiod=200)
    EMA = pd.Series(output, name='EMA200')
    df = df.join(EMA)

    df['buy'] = (df['EMA50'] > df['EMA200']) & (df['EMA50'] - df['EMA200']) < (df[pricetype] * 0.01)

    df.pop('EMA50')
    df.pop('EMA200')

    return df

def price_above_sma200(df, pricetype='Adjusted close'):
    price = df[pricetype].values

    output = talib.SMA(price, timeperiod=200)
    SMA = pd.Series(output, name='SMA200')
    df = df.join(SMA)

    df['buy'] = df[pricetype] > df['SMA200']

    df.pop('SMA200')

    return df



