"""
R&D
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd
from pprint import pprint
import json


filename = 'spbex_usd.csv'
filepath = os.path.join('..', 'data', filename)

df_spb = pd.read_csv(filepath)
df_spb.pop('Unnamed: 0')

filename = 'spyd.csv'
filepath = os.path.join('..', 'data', filename)
df_spyd = pd.read_csv(filepath)

pprint(df_spyd.head(10))

df_spb['SPYD'] = df_spb['Symbol'].isin(df_spyd['Symbol'])

spb_spyd = df_spb[df_spb['SPYD']]
spb_spyd = spb_spyd.reset_index()
spb_spyd.pop('index')

pprint(spb_spyd.head(10))

filepath = os.path.join('..', 'data', 'spbex_spyd.csv')
spb_spyd.to_csv(filepath)
d = spb_spyd['Symbol'].values
print(len(d))

path = os.path.join('..', 'data', 'watchlist.json')
with open(path) as f:
     watchlist = json.load(f)

print(len(watchlist))

existing_symbols = list()
for item in watchlist:
    # Parse watchlist
    if type(item) == dict:
        price = list(item.values())[0]
        symbol = list(item.keys())[0]
    else:
        symbol = item
        price = 0

    existing_symbols.append(symbol)

for symbol in d:
    if symbol not in existing_symbols:
        watchlist.append(symbol)

print(len(watchlist))

with open(path, 'w') as outfile:
    json.dump(watchlist, outfile, indent=4)
