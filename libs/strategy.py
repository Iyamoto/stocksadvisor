"""
Trade strategies
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import talib
from pprint import pprint
import pandas as pd


def price_close_to_sma200(df, pricetype='Close'):
    price = df[pricetype].values

    output = talib.EMA(price, timeperiod=50)
    EMA = pd.Series(output, name='EMA50')
    df = df.join(EMA)

    output = talib.EMA(price, timeperiod=200)
    EMA = pd.Series(output, name='EMA200')
    df = df.join(EMA)

    df['buy'] = (df['EMA50'] - df['EMA200']).abs() < (df['Close'] * 0.01)

    df.pop('EMA50')
    df.pop('EMA200')

    return df



