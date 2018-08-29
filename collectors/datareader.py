"""
R&D
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd
from pandas_datareader import data, wb

import pandas_datareader as pdr

symbol = 'GMKN'

stock = pdr.get_data_moex(symbol)
print(stock.head())

filepath = os.path.join('..', 'cache-m', symbol + '.csv')
stock.to_csv(filepath)

# import pandas_datareader.data as web
#
# f = web.DataReader('AFLT', 'moex', start='2018-08-01', end='2017-08-29')
# print(f.head())
