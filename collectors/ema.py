"""Collect EMA 200"""


import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import datetime
import time
import logging
import fire
import requests
from influxdb import InfluxDBClient
import configs.alphaconf
import configs.influx
import configs.fxit


def get_ema200(symbol, age=23*3600):

    influx_client = InfluxDBClient(
        configs.influx.HOST,
        configs.influx.PORT,
        configs.influx.DBUSER,
        configs.influx.DBPWD,
        configs.influx.DBNAME,
        timeout=5
    )
    query = 'SELECT last("ema200") FROM "data" WHERE ("symbol"=~ /^' + symbol + '$/)'
    result = influx_client.query(query)
    ema200_date = result.raw['series'][0]['values'][0][0]
    tmp = ema200_date.split('.')
    ema200_date = tmp[0]
    ema200_date = datetime.datetime.strptime(ema200_date, '%Y-%m-%dT%H:%M:%S')
    now = datetime.datetime.utcnow()
    diff = now - ema200_date
    if diff.total_seconds() < age:
        ema200 = result.raw['series'][0]['values'][0][1]
    else:
        ema200 = None
    return ema200


def get_price(symbol, age=23*3600):

    influx_client = InfluxDBClient(
        configs.influx.HOST,
        configs.influx.PORT,
        configs.influx.DBUSER,
        configs.influx.DBPWD,
        configs.influx.DBNAME,
        timeout=5
    )

    # influx_client.drop_measurement('data')
    # exit()

    query = 'SELECT last("price") FROM "data" WHERE ("symbol"=~ /^' + symbol + '$/)'
    result = influx_client.query(query)
    price_date = result.raw['series'][0]['values'][0][0]
    tmp = price_date.split('.')
    price_date = tmp[0]
    price_date = datetime.datetime.strptime(price_date, '%Y-%m-%dT%H:%M:%S')
    now = datetime.datetime.utcnow()
    diff = now - price_date
    if diff.total_seconds() < age:
        price = result.raw['series'][0]['values'][0][1]
    else:
        price = None

    query = 'SELECT last("change_percent") FROM "data" WHERE ("symbol"=~ /^' + symbol + '$/)'
    result = influx_client.query(query)
    change_percent = result.raw['series'][0]['values'][0][1]

    return price, change_percent


def fetch_ema200_alpha(symbol, key=configs.alphaconf.key):
    url = 'https://www.alphavantage.co/query?function=' + \
          'EMA&symbol={}&interval=daily&time_period=200&series_type=close&apikey={}'.format(symbol, key)
    retry = 0

    # Check cache
    try:
        ema200 = get_ema200(symbol)
    except:
        ema200 = None

    if ema200:
        logging.info(symbol + ' Got EMA200 from InfluxDB: ' + str(ema200))
    else:
        # Try to fetch from the WEB
        while True:
            try:
                r = requests.get(url=url, timeout=5)
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
                logging.info(symbol + ' retry ' + str(retry))
                time.sleep(retry*5)
                continue

    return ema200


def fetch_price_alpha(symbol, key=configs.alphaconf.key):
    url = 'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={}&apikey={}'.format(symbol, key)
    retry = 0

    # Check cache
    try:
        price = get_price(symbol)
    except:
        price = None

    if price:
        logging.info(symbol + ' Got price from InfluxDB: ' + str(price))
    else:
        # Try to fetch from the WEB
        while True:
            try:
                r = requests.get(url=url, timeout=5)
                data = r.json()
                price = float(data['Global Quote']['05. price'])
                change_percent = data['Global Quote']['10. change percent']
                change_percent = float(change_percent.strip('%'))
                if price:
                    break
            except:
                retry += 1
                if retry > 10:
                    logging.error('Can not fetch ' + symbol)
                    logging.error(url)
                    break
                logging.info(symbol + ' retry ' + str(retry))
                time.sleep(retry*5)
                continue

    return price, change_percent


def fetch(write_to_influx=True, datatype='fxit'):
    if write_to_influx:
        influx_client = InfluxDBClient(
            configs.influx.HOST,
            configs.influx.PORT,
            configs.influx.DBUSER,
            configs.influx.DBPWD,
            configs.influx.DBNAME,
            timeout=5
        )

    if datatype == 'fxit':
        symbols = configs.fxit.holdings
    if datatype == 'portfolio':
        symbols = configs.alphaconf.symbols

    for symbol in symbols:
        if datatype == 'portfolio':
            symbol = list(symbol.keys())[0]

        price, change_percent = fetch_price_alpha(symbol)
        logging.info(symbol + ' price: ' + str(price))
        ema200 = fetch_ema200_alpha(symbol)
        logging.info(symbol + ' ema200: ' + str(ema200))

        if type(ema200) != float:
            logging.error(symbol + ' ema200 ' + str(ema200) + ' not float')
            continue

        if type(price) != float:
            logging.error(symbol + ' price ' + str(price) + ' not float')
            continue

        ema_distance = round(100 * (price - ema200) / ema200, 2)

        if symbol in configs.fxit.holdings:
            symbol_type = 'FXIT'
        else:
            symbol_type = 'Portfolio'

        if write_to_influx:
            json_body = [
                {
                    "measurement": "data",
                    "tags": {
                        "symbol": symbol,
                        "symbol_type": symbol_type,
                    },
                    "fields": {
                        "price": price,
                        "ema200": ema200,
                        "ema_distance": ema_distance,
                        "change_percent": change_percent,
                    }
                }
            ]
            influx_client.write_points(json_body)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)-15s %(levelname)s %(message)s',
                        level='INFO',
                        stream=sys.stderr)
    if "PYCHARM_HOSTED" in os.environ:
        # print(fetch_price_alpha('MSFT'))
        fetch(write_to_influx=False)
    else:
        fire.Fire()

