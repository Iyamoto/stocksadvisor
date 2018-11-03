"""Working with Moex USD
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

symbol = 'USD000UTSTOM'
futures = libs.futures.FUTURES(symbol=symbol, boardid='CETS', volumefield='VOLRUR')
futures.get_data_from_moex(cachedir=os.path.join('..', 'cache-m'))
# futures.plot()
df_usd = futures.df
print(df_usd.tail(10))

symbol = 'SiZ8'
futures = libs.futures.FUTURES(symbol=symbol)
futures.get_data_from_moex(cachedir=os.path.join('..', 'cache-m'))
df_si = futures.df

print(df_si.tail(10))

print(df_si['Close'].corr(df_usd['Close']))
print(df_si['Volume'].corr(df_usd['Volume']))
