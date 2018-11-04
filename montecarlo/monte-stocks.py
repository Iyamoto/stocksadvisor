"""Working with Moex Brent
https://www.moex.com/ru/contract.aspx?code=Si-12.18
https://www.moex.com/ru/derivatives/
https://www.moex.com/ru/derivatives/contracts.aspx
"""

import time
import sys
import os
import json
sys.path.insert(0, os.path.abspath('..'))
import libs.futures
import configs.alphaconf
from pprint import pprint
from datetime import datetime
import collections

min_goal = 0.1
min_RewardRiskRatio = 50
atr_multiplier = 5

results = dict()
datatype = 'a'

if datatype == 'm':
    watchdata = configs.alphaconf.symbols_m
else:
    watchdata = configs.alphaconf.symbols
    key = configs.alphaconf.key

for item in watchdata:

    # Parse watchlist
    if type(item) == dict:
        price = list(item.values())[0]
        symbol = list(item.keys())[0]
    else:
        symbol = item
        price = 0

    print(symbol)

    futures = libs.futures.FUTURES(symbol=symbol, boardid='TQBR')
    if datatype == 'm':
        futures.get_data_from_moex(cachedir=os.path.join('..', 'cache-m'))
    else:
        futures.get_prices_from_alpha(key=key, cachedir=os.path.join('..', 'cache'))
        futures.fix_alpha_columns()

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
    for i in range(1, 5):
        goal = i * min_goal
        if bust_chance < 0.001:
            bust_chance = 0.001
        futures.df['RewardRiskRatio'] = (goal_chance/i) * goal * futures.df['Close'] / \
            (bust_chance * (futures.df['Close'] - futures.df['StopLoss']))
        if futures.df['RewardRiskRatio'].mean() > min_RewardRiskRatio:
            break

    print('Reward-Risk ratio:', futures.df['RewardRiskRatio'].mean())
    print('Goal:', goal)
    print('Exit price:', round(futures.df.Close[-1:].values[0] * (1 + goal), 2))
    print()

    if goal > min_goal:
        print('RewardRiskRatio is to low')
        # bust_chance, goal_chance = futures.get_bust_chance(bust=bust, goal=goal)
        # print('Goal chance:', round(goal_chance, 2))
        # print()
    else:
        results[symbol] = collections.OrderedDict()
        results[symbol]['last_price'] = round(futures.df.Close[-1:].values[0], 2)
        results[symbol]['stop_loss'] = round(futures.df.Close[-1:].values[0] * (1 - bust), 2)
        results[symbol]['exit_price'] = round(futures.df.Close[-1:].values[0] * (1 + goal), 2)
        results[symbol]['goal'] = goal
        results[symbol]['goal_chance'] = round(goal_chance, 2)
        results[symbol]['bust'] = round(bust, 2)
        results[symbol]['bust_chance'] = round(bust_chance, 2)
        results[symbol]['reward_risk_ratio'] = round(futures.df['RewardRiskRatio'].mean(), 2)

print('Results')
pprint(results)

# Save results
today = datetime.today()
filename = datatype + '-' + str(today.strftime("%Y-%m-%d")) + '.json'
filepath = os.path.join('..', 'recomendations', filename)
with open(filepath, 'w') as outfile:
    json.dump(results, outfile, indent=4)
