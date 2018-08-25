"""
R&D
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import talib
from pprint import pprint
import pandas as pd
import configs.alphaconf
import libs.stockslib as sl

watchdata = configs.alphaconf.symbols

for item in watchdata:

    # Parse watchlist
    if type(item) == dict:
        price = list(item.values())[0]
        symbol = list(item.keys())[0]
    else:
        symbol = item
        price = 0

    res = sl.RESOURCE(symbol=symbol)
    res.get_prices_from_alpha(key=configs.alphaconf.key, cacheage=3600*24*7, cachedir='..\cache')
    res.get_history_from_alpha(key=configs.alphaconf.key, cachedir='..\history')
    res.fix_alpha_columns()
    res.fix_alpha_history_columns()

    ####

    df = res.history.tail(365*5)
    df = df.reset_index()

    window = 90
    profit = 10
    MAX = pd.Series(df['Close'].iloc[::-1].rolling(window=window).max(), name='MAX')

    close = df['Close'].values

    output = talib.EMA(close, timeperiod=50)
    EMA = pd.Series(output, name='EMA50')
    df = df.join(EMA)

    output = talib.EMA(close, timeperiod=200)
    EMA = pd.Series(output, name='EMA200')
    df = df.join(EMA)

    df = df.drop(axis=1, columns='date')
    df = df.join(MAX[::-1])
    df = df.dropna()
    df = df.reset_index()
    df = df.drop(axis=1, columns='index')

    df['profit'] = 100 * (df['MAX'] - df['Close']) / df['Close']
    df['result'] = df['profit'] > profit

    df['buy'] = (df['EMA50'] - df['EMA200']).abs() < (df['Close'] * 0.01)

    df.pop('MAX')
    df.pop('Open')
    df.pop('High')
    df.pop('Low')
    df.pop('Volume')
    df.pop('5. adjusted close')
    df.pop('7. dividend amount')
    df.pop('8. split coefficient')

    buys = df[df['buy']]

    bad = buys.query('result == False')['result'].count()
    good = buys.query('result == True')['result'].count()
    ratio = round(good / (good + bad), 2)
    if ratio > 0.7:
        print(symbol, ratio)



