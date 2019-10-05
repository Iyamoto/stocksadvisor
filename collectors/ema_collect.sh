#!/usr/bin/env bash

cd /home/alex/stocksadvisor/
/usr/bin/env git pull
cd /home/alex/stocksadvisor/collectors
/usr/bin/env python3 ema.py fetch_ema200_fxit
