"""
R&D
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd
from pprint import pprint
import csv
from io import StringIO


filename = 'ListingSecurityList.csv'
filepath = os.path.join('..', 'data', filename)

data = ''

with open(filepath, newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=';')
    for row in spamreader:
        if row[4].startswith('Акции'):
            name = str(row[2]).encode("cp1251").decode('cp1251').encode('utf8')
            filtered = row[6] + ',' + row[11] + ',' + str(name.decode("utf-8"))
            data += filtered + '\n'

data = StringIO(data)
df = pd.read_csv(data, names=['Symbol', 'Currency', 'Name'])
pprint(df.query('Currency == "USD"').head(10))

filepath = os.path.join('..', 'data', 'spbex.csv')
df.to_csv(filepath)

filepath = os.path.join('..', 'data', 'spbex_usd.csv')
df.query('Currency == "USD"').to_csv(filepath)
