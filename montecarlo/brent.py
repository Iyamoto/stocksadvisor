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
import math
import numpy as np

symbol = 'SBER'  # 'SiZ8'  # 'SBER'  # 'BRZ8'
expiration = '03.12.2018'
futures = libs.futures.FUTURES(symbol=symbol) # boardid='TQBR'
futures.get_data_from_moex(cachedir=os.path.join('..', 'cache-m'))

futures.get_atr(period=5)
futures.get_ema(period=5)
futures.get_kc()

futures.df.pop('Open')
futures.df.pop('High')
futures.df.pop('Low')
# futures.df.pop('Openpositionsvalue')

# futures.plot()

futures.df.pop('KC_LOW')
futures.df.pop('KC_HIGH')

print(futures.df.corr())
print()

# Stop loss
futures.df['StopLoss'] = futures.df['Close'] - 5 * futures.df['ATR']
futures.df['StopLossPercent'] = 1 - futures.df['StopLoss'] / futures.df['Close']
bust = futures.df['StopLossPercent'].max()
print('Bust:', bust)

bust_chance, goal_chance = futures.get_bust_chance(bust=bust)
print('Bust chance:', bust_chance)
print('Goal chance:', goal_chance)
print()

# Reward-risk ratio
for i in range(1, 10):
    goal = i * 0.1
    futures.df['RewardRiskRatio'] = goal_chance * goal * futures.df['Close'] / \
        (bust_chance * (futures.df['Close'] - futures.df['StopLoss']))
    if futures.df['RewardRiskRatio'].mean() > 3:
        print('Reward-Risk ratio:', futures.df['RewardRiskRatio'].mean())
        print('Goal:', goal)
        break

