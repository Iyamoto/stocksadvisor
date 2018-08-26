import unittest
import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd
import libs.stockslib as sl


class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.symbol = 'MSFT'
        self.res = sl.RESOURCE(symbol=self.symbol)
        self.res.prices = pd.read_csv(self.symbol + '.csv', index_col='date')
        self.res.fix_alpha_columns()

        self.diff = 0.001

        # https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=MSFT&apikey=demo
        self.close = 107.56

        # https://www.alphavantage.co/query?function=SMA&symbol=MSFT&interval=daily&time_period=20&series_type=close&apikey=demo
        self.sma20 = 107.7155
        self.sma50 = 104.6306
        self.sma100 = 100.5726
        self.sma200 = 94.6567

        self.ema5 = 107.2376
        self.ema20 = 107.2890
        self.ema50 = 105.0039
        self.ema100 = 101.2824
        self.ema200 = 94.9310

        # https://www.alphavantage.co/query?function=MACD&symbol=MSFT&interval=daily&series_type=close&apikey=demo
        self.macd = {
            "macd_diff": -0.4259,
            "macd_signal": 1.0264,
            "macd": 0.6005
        }

        # https://www.alphavantage.co/query?function=RSI&symbol=MSFT&interval=daily&time_period=5&series_type=close&apikey=demo
        self.rsi5 = 51.9310
        self.rsi14 = 53.2641
        self.rsi3 = 61.1924

    def test_get_last_price(self):
        self.assertEqual(self.res.get_last_price(), self.close)

    def test_get_sma_last(self):
        self.assertLessEqual(abs(self.res.get_sma_last(period=20) - self.sma20), self.diff)
        self.assertLessEqual(abs(self.res.get_sma_last(period=50) - self.sma50), self.diff)
        self.assertLessEqual(abs(self.res.get_sma_last(period=100) - self.sma100), self.diff)

    def test_get_ema_last(self):
        self.assertLessEqual(abs(self.res.get_ema_last(period=5) - self.ema5), self.diff)
        self.assertLessEqual(abs(self.res.get_ema_last(period=20) - self.ema20), self.diff)
        self.assertLessEqual(abs(self.res.get_ema_last(period=50) - self.ema50), self.diff*100)
        self.assertLessEqual(abs(self.res.get_ema_last(period=100) - self.ema100), self.diff*1000)


if __name__ == '__main__':
    unittest.main()
