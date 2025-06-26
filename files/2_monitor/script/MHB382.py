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
model = 'MHB382'

def read(devinfo):

    datapoint = {}
    ser = serial.Serial(devinfo['dev'], 9600, timeout=1)
    buffer = b""
    
    while True:
        raw = ser.read_until(b'\r')
        if raw.startswith(b'\x00'):
            continue
        buffer += raw

        if buffer.count(b'\r') >= 3:
            packets = buffer.split(b'\r')
            values  = []
            for packet in packets:
                if not packet:
                    continue
                if packet.startswith(b'\x02'):
                    packet = packet[1:]
                try:
                    val_str = packet[-5:].decode(errors='ignore')
                    val     = float(val_str) / 10
                    values.append(val)
                except Exception as e:
                    print(f"Failed to parse packet: {packet}, Error: {e}")
            
            ser.close()
            break

    logging.info(f'RESPONSE: {values}')
    hum  = values[0]
    temp = values[1]
    atmo = values[2]
    wdata = {
        'temp'  : float(temp),
        'hum'   : float(hum),
        'atmo'  : float(atmo),
    }

    tdata = {
        'model' : model,
        'pos'   : devinfo['pos'],
    }

    datapoint = {
        'measurement' : 'Barometer',
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
            data.append(datapoint)

            logging.info(data)

            with InfluxDBClient(url=dburl, token=dbtoken, org=dborg) as cl:
                with cl.write_api() as wcl:
                    wcl.write(dbbucket, dborg, data, write_precision="s")

            p = Path(SLOWDIR) / 'data' / f'{model}_{pos}.dat'
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
