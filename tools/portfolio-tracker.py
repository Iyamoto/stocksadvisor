"""
Track portfolio performance
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd
import json
import advisor
import libs.portfolio


if __name__ == "__main__":

    portfolio = libs.portfolio.PORTFOLIO(name='SBER', money=100000)
    portfolio.add(symbol='FXIT', share=20)
    portfolio.add(symbol='SBSP', share=10)
    # portfolio.add(symbol='SBMX', share=20)
    # portfolio.add(symbol='SBGB', share=10)
    # portfolio.add(symbol='SBRB', share=10)
    portfolio.add(symbol='SBCB', share=10)
    portfolio.add(symbol='FXTB', share=10)
    portfolio.add(symbol='FXRU', share=10)

    print(portfolio.df.head(5))

    print(portfolio)
