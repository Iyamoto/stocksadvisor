"""
Stocks Advisor 1.1
Based on randomness
"""

import sys
import os
import json
sys.path.insert(0, os.path.abspath('..'))
import libs.assets
import pandas as pd
import configs.alphaconf
from pprint import pprint
from datetime import datetime
import fire


class ADVISOR(object):
    """Stocks Advisor"""

    def __init__(self, datatype='m', plot_anomaly=False):
        self.plot_anomaly = plot_anomaly

        self.watchdata, self.source, self.asset_type = self.get_assettype(datatype=datatype)
        self.key = configs.alphaconf.key

        self.tobuy = dict()
        self.tosell = dict()

        self.min_goal = 0.1
        self.min_RewardRiskRatio = 10
        self.atr_multiplier = 5
        self.accepted_goal_chance = 0.33

    def get_assettype(self, datatype='ms'):
        if datatype == 'ms':
            watchdata = configs.alphaconf.symbols_m
            source = 'moex'
            asset_type = 'stock'
        if datatype == 'a':
            watchdata = configs.alphaconf.symbols
            source = 'alpha'
            asset_type = 'stock'
        if datatype == 'mc':
            watchdata = configs.alphaconf.symbols_mc
            source = 'moex'
            asset_type = 'currency'
        if datatype == 'mf':
            watchdata = configs.alphaconf.symbols_mf
            source = 'moex'
            asset_type = 'futures'
        if datatype == 'me':
            watchdata = configs.alphaconf.symbols_me
            source = 'moex'
            asset_type = 'etf'
        return watchdata, source, asset_type

    def correlation(self, datatype1='mc', symbol1='USD000UTSTOM',
                    datatype2='me', symbol2='FXGD'):
        watchdata1, source1, asset_type1 = self.get_assettype(datatype=datatype1)
        watchdata2, source2, asset_type2 = self.get_assettype(datatype=datatype2)

        asset1 = libs.assets.ASSET(symbol=symbol1, source=source1, asset_type=asset_type1, key=self.key)
        asset2 = libs.assets.ASSET(symbol=symbol2, source=source2, asset_type=asset_type2, key=self.key)

        asset1.get_data()
        asset2.get_data()

        df = pd.DataFrame()
        df['A'] = asset1.df['Close']
        df['B'] = asset2.df['Close']

        print(df.corr())

    def check_watchlist(self):
        """Do magic"""

        results = list()
        for item in self.watchdata:

            symbol, entry_price, limit = configs.alphaconf.get_symbol(item)

            print()
            print(symbol)

            if symbol == 'TCS':
                continue

            asset = libs.assets.ASSET(symbol=symbol, source=self.source, asset_type=self.asset_type, key=self.key,
                                      min_goal=self.min_goal, atr_multiplier=self.atr_multiplier, cacheage=3600*24*3)

            # Fetch data from the source
            asset.get_data()

            # Perform static analysis
            asset.static_analysis(printoutput=True)
            if asset.stoploss <= 0:
                asset.stoploss = asset.lastprice * 0.5

            # print(asset.df)
            # exit()

            # Calculate chances
            asset.get_bust_chance(bust=asset.stoplosspercent, sims=10000, goal=self.min_goal)
            print('Bust chance:', round(asset.bust_chance, 2))
            print('Goal chance:', round(asset.goal_chance, 2))

            # Reward-risk ratio
            if asset.goal_chance > self.accepted_goal_chance:
                asset.get_reward_risk_ratio()
                print('Reward-Risk ratio:', asset.rewardriskratio)

            if asset.anomalies > 0 and self.plot_anomaly:
                print('Anomaly detected')
                asset.plot('Anomaly:')

            # Can we sell something?
            if asset.lastprice > entry_price > 0:
                income = round((asset.lastprice / entry_price - 1) * 100, 2)
                if income > self.min_goal*100:
                    self.tosell[symbol] = str(income) + '%'
                    print('Time to sell, income:', str(income) + '%')
                    asset.plot('Sell:')

            # Filter out too risky stuff
            if asset.rewardriskratio >= self.min_RewardRiskRatio and asset.goal_chance > self.accepted_goal_chance:
                results.append(asset.get_results())

                # Ignore too expensive stuff
                if asset.lastprice > limit > 0:
                    continue
                else:
                    asset.plot('Buy:')

        print('Results:')
        pprint(results)

        # Save results
        today = datetime.today()
        filename = self.source + '-' + str(today.strftime("%Y-%m-%d")) + '.json'
        filepath = os.path.join('', 'recomendations', filename)
        with open(filepath, 'w') as outfile:
            json.dump(results, outfile, indent=4)


if __name__ == "__main__":
    if "PYCHARM_HOSTED" in os.environ:
        adv = ADVISOR(datatype='me', plot_anomaly=False)
        # fire.Fire(adv.check_watchlist)
        fire.Fire(adv.correlation)
    else:
        fire.Fire(ADVISOR)
