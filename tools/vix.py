"""
Get VIX
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import requests
from bs4 import BeautifulSoup
import logging
from influxdb import InfluxDBClient
import configs.influx


def get_vix():
    url = 'http://www.cboe.com/vix/'
    r = requests.get(url)
    if not r.ok:
        logging.error('Can not fetch VIX')
        return None
    html = r.text
    soup = BeautifulSoup(html, 'lxml')
    divs = soup.find_all('div')
    count = 0
    vix = None
    for div in divs:
        if div.text == '^VIX':
            vix = float(divs[count+1].text)
            break
        count += 1
    return vix


if __name__ == "__main__":
    influx_client = InfluxDBClient(
        configs.influx.HOST,
        configs.influx.PORT,
        configs.influx.DBUSER,
        configs.influx.DBPWD,
        configs.influx.DBNAME,
        timeout=5
    )

    vix = get_vix()
    print(vix)
    if vix:
        json_body = [
            {
                "measurement": "vix",
                "fields": {
                    "value": vix,
                }
            }
        ]
        influx_client.write_points(json_body)
