"""Working with Moex Brent
https://www.moex.com/ru/contract.aspx?code=Si-12.18
https://www.moex.com/ru/derivatives/
https://www.moex.com/ru/derivatives/contracts.aspx
"""

import time
import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd
import matplotlib.pyplot as plt
import libs.futures

symbol = 'BRZ8'
futures = libs.futures.FUTURES(symbol=symbol)
futures.get_data_from_moex(cachedir=os.path.join('..', 'cache-m'))
# futures.plot()

futures.get_atr(period=14)

futures.df['Diff'] = futures.df['High'] - futures.df['Low']
futures.df.pop('Open')
futures.df.pop('High')
futures.df.pop('Low')
futures.df.pop('Openpositionsvalue')

print(futures.df.corr())

print(futures.df.tail(10))



# symbol = 'SiZ8'
# futures = libs.futures.FUTURES(symbol=symbol)
# futures.get_data_from_moex(cachedir=os.path.join('..', 'cache-m'))
# futures.plot()
#
# df_si = futures.df
#
# print(df_si.tail(10))
#
# print(df_si['Close'].corr(df_br['Close']))
# print(df_si['Volume'].corr(df_br['Volume']))




