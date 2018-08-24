"""
S-advisor
"""

import configs.alphaconf
import libs.stockslib as sl
import fire


class ADVISOR(object):
    """CLI S-Advisor"""

    def __init__(self):
        self.key = configs.alphaconf.key
        self.watchdata = configs.alphaconf.symbols

        self.tobuy = dict()
        self.tosell = dict()

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
            res.get_prices_from_alpha(key=self.key)
            res.fix_alpha_columns()
            # res.get_history_from_alpha(key=self.key)

            lastprice = res.get_last_price()

            buy = 0

            # buy += res.check_rsi_buy(period=3)
            # buy += res.check_rsi_buy(period=5)
            # buy += res.check_rsi_buy(period=14)

            buy += 0.22 * res.check_atr(period=20)
            buy += 0.11 * res.check_rsi2_buy(period=20)

            # buy += res.check_ema5_above_ema20()
            # buy += res.check_ema20_above_ema50()
            # buy += res.check_sma20_above_sma100()

            # buy += res.check_macd()

            if buy > 0:
                res.buy = buy
                self.tobuy[symbol] = [buy, lastprice, res.msg]

            if lastprice > price > 0 and (price/lastprice - 1)*100 > 5:
                sell = 0
                sell += res.check_rsi_sell(period=3)
                sell += res.check_rsi_sell(period=5)
                sell += res.check_rsi_sell(period=14)

                print('Sell advice', sell)
                income = (price / lastprice) * 100
                print('Income', income)

                if sell > 5:
                    self.tosell[symbol] = [sell, income]

        print('BUY:')
        print(self.tobuy)
        print('SELL:')
        print(self.tosell)

if __name__ == "__main__":
    adv = ADVISOR()
    fire.Fire(adv.check_watchlist)
