"""Working with Moex Brent
https://www.moex.com/ru/contract.aspx?code=Si-12.18
https://www.moex.com/ru/derivatives/
https://www.moex.com/ru/derivatives/contracts.aspx
"""

import time
import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import libs.futures

min_goal = 0.1
min_RewardRiskRatio = 2
atr_multiplier = 5

symbol = 'MOEX'

print(symbol)

futures = libs.futures.FUTURES(symbol=symbol, boardid='TQBR')
futures.get_data_from_moex(cachedir=os.path.join('..', 'cache-m'))

futures.get_atr(period=5)
futures.get_ema(period=5)
futures.get_kc()

futures.df.pop('Open')
futures.df.pop('High')
futures.df.pop('Low')

# futures.plot()

futures.df.pop('KC_LOW')
futures.df.pop('KC_HIGH')

# Stop loss
futures.df['StopLoss'] = futures.df['Close'] - atr_multiplier * futures.df['ATR']
futures.df['StopLossPercent'] = 1 - futures.df['StopLoss'] / futures.df['Close']
bust = futures.df['StopLossPercent'].max()

print('Last price:', round(futures.df.Close[-1:].values[0], 2))
print('Bust:', bust)
print('StopLoss:', round(futures.df.Close[-1:].values[0]*(1-bust), 2))
print()

bust_chance, goal_chance = futures.get_bust_chance(bust=bust, sims=10000, goal=min_goal)
print('Bust chance:', round(bust_chance, 2))
print('Goal chance:', round(goal_chance, 2))
print()

# Reward-risk ratio
for i in range(1, 10):
    goal = i * min_goal
    futures.df['RewardRiskRatio'] = (goal_chance/i) * goal * futures.df['Close'] / \
        (bust_chance * (futures.df['Close'] - futures.df['StopLoss']))
    if futures.df['RewardRiskRatio'].mean() > min_RewardRiskRatio:
        break

print('Reward-Risk ratio:', futures.df['RewardRiskRatio'].mean())
print('Goal:', goal)
print('Exit price:', round(futures.df.Close[-1:].values[0] * (1 + goal), 2))
print()

if goal > min_goal:
    print('RewardRiskRatio is to low, calculating new goal chances')
    bust_chance, goal_chance = futures.get_bust_chance(bust=bust, goal=goal)
    print('Goal chance:', round(goal_chance, 2))
    print()
