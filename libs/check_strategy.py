"""
Trade strategy checker
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
from pprint import pprint
import pandas as pd
import configs.alphaconf
import libs.stockslib as sl
import libs.strategy

watchdata = configs.alphaconf.symbols

window = 90
profit = 10
strategy_name = libs.strategy.ema50_close_to_ema200

price_type = 'Adjusted close'
ratios = dict()
for item in watchdata:

    # Parse watchlist
    if type(item) == dict:
        price = list(item.values())[0]
        symbol = list(item.keys())[0]
    else:
        symbol = item
        price = 0

    # Get prices
    res = sl.RESOURCE(symbol=symbol)
    res.get_prices_from_alpha(key=configs.alphaconf.key, cacheage=3600*24*7, cachedir=os.path.join('..', 'cache'))
    res.get_history_from_alpha(key=configs.alphaconf.key, cachedir=os.path.join('..', 'history'))
    res.fix_alpha_columns()
    res.fix_alpha_history_columns()

    # Cut some data
    df = res.history.tail(365*5)
    df = df.reset_index()
    df = df.drop(axis=1, columns='date')

    # Get Max values
    MAX = pd.Series(df[price_type].iloc[::-1].rolling(window=window).max(), name='MAX')
    df = df.join(MAX[::-1])
    df = df.dropna()
    df = df.reset_index()
    df = df.drop(axis=1, columns='index')

    # Apply strategy
    df = strategy_name(df, pricetype='Adjusted close')

    # Calculate profit
    df['profit'] = 100 * (df['MAX'] - df[price_type]) / df[price_type]
    df['result'] = df['profit'] > profit

    # Clean up
    df.pop('MAX')
    df.pop('Open')
    df.pop('High')
    df.pop('Low')
    df.pop('Volume')
    df.pop('Close')
    df.pop('7. dividend amount')
    df.pop('8. split coefficient')

    # Validate strategy
    buys = df[df['buy']]
    bad = buys.query('result == False')['result'].count()
    good = buys.query('result == True')['result'].count()
    if good ==0 and bad ==0:
        ratio = 0
    else:
        ratio = round(good / (good + bad), 2)
    ratios[symbol] = ratio
    if ratio > 0.75:
        print(symbol, ratio)

print(ratios)
