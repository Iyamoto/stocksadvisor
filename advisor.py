"""
Stocks Advisor
"""

import configs.alphaconf
import libs.stockslib as sl
import fire
import json


class ADVISOR(object):
    """Stocks Advisor"""

    def __init__(self):
        self.key = configs.alphaconf.key
        self.watchdata = configs.alphaconf.symbols

        self.tobuy = dict()
        self.tosell = dict()

        self.incomelimit = 5
        self.luck = 0.3

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
            res.get_prices_from_alpha(key=self.key, cacheage=3600*6)
            res.fix_alpha_columns()

            # res.get_history_from_alpha(key=self.key)
            # res.fix_alpha_history_columns()

            lastprice = res.get_last_price()

            buy = 0

            # FB Prophet
            # if res.get_prophet_prediction() > 30:
            #     buy += 1

            # Calculate strategies
            for strategy_name in configs.alphaconf.ratios.keys():
                weight = configs.alphaconf.ratios[strategy_name][symbol]
                strategy_method = getattr(res, strategy_name)
                buy += weight * strategy_method()

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
    adv = ADVISOR()
    fire.Fire(adv.check_watchlist)
