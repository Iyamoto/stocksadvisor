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
import pandas_montecarlo
from pprint import pprint

symbol = 'BRZ8'
expiration = '03.12.2018'
futures = libs.futures.FUTURES(symbol=symbol)
futures.get_data_from_moex(cachedir=os.path.join('..', 'cache-m'))

futures.get_atr(period=14)
futures.get_ema(period=14)
futures.get_kc()

futures.df.pop('Open')
futures.df.pop('High')
futures.df.pop('Low')
futures.df.pop('Openpositionsvalue')

# futures.plot()

futures.df.pop('KC_LOW')
futures.df.pop('KC_HIGH')

print(futures.df.corr())
print()

# Stop loss and reward-risk ratio
futures.df['StopLoss'] = futures.df['Close'] - 2.1 * futures.df['ATR']
futures.df['StopLossPercent'] = 1 - futures.df['StopLoss'] / futures.df['Close']
pprint(futures.df['StopLossPercent'].describe())

# futures.df['RewardRiskRatio'] = 0.11 * futures.df['Close'] / (futures.df['Close'] - futures.df['StopLoss'])
#
# print(futures.df.tail())
# print()
# print(futures.df['RewardRiskRatio'].describe())

# Monte-Carlo
futures.df['Return'] = futures.df['Close'].pct_change().fillna(0)
pprint(futures.df.tail())
print()

mc = futures.df['Return'].montecarlo(sims=100, bust=-0.06, goal=0.0)

pprint(mc.stats)
print()
pprint(mc.maxdd)

mc.plot(title=symbol, figsize=(15, 5))
