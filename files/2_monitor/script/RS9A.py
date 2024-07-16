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

model    = "RS9A"

def read(devinfo):

    datapoint = {}
    with serial.Serial(devinfo['dev'], 19200, timeout=1) as ser:
        ser.write(b'VALUE?\r\n')
        line1 = ser.readline()
        ser.write(b'SERIALNO?\r\n')
        line2 = ser.readline()

    line1 = line1.decode('utf-8').strip()
    line2 = line2.decode('utf-8').strip()
    logging.info(f'RESPONSE: {line1} {line2}')

    val     = line1.split(' ')
    tmp, sn = line2.split(' ')
    st, tmp = val[1].split(':')
    rn, tmp = val[2].split(':')
    unit    = val[5]

    if st != "NORMAL":
        raise NameError('Wait')
    
    if unit == "0":
        with serial.Serial(devinfo['dev'], 19200, timeout=5) as ser:
            ser.write(b'UNIT 1\r\n')
            tmp = ser.readline()
            time.sleep(1)
            ser.write(b'VALUE?\r\n')
            line1 = ser.readline()   # read a '\n' terminated line
        line1 = line1.decode('utf-8').strip()

        val     = line1.split(' ')
        rn, tmp = val[2].split(':')

    wdata = {
        'Rn'  : float(rn),
    }
    
    tdata = {
        'dev'   : sn,
        'model' : model,
        'pos'   : devinfo['pos'],
    }

    datapoint = {
        'measurement' : 'Radon Sensor',
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

            time.sleep(3600)

        except KeyboardInterrupt:
            logging.info('Good bye!')
            break
            
        except NameError:
            logging.exception('Exception: Wait')
            time.sleep(600)
            
        except:
            logging.exception('Exception: ')
            time.sleep(600)
        
if __name__ == '__main__':
    main()
