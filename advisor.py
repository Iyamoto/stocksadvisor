"""
Stocks Advisor
"""

import configs.alphaconf
import libs.stockslib as sl
import fire
import json
import os
from pprint import pprint


class ADVISOR(object):
    """Stocks Advisor"""

    def __init__(self, datatype='m'):
        self.key = configs.alphaconf.key

        self.datatype = datatype

        if self.datatype == 'm':
            self.watchdata = configs.alphaconf.symbols_m
        else:
            self.watchdata = configs.alphaconf.symbols

        self.tobuy = dict()
        self.tosell = dict()

        self.incomelimit = 5
        self.luck = 0.2

    def check_watchlist(self):
        """Checks indicators"""

        for item in self.watchdata:

            # Parse watchlist
            if type(item) == dict:
                price = list(item.values())[0]
                symbol = list(item.keys())[0]
            else:
                symbol = item
                price = 0

            # print(symbol)

            # Init
            res = sl.RESOURCE(symbol=symbol, price_header='Close')
            if self.datatype == 'm':
                res.prices = res.get_prices_from_moex(cacheage=3600*24, days=200, cachedir=os.path.join('cache-m'))
                res.prices = res.prices.tail(200)
            else:
                res.get_prices_from_alpha(key=self.key, cacheage=3600*6)
                res.fix_alpha_columns()

                # res.get_history_from_alpha(key=self.key)
                # res.fix_alpha_history_columns()

            lastprice = res.get_last_price()

            buy = 0

            # FB Prophet
            # if res.get_prophet_prediction() > 30:
            #     buy += 1

            # Check for anomaly
            res.is_anomaly()

            # Calculate strategies
            for strategy_name in configs.alphaconf.ratios.keys():
                if self.datatype == 'm':
                    weight = configs.alphaconf.ratios_m[strategy_name][symbol]
                else:
                    weight = configs.alphaconf.ratios[strategy_name][symbol]
                strategy_method = getattr(res, strategy_name)
                try:
                    rez = strategy_method()
                except:
                    print(symbol, 'failed', strategy_method)
                    rez = 0
                if rez > 0:
                    buy += weight * rez
                else:
                    buy += rez

            if buy > self.luck * len(configs.alphaconf.ratios.keys()):
                res.buy = buy
                self.tobuy[symbol] = [buy, lastprice, res.msg]

            if lastprice > price > 0:
                income = round((lastprice / price - 1) * 100, 1)
                if income > self.incomelimit:
                    self.tosell[symbol] = [buy, income, res.msg]

        print('BUY:')
        print(json.dumps(self.tobuy, indent=4))
        print('SELL:')
        print(json.dumps(self.tosell, indent=4))


if __name__ == "__main__":
    adv = ADVISOR(datatype='a')
    fire.Fire(adv.check_watchlist)
