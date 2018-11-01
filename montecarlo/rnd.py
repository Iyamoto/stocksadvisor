""" Undestanding Monte-Carlo
https://pythonprogramming.net/monte-carlo-simulator-python/
https://pypi.org/project/pandas-montecarlo/
"""

import random
import matplotlib.pyplot as plt


# let us go ahead and change this to return a simple win/loss
def rollDice():
    roll = random.randint(1, 100)

    if roll == 100:
        print(roll, 'roll was 100, you lose. What are the odds?! Play again!')
        return False
    elif roll <= 50:
        print(roll, 'roll was 1-50, you lose.')
        return False
    elif 100 > roll >= 50:
        print(roll, 'roll was 51-99, you win! *pretty lights flash* (play more!)')
        return True


def simple_bettor(funds, initial_wager, wager_count):
    value = funds
    wager = initial_wager

    # wager X
    wX = []

    # value Y
    vY = []

    # change to 1, to avoid confusion so we start @ wager 1
    # instead of wager 0 and end at 100.
    currentWager = 1

    #           change this to, less or equal.
    while currentWager <= wager_count:
        if rollDice():
            value += wager
            # append #
            wX.append(currentWager)
            vY.append(value)

        else:
            value -= wager
            # append #
            wX.append(currentWager)
            vY.append(value)

        currentWager += 1

    # print 'Funds:', value

    plt.plot(wX, vY)


x = 0

while x < 10000:
    simple_bettor(10000,100,1000)
    x += 1

plt.ylabel('Account Value')
plt.xlabel('Wager Count')
plt.show()
