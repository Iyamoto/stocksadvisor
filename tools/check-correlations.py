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

    # Portfolio FX-Kub
    etfs = [
        'FXIT',  # +
        'FXUS',  # +
        'AKNX',  # + , Anti RUB devaluation
        'FXRL',  # +
        'FXCN',  # +
        'RUSE',  # +
        'FXRB',  # +
        'FXMM',  # +
        'FXRU',  # + , Anti RUB devaluation
        'FXGD',  # + , Anti RUB devaluation, or PLZL?
        'RUSB',  # + , Anti RUB devaluation
        'FXTB',  # + , Anti RUB devaluation
    ]

    # Portfolio Power-RUB
    stocks = [
        'SBER',
        'MSTT',
        'MRKV',
        'CHMF',
        'MAGN',
        'IRAO',
        'TRMK',
        'SJM'
    ]

    # # Portfolio Power-USD
    # stocks = [
    #     'PLZL',  # ?
    #     'VEON',
    #     'HD'
    # ]

    # # Portfolio Sber
    # etfs = [
    #     'FXIT',  # + 20%, 70
    #     'SBSP',  # 10%, 35
    #     'SBMX',  # 20%, vs SBRB
    #     'SBGB',  # 10%, vs SBRB
    #     'SBRB',  # 10%
    #     'SBCB',  # + 10%, Anti RUB devaluation
    #     'FXTB',  # + 10%, Anti RUB devaluation
    #     'FXRU'   # + 10%, Anti RUB devaluation
    # ]

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

    # print('MOEX', adv.correlation(datatype2='ms', symbol2='MOEX'))
    # print('SBER', adv.correlation(datatype2='ms', symbol2='SBER'))
    # print('MTSS', adv.correlation(datatype2='ms', symbol2='MTSS'))
