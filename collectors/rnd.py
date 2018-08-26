"""
R&D
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd

filename = 'ListingSecurityList.csv'
filepath = os.path.join('..', 'data', filename)
data = pd.read_csv(filepath, index_col='date')
