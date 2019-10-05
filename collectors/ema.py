"""Collect EMA 200"""


import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import json
import time
import logging
import fire
import requests
from influxdb import InfluxDBClient
import configs.alphaconf
import configs.influx
import configs.fxit


def get_ema200(symbol):
    influx_client = InfluxDBClient(
        configs.influx.HOST,
        configs.influx.PORT,
        configs.influx.DBUSER,
        configs.influx.DBPWD,
        configs.influx.DBNAME,
        timeout=5
    )

    query = 'SELECT last("ema200") FROM "ema200" WHERE ("symbol"=~ /' + symbol + '/)'
    result = influx_client.query(query)
    ema200 = result['series'][0]['values'][1]
    return ema200


def fetch_ema200_alpha(symbol, key=configs.alphaconf.key):
    url = 'https://www.alphavantage.co/query?function=' + \
          'EMA&symbol={}&interval=daily&time_period=200&series_type=close&apikey={}'.format(symbol, key)
    retry = 0
    ema200 = None
    while True:
        try:
            r = requests.get(url=url)
            data = r.json()
            last = data['Meta Data']['3: Last Refreshed']
            ema200 = float(data['Technical Analysis: EMA'][last]['EMA'])
            if ema200:
                break
        except:
            retry += 1
            if retry > 10:
                logging.error('Can not fetch ' + symbol)
                logging.error(url)
                break
            time.sleep(retry)
            continue

    return ema200


def fetch_ema200_fxit(write_to_influx=True):
    if write_to_influx:
        influx_client = InfluxDBClient(
            configs.influx.HOST,
            configs.influx.PORT,
            configs.influx.DBUSER,
            configs.influx.DBPWD,
            configs.influx.DBNAME,
            timeout=5
        )

    symbols = configs.fxit.holdings
    for symbol in symbols:
        ema200 = fetch_ema200_alpha(symbol=symbol)
        logging.info(symbol + ' ' + str(ema200))
        if type(ema200) != float:
            logging.error(symbol + ' ' + str(ema200) + ' not float')
            continue

        if write_to_influx:
            json_body = [
                {
                    "measurement": "ema200",
                    "tags": {
                        "symbol": symbol,
                    },
                    "fields": {
                        "ema200": ema200,
                    }
                }
            ]
            influx_client.write_points(json_body)


if __name__ == "__main__":
    if "PYCHARM_HOSTED" in os.environ:
        fetch_ema200_fxit(write_to_influx=False)
    else:
        logging.basicConfig(format='%(asctime)-15s %(levelname)s %(message)s',
                            level='ERROR',
                            stream=sys.stderr)
        fire.Fire()

