#!/opt/monitor/venv/bin/python
import sys
import time
import logging
from pathlib import Path
import json
import os
from datetime import datetime
import struct
from influxdb_client import InfluxDBClient
from pymodbus.client.serial import ModbusSerialClient as modbus

logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO)

SLOWDIR  = '/opt/monitor'
model    = 'red-y'
slave    = 247 # Default Device Address : 247

def read(devinfo):

    datapoint = {}
    with modbus(devinfo['dev'], baudrate=9600, stopbits=2, timeout=1) as client:        
        r       = client.read_holding_registers(address=0, count=2, slave=247)
        data    = struct.pack('>HH', r.registers[0], r.registers[1])
        gasflow = struct.unpack('>f', data)[0]
        gasflow = round(gasflow, 1)
        
    wdata = {
        'gasflow' : float(gasflow)
    }

    tdata = {
        'model' : model,
        'pos'   : devinfo['pos'],
    }
    
    datapoint = {
        'measurement' : 'gasflow',
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

            p = Path(SLOWDIR) / 'data' / f'gasflow_{pos}.dat'
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
