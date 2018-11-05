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
import fire


class ADVISOR(object):
    """Stocks Advisor"""

    def __init__(self, datatype='m', asset_type='stock'):
        self.asset_type = asset_type

        if datatype == 'm':
            self.watchdata = configs.alphaconf.symbols_m
            self.source = 'moex'
        else:
            self.watchdata = configs.alphaconf.symbols
            self.source = 'alpha'

        self.key = configs.alphaconf.key

        self.tobuy = dict()
        self.tosell = dict()

        self.min_goal = 0.1
        self.min_RewardRiskRatio = 50
        self.atr_multiplier = 5

    def check_watchlist(self):
        """Do magic"""

        results = dict()
        for item in self.watchdata:

            symbol, entry_price = configs.alphaconf.get_symbol(item)

            print(symbol)

            asset = libs.assets.ASSET(symbol=symbol, source=self.source, asset_type=self.asset_type, key=self.key)

            # Fetch data from the source
            asset.get_data()

            # Calculate some stats
            asset.get_lastprice()
            asset.get_atr(period=5)
            asset.get_ema(period=5)
            asset.get_ema(period=20)
            asset.get_kc()

            # Stop loss
            stop_loss, bust = asset.get_stoploss(atr_multiplier=self.atr_multiplier)
            if stop_loss <= 0:
                exit('Negative stop-loss')  # Debug

            print('Last price:', asset.lastprice)
            print('Bust:', asset.stoplosspercent)
            print('StopLoss:', asset.stoploss)
            print()

            asset.plot()

            # Calculate trend
            trend = asset.detect_trend()
            print('Trend:', trend)

            # Count anomalies
            anomalies = asset.count_anomalies()
            if anomalies > 0:
                print('Anomaly detected:', anomalies)

            bust_chance, goal_chance = asset.get_bust_chance(bust=bust, sims=10000, goal=self.min_goal)
            print('Bust chance:', round(bust_chance, 2))
            print('Goal chance:', round(goal_chance, 2))
            print()

            # Reward-risk ratio
            for i in range(1, 5):
                goal = i * self.min_goal
                if bust_chance < 0.001:
                    bust_chance = 0.001
                asset.df['RewardRiskRatio'] = (goal_chance / i) * goal * asset.df['Close'] / \
                                              (bust_chance * (asset.df['Close'] - asset.df['StopLoss']))
                if asset.df['RewardRiskRatio'].mean() > self.min_RewardRiskRatio:
                    break

            print('Reward-Risk ratio:', asset.df['RewardRiskRatio'].mean())
            print('Goal:', goal)
            print('Exit price:', round(asset.df.Close[-1:].values[0] * (1 + goal), 2))
            print()

            if goal > self.min_goal:
                print('RewardRiskRatio is to low')
                # bust_chance, goal_chance = futures.get_bust_chance(bust=bust, goal=goal)
                # print('Goal chance:', round(goal_chance, 2))
                # print()
            else:
                results[symbol] = collections.OrderedDict()
                results[symbol]['last_price'] = asset.lastprice
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

        # # Save results
        # today = datetime.today()
        # filename = datatype + '-' + str(today.strftime("%Y-%m-%d")) + '.json'
        # filepath = os.path.join('..', 'recomendations', filename)
        # with open(filepath, 'w') as outfile:
        #     json.dump(results, outfile, indent=4)


if __name__ == "__main__":
    adv = ADVISOR(datatype='a')
    fire.Fire(adv.check_watchlist)
