"""
Trade strategies
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import talib
from pprint import pprint
import pandas as pd


def max_close_to_may(df, pricetype='Adjusted close', indicator='EMA', x=50, y=200):
    price = df[pricetype].values
    method = getattr(talib, indicator)

    output = method(price, timeperiod=x)
    EMAx = pd.Series(output, name='MAx')
    df = df.join(EMAx)

    output = method(price, timeperiod=y)
    EMAy = pd.Series(output, name='MAy')
    df = df.join(EMAy)

    df['buy'] = (df['MAx'] > df['MAy']) & (df['MAx'] - df['MAy']) < (df[pricetype] * 0.01)

    df.pop('MAx')
    df.pop('MAy')

    return df


def ema50_close_to_ema200(df, pricetype='Adjusted close'):
    return max_close_to_may(df, pricetype=pricetype, indicator='EMA', x=50, y=200)


def ema50_close_to_ema100(df, pricetype='Adjusted close'):
    return max_close_to_may(df, pricetype=pricetype, indicator='EMA', x=50, y=100)


def ema20_close_to_ema50(df, pricetype='Adjusted close'):
    return max_close_to_may(df, pricetype=pricetype, indicator='EMA', x=20, y=50)


def price_above_ma(df, pricetype='Adjusted close', indicator='SMA', period=100):
    price = df[pricetype].values
    method = getattr(talib, indicator)
    output = method(price, timeperiod=period)
    MA = pd.Series(output, name='MA')
    df = df.join(MA)

    df['buy'] = df[pricetype] > df['MA']

    df.pop('MA')

    return df


def price_above_sma200(df, pricetype='Adjusted close'):
    return price_above_ma(df, pricetype=pricetype, indicator='SMA', period=200)


def price_above_ema200(df, pricetype='Adjusted close'):
    return price_above_ma(df, pricetype=pricetype, indicator='EMA', period=200)


def price_above_ema100(df, pricetype='Adjusted close'):
    return price_above_ma(df, pricetype=pricetype, indicator='EMA', period=100)


def rsi_bellow_x(df, pricetype='Adjusted close', indicator='RSI', period=5, x=40):
    price = df[pricetype].values
    method = getattr(talib, indicator)
    output = method(price, timeperiod=period)
    rsi = pd.Series(output, name='RSI')
    df = df.join(rsi)

    df['buy'] = df['RSI'] < x

    df.pop('RSI')

    return df


def rsi5_bellow_40(df, pricetype='Adjusted close'):
    return rsi_bellow_x(df, pricetype=pricetype, indicator='RSI', period=5, x=40)


def rsi14_bellow_40(df, pricetype='Adjusted close'):
    return rsi_bellow_x(df, pricetype=pricetype, indicator='RSI', period=14, x=40)

def rsi14_bellow_30(df, pricetype='Adjusted close'):
    return rsi_bellow_x(df, pricetype=pricetype, indicator='RSI', period=14, x=30)
