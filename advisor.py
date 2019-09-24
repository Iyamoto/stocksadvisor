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

    def __init__(self, datatype='m', plot_anomaly=False, caching=True):
        self.plot_anomaly = plot_anomaly
        self.datatype = datatype
        self.watchdata, self.source, self.asset_type = self.get_assettype(datatype=self.datatype)
        self.key = configs.alphaconf.key
        self.caching = caching

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

    def test_strategy(self):
        """ Test predictions"""
        watchdata, source, asset_type = self.get_assettype(datatype=self.datatype)

        # Get prediction dates
        prediction_dates = list()
        sep = '-'
        dirpath = os.path.join('', 'recommendations')
        for filename in os.listdir(dirpath):
            if filename.endswith('.json') and filename.startswith(self.datatype + '-' + source):
                items = filename.split(sep)
                prediction_date = items[2] + sep + items[3] + sep + items[4]
                prediction_date = prediction_date.strip('.json')
                prediction_dates.append(prediction_date)

        # print('Date', 'Status', 'Prediction_date', 'Delta', 'Symbol', 'Exit_price', 'Success_count', 'Max/Min')

        # Check predictions
        for prediction_date in prediction_dates:
            today = datetime.today().strftime("%Y-%m-%d")
            delta = datetime.today() - datetime.strptime(prediction_date, "%Y-%m-%d")
            filename = self.datatype + '-' + source + '-' + prediction_date + '.json'
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as infile:
                    data = json.load(infile)
            else:
                return

            for item in data:
                symbol = list(item.keys())[0]
                stop_loss = item[symbol]['stop_loss']
                exit_price = item[symbol]['exit_price']

                asset = libs.assets.ASSET(symbol=symbol, source=source, asset_type=asset_type, key=self.key,
                                          cacheage=3600*48, caching=self.caching)
                asset.get_data()

                df = pd.concat([asset.df['date'], asset.df['Close']], axis=1)
                df.date = pd.to_datetime(df['date'], format='%Y-%m-%d')
                df = df.set_index('date')

                filtered = df[prediction_date:].copy()

                filtered['Success'] = filtered.Close > exit_price
                if filtered['Success'].sum() > 0:
                    print(today + ' Succeeded', prediction_date, delta.days, symbol, exit_price, filtered['Success'].sum(),
                          filtered.Close.max())

                filtered['Bust'] = filtered.Close < stop_loss
                if filtered['Bust'].sum() > 0:
                    print(today + ' Busted', prediction_date, delta.days, symbol, stop_loss, filtered['Bust'].sum(),
                          filtered.Close.min())

    def correlation(self, datatype1='mc', symbol1='USD000UTSTOM',
                    datatype2='me', symbol2='FXRU'):
        watchdata1, source1, asset_type1 = self.get_assettype(datatype=datatype1)
        watchdata2, source2, asset_type2 = self.get_assettype(datatype=datatype2)

        asset1 = libs.assets.ASSET(symbol=symbol1, source=source1, asset_type=asset_type1,
                                   key=self.key, caching=self.caching)
        asset2 = libs.assets.ASSET(symbol=symbol2, source=source2, asset_type=asset_type2,
                                   key=self.key, caching=self.caching)

        asset1.get_data()
        asset2.get_data()

        df = pd.DataFrame()
        df['A'] = asset1.df['Close'].copy()
        df['B'] = asset2.df['Close'].copy()

        correlation = df['A'].corr(df['B'])
        return correlation

    def check_watchlist(self):
        """Do magic"""

        results = list()
        for item in self.watchdata:

            symbol, entry_price, limit, dividend = configs.alphaconf.get_symbol(item)

            print()
            print(symbol)

            if symbol == 'TCS':
                continue

            asset = libs.assets.ASSET(symbol=symbol, source=self.source, asset_type=self.asset_type, key=self.key,
                                      min_goal=self.min_goal, atr_multiplier=self.atr_multiplier, cacheage=3600*12)

            # Fetch data from the source
            asset.get_data()

            # Perform static analysis
            asset.static_analysis(printoutput=True)
            if asset.stoploss <= 0:
                asset.stoploss = asset.lastprice * 0.5

            # # Check 10% theory
            # asset.df['PCT'] = asset.df['Close'].pct_change().fillna(0)
            # asset.df['PCT10'] = asset.df['PCT'] > 0.1
            #
            # pd.options.display.max_rows = 200
            #
            # if asset.df['PCT10'].sum() > 1:
            #     print(asset.df['PCT10'].sum())
            #     print(asset.df[['PCT', 'PCT10']])
            # else:
            #     continue

            # usd_rub_correlation = round(self.correlation(datatype2=self.datatype, symbol2=symbol), 2)
            # print('USD-RUB-Correlation:', usd_rub_correlation)

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

            # Check EMA200
            if self.datatype == 'a':
                ema200 = asset.get_ema200_alpha(key=self.key)
                print('EMA200:', ema200)
                if ema200 and asset.lastprice > ema200:
                    ema200_diff = round(100 * (asset.lastprice - ema200) / asset.lastprice, 1)
                    print('Price above EMA200', ema200_diff, '%')

            # Can we sell something?
            if asset.lastprice > entry_price > 0:
                income = round((asset.lastprice / entry_price - 1) * 100, 2)
                if income > self.min_goal*100:
                    self.tosell[symbol] = str(income) + '%'
                    print('Time to sell, income:', str(income) + '%')
                    asset.plot('Sell:')

            asset.get_fair_price(dividend=dividend)
            print('Fair price:', asset.fairprice)
            print('USD/RUB Correlation:', round(self.correlation(datatype2=self.datatype, symbol2=symbol), 1))

            # Filter out too risky stuff
            if asset.rewardriskratio >= self.min_RewardRiskRatio and asset.goal_chance > self.accepted_goal_chance:
                results.append(asset.get_results())

                # Ignore too expensive stuff
                # if asset.fairprice > asset.lastprice:
                #     asset.plot('Cheap:')
                if limit == 0:
                    limit = asset.fairprice
                if asset.lastprice > limit > 0:
                    continue
                if entry_price > 0 and asset.lastprice > 0.9 * entry_price:
                    # We have the asset already
                    continue

                asset.plot('Buy:')

        print('Results:')
        pprint(results)

        # Save results
        today = datetime.today()
        filename = self.datatype + '-' + self.source + '-' + str(today.strftime("%Y-%m-%d")) + '.json'
        filepath = os.path.join('', 'recommendations', filename)
        if len(results) > 0:
            with open(filepath, 'w') as outfile:
                json.dump(results, outfile, indent=4)


if __name__ == "__main__":
    if "PYCHARM_HOSTED" in os.environ:
        adv = ADVISOR(datatype='a', plot_anomaly=False)
        adv.check_watchlist()

        # fire.Fire(adv.correlation(datatype2='ms', symbol2='SBER'))
        # fire.Fire(adv.test_strategy)
    else:
        fire.Fire(ADVISOR)
