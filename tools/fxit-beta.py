"""
Research FXIT

Beta Interpretation
0 indicates no correlation with the chosen benchmark (e.g. NASDAQ index )
1 indicates a stock has the same volatility as the market
>1 indicates a stock that’s more volatile than its benchmark
<1 is less volatile than the benchmark
1.5 is 50% more volatile than the benchmark

"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd
import configs.etf
import libs.assets
import configs.alphaconf
import numpy as np


def calc_beta(df):
    np_array = df.values
    m = np_array[:, 0]  # market returns are column zero from numpy array
    s = np_array[:, 1]  # stock returns are column one from numpy array
    covariance = np.cov(s, m)  # Calculate covariance between stock and market
    beta = covariance[0, 1]/covariance[1, 1]
    return beta


if __name__ == "__main__":

    # Transform FXIT to USD
    asset = libs.assets.ASSET(symbol='FXIT', source='moex', asset_type='etf', key=configs.alphaconf.key)
    asset.get_data()
    fxit_df = asset.df

    asset = libs.assets.ASSET(symbol='USD000UTSTOM', source='moex', asset_type='currency', key=configs.alphaconf.key)
    asset.get_data()
    usdrub_df = asset.df

    fxit_usd_df = pd.DataFrame()
    fxit_usd_df[['date', 'RUB']] = fxit_df[['date', 'Close']]
    fxit_usd_df['USD'] = round(fxit_usd_df['RUB'] / usdrub_df['Close'], 2)
    fxit_usd_df['Close'] = fxit_usd_df['USD'].fillna(method='ffill')

    # correlation = fxit_usd_df['RUB'].corr(fxit_usd_df['Close'])
    # print(correlation)

    fxit_usd_df.drop(['RUB', 'USD'], axis=1, inplace=True)

    data = dict()
    data['Symbol'] = list()
    data['Correlation'] = list()
    data['Beta'] = list()

    for symbol in configs.etf.XLK:

        # Calculate correlation
        asset = libs.assets.ASSET(symbol=symbol, source='alpha', asset_type='stock', key=configs.alphaconf.key)
        asset.get_data()

        df = pd.DataFrame()
        df['A'] = fxit_usd_df['Close'].copy()
        df['B'] = asset.df['Close'].copy()

        correlation = df['A'].corr(df['B'])

        # Calculate Beta

        df_change = df.pct_change(1).dropna(axis=0)

        X = df_change['A']
        y = df_change['B']

        data['Symbol'].append(symbol)
        data['Correlation'].append(round(correlation, 2))
        data['Beta'].append(round(calc_beta(df_change), 2))

    df_rez = pd.DataFrame(data)
    print(df_rez.sort_values('Correlation'))
