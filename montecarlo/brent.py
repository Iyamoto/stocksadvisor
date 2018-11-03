"""Working with Moex Brent
https://www.moex.com/ru/contract.aspx?code=Si-12.18
https://www.moex.com/ru/derivatives/
https://www.moex.com/ru/derivatives/contracts.aspx
"""

import time
import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd
import matplotlib.pyplot as plt
import libs.futures

symbol = 'BRZ8'
futures = libs.futures.FUTURES(symbol=symbol)
futures.get_data_from_moex(cachedir=os.path.join('..', 'cache-m'))

futures.get_atr(period=14)
futures.get_ema(period=14)

futures.df['KC_LOW'] = futures.df['EMA'] - 2 * futures.df['ATR']
futures.df['KC_HIGH'] = futures.df['EMA'] + 2 * futures.df['ATR']

futures.df.pop('Open')
futures.df.pop('High')
futures.df.pop('Low')
futures.df.pop('Openpositionsvalue')

futures.plot()

futures.df.pop('KC_LOW')
futures.df.pop('KC_HIGH')

print(futures.df.corr())

print(futures.df.tail(10))

