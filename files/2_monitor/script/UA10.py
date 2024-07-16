#!/opt/monitor/venv/bin/python
import sys
import time
import logging
from pathlib import Path
import json
import serial
import os
from datetime import datetime
from influxdb_client import InfluxDBClient

logging.basicConfig(stream=sys.stdout, format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO)

SLOWDIR = '/opt/monitor'
model   = "UA10"

def read(devinfo):

    datapoint = {}
    with serial.Serial(devinfo['dev'], 19200, timeout=1) as ser:
        ser.write(b'ATCD\r\n')
        line1 = ser.readline()
        ser.write(b'ATCMODEL\r\n')
        line2 = ser.readline()
        
    line1 = line1.decode('utf-8').strip()
    line2 = line2.decode('utf-8').strip()
    logging.info(f'RESPONSE: {line1} {line2}')
    
    cmd, result = line1.split(' ')
    cmd, sn     = line2.split(' ')
    temp, hum   = result.split(',')

    wdata = {
        'temp'  : float(temp),
        'hum'   : float(hum),
    }
    
    tdata = {
        'dev'   : sn,
        'model' : model,
        'pos'   : devinfo['pos'],
    }

    datapoint = {
        'measurement' : 'temphum',
        'time'        : int(time.time()),
        'fields'      : wdata,
        'tags'        : tdata
    }

    return datapoint

def main():
 
    dev      = os.getenv('DEVICE_USB', '')
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
            dev       = datapoint['tags']['dev']
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
