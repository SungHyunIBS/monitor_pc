#!/opt/monitor/venv/bin/python
import sys
import time
import logging
from pathlib import Path
import json
import psutil
import os
from datetime import datetime
from influxdb_client import InfluxDBClient

logging.basicConfig(stream=sys.stdout, format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO)

SLOWDIR = '/opt/monitor'
model   = "PCInfo"

def read(devinfo):

    datapoint = {}

    # CPU, RAM, Storage usage
    cpu_usage       = psutil.cpu_percent(interval=1)
    ram_usage       = psutil.virtual_memory().percent
    disk_usage_root = psutil.disk_usage('/').percent
    disk_usage_home = psutil.disk_usage('/home').percent
    
    wdata = {
        'CPU'  : float(cpu_usage),
        'RAM'  : float(ram_usage),
        'DISKR': float(disk_usage_root),
        'DISKH': float(disk_usage_home),
    }

    tdata = {
        'dev'  : devinfo['dev'],
        'model': model,
        'pos'  : devinfo['pos'],
    }

    datapoint = {
        'measurement': 'system_metrics',
        'time'       : int(time.time()),
        'fields'     : wdata,
        'tags'       : tdata
    }

    return datapoint

def main():
    dev      = os.getenv('DEVICE_DEV', '')
    pos      = os.getenv('DEVICE_POS', '')
    dburl    = os.getenv('DB_URL',     '')
    dborg    = os.getenv('DB_ORG',     '')
    dbbucket = os.getenv('DB_BUCKET',  '')
    dbtoken  = os.getenv('DB_TOKEN',   '')
        
    devinfo = {
        'dev'   : dev,
        'pos'   : pos,
    }

    while True:
        data = []
        try:
            datapoint = read(devinfo)
            data.append(datapoint)

            logging.info(data)

            with InfluxDBClient(url=dburl, token=dbtoken, org=dborg) as cl:
                with cl.write_api() as wcl:
                    wcl.write(dbbucket, dborg, data, write_precision="s")

            p = Path(SLOWDIR) / 'data' / f'{model}_{pos}_{dev}.dat'
            with p.open('a') as f:
                for d in data:
                    f.write(json.dumps(d)+'\n')

            time.sleep(60)

        except KeyboardInterrupt:
            logging.info('Good bye!')
            break

        except:
            logging.exception('Exception: ')
            time.sleep(60)

if __name__ == '__main__':
    main()
