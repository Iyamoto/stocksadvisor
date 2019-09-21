"""
Check correlations between ETFs
https://www.moex.com/s221
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import fire
import advisor

if __name__ == "__main__":

    adv = advisor.ADVISOR(datatype='me', plot_anomaly=False)
    etfs = [
        'FXRL',
        'FXUS',
        'FXRU',
        'FXGD'
    ]
    rez = adv.correlation(datatype1='me', symbol1='FXGD', datatype2='me', symbol2='FXRU')
    print(rez)

