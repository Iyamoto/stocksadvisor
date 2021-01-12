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
        self.min_RewardRiskRatio = 5
        self.atr_multiplier = 1
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
        if datatype == 'meusd':
            watchdata = configs.alphaconf.symbols_meusd
            source = 'moex'
            asset_type = 'etfusd'
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
                    datatype2='me', symbol2='FXRU', extended=False):
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
        if extended:
            return correlation, df
        else:
            return correlation

    def check_watchlist(self, symbol_overide='', ignore=None):
        """Do magic"""

        for item in self.watchdata:

            symbol, entry_price, limit, dividend, desc, fair_price, average_score = configs.alphaconf.get_symbol(item)

            if symbol_overide:
                if symbol != symbol_overide:
                    continue

            if symbol in ignore:
                continue

            print()
            print(symbol, ' - ', desc)

            asset = libs.assets.ASSET(symbol=symbol, source=self.source, asset_type=self.asset_type, key=self.key,
                                      min_goal=self.min_goal, atr_multiplier=self.atr_multiplier, cacheage=3600*23)

            # Fetch data from the source
            asset.get_data()

            # Perform static analysis
            asset.static_analysis(printoutput=False)
            if asset.stoploss <= 0:
                asset.stoploss = asset.lastprice * 0.5

            pd.options.display.max_rows = 200

            # # Check 10% theory
            # asset.df['PCT'] = asset.df['Close'].pct_change().fillna(0)
            # asset.df['PCT10'] = asset.df['PCT'] > 0.1
            #
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

            # Find anomalies
            # if asset.anomalies > 0 and self.plot_anomaly:
            #     print('Anomaly detected')
            #     asset.plot('Anomaly:')

            # Find fous pattern

            asset.find_phase1(points=3, diff=1.5, rsi=50)

            # if symbol_overide:
            #     asset.plot('Manual:')

            # asset.find_event(points=3, diff=1.5)
            price_distance = 0.03
            gain_chance = 0.2
            loss_chance = 0.2

            if 'Max' not in asset.df.columns or asset.phase1_len < 1:
                continue

            if asset.df.Max.sum() > 0 and \
                    asset.df.Max[abs(asset.df.Max - asset.lastprice)/asset.df.Max <= price_distance].sum() > 0:
                event_index = asset.df.Max[abs(asset.df.Max - asset.lastprice)/asset.df.Max <= price_distance][-1:].index.values[0]
                taillen = len(asset.df) - event_index
                if 3 <= taillen <= 50:
                    trend = asset.get_trendline(asset.df['Close'].tail(taillen))
                    angle = trend[0]
                    if angle > 0:
                        print('Last price:', asset.lastprice)
                        print('Fair price based on divs:', asset.get_fair_price(dividend=dividend))
                        print('Fair price based on experts estimates:', fair_price)
                        print('StopLoss1 (EMA13 based):', asset.get_lastema13())
                        print('StopLoss2 (ATR based):', asset.stoploss)
                        if asset.lastprice > asset.lastema50:
                            print('Price is above EMA50')
                        if asset.lastprice > asset.lastema100:
                            print('Price is above EMA100')

                        if abs(asset.lastprice - asset.breakout_level)/asset.breakout_level <= price_distance:
                            print('Price is close to the breakout level!')
                            print('Breakout level:', asset.breakout_level)
                            print()

                            print('Positive signals')

                            asset.compare_volumes(days=taillen)
                            if asset.is_under_accumulation:
                                print('For the last {} days the stock is under accumulation:'.format(taillen), asset.is_under_accumulation)
                                gain_chance += 0.05
                            if 50 < asset.lastrsi < 70:
                                print('RSI shows upside momentum: {}'.format(asset.lastrsi))
                                gain_chance += 0.05
                            if asset.lastrsi < 30:
                                print('Oversold according to RSI:', asset.lastrsi)
                                gain_chance += 0.1
                            if average_score > 5:
                                print('The company average score > 5', average_score)
                                gain_chance += abs(average_score - 5) / 20
                            if asset.lastmfi < 20:
                                print('Oversold according to MFI:', asset.lastmfi)
                                gain_chance += 0.1
                            if asset.trend in ['Sideways Up', 'Up Up']:
                                print('Trend is up:', asset.trend)
                                gain_chance += 0.1

                            print()
                            print('Risks')

                            if not asset.is_under_accumulation:
                                print('For the last {} days the stock is not under accumulation:'.format(taillen), asset.is_under_accumulation)
                                loss_chance += 0.05
                            if 30 < asset.lastrsi < 50:
                                print('RSI shows downside momentum: {}'.format(asset.lastrsi))
                                loss_chance += 0.05
                            if asset.lastrsi > 70:
                                print('Overbought according to RSI:', asset.lastrsi)
                                loss_chance += 0.1
                            if average_score < 5:
                                print('The company average score < 5', average_score)
                                loss_chance += abs(average_score - 5) / 20
                            if asset.lastmfi > 80:
                                print('Overbought according to MFI:', asset.lastmfi)
                                loss_chance += 0.1
                            if asset.trend in ['Sideways Down', 'Up Down']:
                                print('Trend is down:', asset.trend)
                                loss_chance += 0.1

                            if fair_price > 0:
                                if 0 < fair_price <= asset.lastprice:
                                    continue
                                gain = (fair_price - asset.lastprice) * gain_chance
                                loss1 = (asset.lastprice - asset.get_lastema13()) * loss_chance
                                loss2 = (asset.lastprice - asset.stoploss) * loss_chance
                                rrr1 = round(gain / loss1, 1)
                                rrr2 = round(gain / loss2, 1)
                                print()
                                print('Reward/Risk ratio:', rrr1, rrr2)

                            print()
                            print('Please read recent news https://seekingalpha.com/symbol/{}'.format(symbol))
                            print('Check short interest')
                            print('Check money flow index for divergences')
                            print(
                                'Please check dividend pay date https://seekingalpha.com/symbol/{}/dividends/news'.format(
                                    symbol))
                            print('Please check earnings report date (Jan, April, July, Oct)')
                            print('Check growth estimates https://seekingalpha.com/symbol/{}/growth'.format(symbol))
                            print('Check FFV = Avg F EPS * F P/E (industry)')
                            print('Sector PE https://seekingalpha.com/symbol/{}/valuation/metrics'.format(symbol))
                            print(
                                'Earnings https://seekingalpha.com/symbol/{}/earnings/estimates#figure_type=annual'.format(
                                    symbol))
                            print('Are insiders buying or selling? https://www.gurufocus.com/stock/{}/insider'.format(
                                symbol))
                            print('Check the stock on https://www.morningstar.com/ read news')
                            print('Check Consensus Forward P/E, Debt/Equity, Net Margin, ROE, Free Cash Flow')
                            print('Anomalies:', asset.anomalies)
                            print()

                            # print('Monte-Carlo')
                            # asset.get_bust_chance(bust=asset.stoplosspercent, sims=10000, plot=False, taillen=taillen)
                            # asset.get_bust_chance(bust=price_distance, sims=1000, plot=False, taillen=taillen)
                            # print('Stop loss chance:', round(asset.bust_chance, 2))
                            # print('Stop loss price:', round(asset.breakout_level, 2))
                            # print('Take profit chance:', round(asset.goal_chance, 2))
                            # asset.goalprice = asset.lastprice * 1.1
                            # print('Take profit price:', round(asset.goalprice, 2))
                            # asset.get_reward_risk_ratio()
                            # print('Reward-Risk ratio:', asset.rewardriskratio)

                            asset.plot('Turbo:')

        # # Save results
        # today = datetime.today()
        # filename = self.datatype + '-' + self.source + '-' + str(today.strftime("%Y-%m-%d")) + '.json'
        # filepath = os.path.join('', 'recommendations', filename)
        # if len(results) > 0:
        #     with open(filepath, 'w') as outfile:
        #         json.dump(results, outfile, indent=4)


if __name__ == "__main__":
    if "PYCHARM_HOSTED" in os.environ:
        datatypes = ['a', 'mc', 'me', 'meusd', 'ms']
        # Ignore until February
        ignore = ['SBUX', 'MDT', 'AVGO', 'ZTS', 'ROP', 'V', 'ANTM', 'SYY']
        for datatype in datatypes:
            adv = ADVISOR(datatype=datatype)
            adv.check_watchlist(ignore=ignore)

        # fire.Fire(adv.correlation(datatype2='ms', symbol2='SBER'))
        # fire.Fire(adv.test_strategy)
    else:
        fire.Fire(ADVISOR)
