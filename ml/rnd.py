"""
R&D
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
# import tensorflow as tf
import configs.alphaconf
import libs.stockslib as sl
import libs.technical_indicators as ti
from pprint import pprint
import pandas as pd


#res = sl.RESOURCE(symbol='INTC')
res = sl.RESOURCE(symbol='MSFT')
res.get_prices_from_alpha(key=configs.alphaconf.key)
res.get_history_from_alpha(key=configs.alphaconf.key)
res.fix_alpha_columns()
res.fix_alpha_history_columns()

####

df = res.history
df = df.reset_index()

n = 14
MAX = pd.Series(df['Close'].iloc[::-1].rolling(window=90).max(), name='MAX')

# df = ti.moving_average(df, n)
# df = ti.exponential_moving_average(df, n)
# df['dist'] = 100 * (df['Close'] - df['SMA']) / df['SMA']
# df = ti.average_true_range(df, n)
df = ti.rsi(df, n)
df['over'] = df['RSI'] < 50

df = df.drop(axis=1, columns='date')
df = df.join(MAX[::-1])
df = df.dropna()
df = df.reset_index()
df = df.drop(axis=1, columns='index')

df['profit'] = 100 * (df['MAX'] - df['Close']) / df['Close']

df['result'] = df['profit'] > 9

df.pop('MAX')
df.pop('Open')
df.pop('High')
df.pop('Low')
df.pop('5. adjusted close')
df.pop('6. volume')
df.pop('7. dividend amount')
df.pop('8. split coefficient')

pprint(df.tail(10))
print()
print('Correlation:', round(df['profit'].corr(df['RSI']), 2))
print('Correlation:', round(df['result'].corr(df['over']), 2))

# p = 107.56
# sma20 = 107.7155
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
