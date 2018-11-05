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
        self.min_RewardRiskRatio = 10
        self.atr_multiplier = 5
        self.accepted_goal_chance = 0.33

    def check_watchlist(self):
        """Do magic"""

        results = list()
        for item in self.watchdata:

            symbol, entry_price = configs.alphaconf.get_symbol(item)

            print()
            print(symbol)

            if symbol == 'TCS':
                continue

            asset = libs.assets.ASSET(symbol=symbol, source=self.source, asset_type=self.asset_type, key=self.key,
                                      min_goal=self.min_goal, atr_multiplier=self.atr_multiplier)

            # Fetch data from the source
            asset.get_data()

            # Perform static analysis
            asset.static_analysis(printoutput=True)
            if asset.stoploss <= 0:
                continue

            # asset.plot()

            # Calculate chances
            asset.get_bust_chance(bust=asset.stoplosspercent, sims=10000, goal=self.min_goal)
            print('Bust chance:', round(asset.bust_chance, 2))
            print('Goal chance:', round(asset.goal_chance, 2))

            # Reward-risk ratio
            if asset.goal_chance > self.accepted_goal_chance:
                asset.get_reward_risk_ratio()
                print('Reward-Risk ratio:', asset.rewardriskratio)

            # Filter out too risky stuff
            if asset.rewardriskratio >= self.min_RewardRiskRatio and asset.goal_chance > self.accepted_goal_chance:
                results.append(asset.get_results())
                asset.plot()

        print('Results:')
        pprint(results)

        # Save results
        today = datetime.today()
        filename = self.source + '-' + str(today.strftime("%Y-%m-%d")) + '.json'
        filepath = os.path.join('', 'recomendations', filename)
        with open(filepath, 'w') as outfile:
            json.dump(results, outfile, indent=4)


if __name__ == "__main__":
    adv = ADVISOR(datatype='m')
    fire.Fire(adv.check_watchlist)
