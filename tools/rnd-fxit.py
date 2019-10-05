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
import advisor
import configs.fxit
import numpy as np


def calc_beta(df):
    np_array = df.values
    m = np_array[:, 0]  # market returns are column zero from numpy array
    s = np_array[:, 1]  # stock returns are column one from numpy array
    covariance = np.cov(s, m)  # Calculate covariance between stock and market
    beta = covariance[0, 1]/covariance[1, 1]
    return beta


if __name__ == "__main__":

    adv = advisor.ADVISOR(datatype='a', plot_anomaly=False)

    data = dict()
    data['Symbol'] = list()
    data['Correlation'] = list()
    data['Beta'] = list()

    for symbol in configs.fxit.holdings:

        correlation, df = adv.correlation(datatype1='me', symbol1='FXIT', datatype2='a', symbol2=symbol,
                                          extended=True)

        df_change = df.pct_change(1).dropna(axis=0)

        X = df_change['A']
        y = df_change['B']

        data['Symbol'].append(symbol)
        data['Correlation'].append(round(correlation, 2))
        data['Beta'].append(round(calc_beta(df_change), 2))

    df_rez = pd.DataFrame(data)
    print(df_rez.sort_values('Correlation'))
