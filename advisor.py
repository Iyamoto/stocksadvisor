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

        self.incomelimit = 9

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

            print(symbol)

            # Init
            res = sl.RESOURCE(symbol=symbol)
            res.get_prices_from_alpha(key=self.key, cacheage=3600*24*3)
            res.fix_alpha_columns()

            lastprice = res.get_last_price()

            buy = 0

            # FB Prophet
            # if res.get_prophet_prediction() > 30:
            #     buy += 1

            # EMA200 close to EMA50
            weight = configs.alphaconf.ema50_close_to_ema200_ratios[symbol]
            buy += weight * res.check_ema200_closeto_ema50()

            if buy > 0:
                res.buy = buy
                self.tobuy[symbol] = [buy, lastprice, res.msg]

            if lastprice > price > 0:
                income = round((lastprice / price - 1) * 100, 1)
                if income > self.incomelimit:
                    sell = 0
                    if sell >= 0:
                        self.tosell[symbol] = [sell, income]

        print('BUY:')
        print(json.dumps(self.tobuy, indent=4))
        print('SELL:')
        print(self.tosell)


if __name__ == "__main__":
    adv = ADVISOR()
    fire.Fire(adv.check_watchlist)
