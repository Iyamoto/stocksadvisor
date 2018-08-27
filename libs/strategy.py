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


def price_above_ema50(df, pricetype='Adjusted close'):
    return price_above_ma(df, pricetype=pricetype, indicator='EMA', period=50)


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


def rsi_above_x(df, pricetype='Adjusted close', indicator='RSI', period=5, x=60):
    price = df[pricetype].values
    method = getattr(talib, indicator)
    output = method(price, timeperiod=period)
    rsi = pd.Series(output, name='RSI')
    df = df.join(rsi)

    df['buy'] = df['RSI'] > x

    df.pop('RSI')

    return df


def rsi14_above_60(df, pricetype='Adjusted close'):
    return rsi_bellow_x(df, pricetype=pricetype, indicator='RSI', period=14, x=60)


def rsi14_above_70(df, pricetype='Adjusted close'):
    return rsi_bellow_x(df, pricetype=pricetype, indicator='RSI', period=14, x=70)


def price_bellow_kc(df, pricetype='Adjusted close'):
    low = df['Low'].values
    high = df['High'].values
    close = df[pricetype].values
    output = talib.ATR(high, low, close, timeperiod=10)
    atr = pd.Series(output, name='ATR')
    df = df.join(atr)

    output = talib.EMA(close, timeperiod=20)
    ema = pd.Series(output, name='EMA')
    df = df.join(ema)

    df['KC_low'] = df['EMA'] - 1.4 * df['ATR']

    df['buy'] = df['Close'] < df['KC_low']

    df.pop('EMA')
    df.pop('ATR')
    df.pop('KC_low')

    return df


def price_above_kc(df, pricetype='Adjusted close'):
    low = df['Low'].values
    high = df['High'].values
    close = df[pricetype].values
    output = talib.ATR(high, low, close, timeperiod=10)
    atr = pd.Series(output, name='ATR')
    df = df.join(atr)

    output = talib.EMA(close, timeperiod=20)
    ema = pd.Series(output, name='EMA')
    df = df.join(ema)

    df['KC_high'] = df['EMA'] + 1.4 * df['ATR']

    df['buy'] = df['Close'] > df['KC_high']

    df.pop('EMA')
    df.pop('ATR')
    df.pop('KC_high')

    return df


def macd_hist_positive(df, pricetype='Adjusted close'):
    close = df[pricetype].values
    macd, macdsignal, macdhist = talib.MACD(close)
    ma = pd.Series(macdhist, name='MACD_Hist')
    df = df.join(ma)

    df['buy'] = (abs(df['MACD_Hist']) < 0.1 * df['Close']) & (df['MACD_Hist'] > 0)

    df.pop('MACD_Hist')

    return df
