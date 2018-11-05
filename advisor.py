"""
Stocks Advisor 1.1
Based on randomness
"""

import time
import sys
import os
import json
sys.path.insert(0, os.path.abspath('..'))
import libs.assets
import configs.alphaconf
from pprint import pprint
from datetime import datetime
import collections

min_goal = 0.1
min_RewardRiskRatio = 50
atr_multiplier = 5

datatype = 'm'
asset_type = 'stock'

if datatype == 'm':
    watchdata = configs.alphaconf.symbols_m
    source = 'moex'
else:
    watchdata = configs.alphaconf.symbols
    source = 'alpha'

key = configs.alphaconf.key
results = dict()
for item in watchdata:

    symbol, entry_price = configs.alphaconf.get_symbol(item)

    print(symbol)

    asset = libs.assets.ASSET(symbol=symbol, source=source, asset_type=asset_type, key=key)

    # Fetch data from the source
    asset.get_data()

    # Calculate some stats
    asset.get_atr(period=5)
    asset.get_ema(period=5)
    asset.get_ema(period=20)
    asset.get_kc()

    asset.plot()

    # Calculate trend
    trend = asset.detect_trend()
    print('Trend:', trend)

    # Count anomalies
    anomalies = asset.count_anomalies()
    if anomalies > 0:
        print('Anomaly detected:', anomalies)

    # Stop loss
    asset.df['StopLoss'] = asset.df['Close'] - atr_multiplier * asset.df['ATR']
    asset.df['StopLossPercent'] = 1 - asset.df['StopLoss'] / asset.df['Close']
    bust = asset.df['StopLossPercent'].max()

    stop_loss = round(asset.df.Close[-1:].values[0] * (1 - bust), 2)
    if stop_loss <= 0:
        continue

    print('Last price:', round(asset.df.Close[-1:].values[0], 2))
    print('Bust:', bust)
    print('StopLoss:', stop_loss)
    print()

    bust_chance, goal_chance = asset.get_bust_chance(bust=bust, sims=10000, goal=min_goal)
    print('Bust chance:', round(bust_chance, 2))
    print('Goal chance:', round(goal_chance, 2))
    print()

    # Reward-risk ratio
    for i in range(1, 5):
        goal = i * min_goal
        if bust_chance < 0.001:
            bust_chance = 0.001
        asset.df['RewardRiskRatio'] = (goal_chance / i) * goal * asset.df['Close'] / \
                                      (bust_chance * (asset.df['Close'] - asset.df['StopLoss']))
        if asset.df['RewardRiskRatio'].mean() > min_RewardRiskRatio:
            break

    print('Reward-Risk ratio:', asset.df['RewardRiskRatio'].mean())
    print('Goal:', goal)
    print('Exit price:', round(asset.df.Close[-1:].values[0] * (1 + goal), 2))
    print()

    if goal > min_goal:
        print('RewardRiskRatio is to low')
        # bust_chance, goal_chance = futures.get_bust_chance(bust=bust, goal=goal)
        # print('Goal chance:', round(goal_chance, 2))
        # print()
    else:
        results[symbol] = collections.OrderedDict()
        results[symbol]['last_price'] = float(round(asset.df.Close[-1:].values[0], 2))
        results[symbol]['stop_loss'] = stop_loss
        results[symbol]['exit_price'] = round(asset.df.Close[-1:].values[0] * (1 + goal), 2)
        results[symbol]['goal'] = goal
        results[symbol]['goal_chance'] = round(goal_chance, 2)
        results[symbol]['bust'] = round(bust, 2)
        results[symbol]['bust_chance'] = round(bust_chance, 2)
        results[symbol]['reward_risk_ratio'] = round(asset.df['RewardRiskRatio'].mean(), 2)
        results[symbol]['trend'] = trend
        results[symbol]['anomalies'] = float(anomalies)

    break

print('Results')
pprint(results)

exit()

# Save results
today = datetime.today()
filename = datatype + '-' + str(today.strftime("%Y-%m-%d")) + '.json'
filepath = os.path.join('..', 'recomendations', filename)
with open(filepath, 'w') as outfile:
    json.dump(results, outfile, indent=4)
