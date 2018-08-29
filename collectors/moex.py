"""
R&D moex
https://iss.moex.com/iss/engines/stock/markets/shares/boards/
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd
from pprint import pprint

sybmol = 'GMKN'

filename = sybmol + '.csv'
filepath = os.path.join('..', 'cache-m', filename)

df = pd.read_csv(filepath)

# pprint(df.columns)
df = df.query('BOARDID == "TQBR"')

filtered = pd.DataFrame()
filtered['date'] = df['TRADEDATE']
filtered['Open'] = df['OPEN']
filtered['Low'] = df['LOW']
filtered['High'] = df['HIGH']
filtered['Close'] = df['CLOSE']
filtered['Volume'] = df['VOLUME']

pprint(filtered.head())

filepath = os.path.join('..', 'history-m', filename)
filtered.to_csv(filepath)
