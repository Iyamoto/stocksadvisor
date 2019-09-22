"""
Track portfolio performance
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd
import libs.portfolio


if __name__ == "__main__":

    # portfolio = libs.portfolio.PORTFOLIO(name='SBER', money=100000)
    # portfolio.add(symbol='FXIT', share=30)
    # portfolio.add(symbol='SBSP', share=25)
    # portfolio.add(symbol='SBCB', share=15)
    # portfolio.add(symbol='FXTB', share=15)
    # portfolio.add(symbol='FXRU', share=15)

    portfolio = libs.portfolio.PORTFOLIO(name='Kubyshka', money=100000)
    portfolio.add(symbol='FXRL', share=25)
    portfolio.add(symbol='FXUS', share=25)
    portfolio.add(symbol='FXGD', share=25)
    portfolio.add(symbol='FXRU', share=25)

    portfolio.run()

    print(portfolio)

    print(portfolio.df.head(5))
    print(portfolio.df.tail(5))
