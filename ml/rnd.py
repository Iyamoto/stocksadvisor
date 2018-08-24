"""
R&D
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import tensorflow as tf
import configs.alphaconf
import libs.stockslib as sl
import libs.technical_indicators as ti
from pprint import pprint
import pandas as pd

p = 107.56
sma20 = 107.7155

res = sl.RESOURCE(symbol='INTC')
res.get_prices_from_alpha(key=configs.alphaconf.key)

####

df = res.prices
df = df.rename(index=str, columns={'3. low': 'Low'})
df = df.rename(index=str, columns={'2. high': 'High'})
df = df.rename(index=str, columns={'1. open': 'Open'})
df = df.rename(index=str, columns={'4. close': 'Close'})

df = df.reset_index()

df = df.drop(axis=1, columns='date')
df = df.drop(axis=1, columns='Open')
df = df.drop(axis=1, columns='Close')
df = df.drop(axis=1, columns='8. split coefficient')
df = df.drop(axis=1, columns='7. dividend amount')
df = df.drop(axis=1, columns='6. volume')
df = df.drop(axis=1, columns='5. adjusted close')

df = ti.rsi(df, 5)

pprint(df)

# pricedata = res.prices['4. close']
# MA = pd.Series(df['4. close'].rolling(window=20).mean(), name='SMA')
# MAX = pd.Series(df['4. close'].iloc[::-1].rolling(window=30).max(), name='MAX')
#
# df = df.drop(axis=1, columns='date')
# df = df.join(MA)
# df = df.join(MAX[::-1])
# df = df.dropna()
# df = df.rename(index=str, columns={'4. close': 'close'})
# df = df.reset_index()
# df = df.drop(axis=1, columns='index')
# df['dist'] = 100 * (df['SMA'] - df['close']) / df['close']
# df['diff'] = 100 * (df['MAX'] - df['close']) / df['close']
# df['flag'] = abs(df['dist']) < 1.5
# df['result'] = df['diff'] > 5
#
# df.pop('SMA')
# df.pop('MAX')
# df.pop('diff')

# pprint(df[df.flag])


#
# x = tf.constant(p, name='input')
# w = tf.Variable(0.5, name='weight')
# y = tf.mul(w, x, name='output')
# y_ = tf.constant(0.0, name='correct_value')
# loss = tf.pow(y - y_, 2, name='loss')
# train_step = tf.train.GradientDescentOptimizer(0.025).minimize(loss)
#
# for value in [x, w, y, y_, loss]:
#     tf.scalar_summary(value.op.name, value)
#
# summaries = tf.merge_all_summaries()
#
# sess = tf.Session()
# summary_writer = tf.train.SummaryWriter('log_simple_stats', sess.graph)
#
# sess.run(tf.initialize_all_variables())
# for i in range(100):
#     summary_writer.add_summary(sess.run(summaries), i)
#     sess.run(train_step)
