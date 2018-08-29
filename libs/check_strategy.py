"""
Trade strategy checker
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import json
from pprint import pprint
import pandas as pd
import configs.alphaconf
import libs.stockslib as sl
import libs.strategy


def checkstrategy(strategy_name=None, window=20, profit=5, max_ratio=0.51, datatype='m'):
    if datatype == 'm':
        watchdata = configs.alphaconf.symbols_m
        price_type = 'Close'
    else:
        watchdata = configs.alphaconf.symbols
        price_type = 'Adjusted close'

    ratios = dict()
    good_ratio = 0
    for item in watchdata:

        # Parse watchlist
        if type(item) == dict:
            symbol = list(item.keys())[0]
        else:
            symbol = item

        # Get prices
        res = sl.RESOURCE(symbol=symbol)

        if datatype == 'm':
            res.history = res.get_prices_from_moex(days=365 * 5, cachedir=os.path.join('..', 'history-m'))
        else:
            res.get_prices_from_alpha(key=configs.alphaconf.key, cacheage=3600*24*7, cachedir=os.path.join('..', 'cache'))
            res.get_history_from_alpha(key=configs.alphaconf.key, cachedir=os.path.join('..', 'history'))
            res.fix_alpha_columns()
            res.fix_alpha_history_columns()

        # Cut last data
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
        df = strategy_name(df, pricetype=price_type)

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

        if datatype != 'm':
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
        if ratio > max_ratio:
            good_ratio += 1
            print(symbol, ratio)

    print(good_ratio, len(watchdata))

    print(strategy_name)

    print(ratios)
    print()

    ratiopath = os.path.join('..', 'data', datatype, strategy_name.__name__ + '.json')
    with open(ratiopath, 'w') as outfile:
        json.dump(ratios, outfile, indent=4)


for strategy in configs.alphaconf.ratios.keys():
    strategy = getattr(libs.strategy, strategy)
    checkstrategy(strategy_name=strategy, datatype='m')
