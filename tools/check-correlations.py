"""
Check correlations between ETFs
https://www.moex.com/s221
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd
import advisor

if __name__ == "__main__":

    adv = advisor.ADVISOR(datatype='me', plot_anomaly=False)

    # # Portfolio FX-Kub
    # etfs = [
    #     'FXRL',
    #     'FXUS',
    #     'FXRU',
    #     'FXGD',
    #     'FXTB'
    # ]

    # Portfolio Sber
    etfs = [
        'SBMX',
        'SBSP',
        'SBGB',
        'SBCB',
    ]

    data = dict()
    data['USD/RUB'] = list()
    data['Name'] = list()
    for etf0 in etfs:
        data['Name'].append(etf0)
        data[etf0] = list()

        for etf1 in etfs:
            rez = round(adv.correlation(datatype1='me', symbol1=etf0, datatype2='me', symbol2=etf1), 1)
            data[etf0].append(rez)

        # USD/RUB correlation
        rez = round(adv.correlation(datatype1='me', symbol1=etf0, datatype2='mc', symbol2='USD000UTSTOM'), 1)
        data['USD/RUB'].append(rez)

    df = pd.DataFrame(data)
    print(df)
