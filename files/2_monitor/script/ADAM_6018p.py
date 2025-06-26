#!/opt/monitor/venv/bin/python
import sys
import time
import logging
from pathlib import Path
import json
import serial
import os
import math

import datetime
from datetime import datetime
from pyModbusTCP.client import ModbusClient
from influxdb_client import InfluxDBClient

logging.basicConfig(stream=sys.stdout, format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO)

SLOWDIR = '/opt/monitor'
model   = 'ADAM_6018p'

class ThermocoupleConverter:
    def __init__(self, min_temp=-100, max_temp=400, min_raw=0, max_raw=65535):
        # Initialize the temperature and raw value range
        self.min_temp = min_temp  # Minimum temperature (°C)
        self.max_temp = max_temp  # Maximum temperature (°C)
        self.min_raw = min_raw    # Minimum raw value (0)
        self.max_raw = max_raw    # Maximum raw value (65535)

    def raw_to_temperature(self, raw_value):
        # Convert raw value to temperature using linear scaling
        if not self.min_raw <= raw_value <= self.max_raw:
            raise ValueError(f"Raw value {raw_value} is out of bounds.")
        
        # Apply the scaling formula to convert raw value to temperature
        temp = ((raw_value - self.min_raw) / (self.max_raw - self.min_raw)) * (self.max_temp - self.min_temp) + self.min_temp
        return temp

    def temperature_to_raw(self, temperature):
        # Convert temperature to raw value using linear scaling
        if not self.min_temp <= temperature <= self.max_temp:
            raise ValueError(f"Temperature {temperature} is out of bounds.")
        
        # Apply the reverse scaling formula to convert temperature to raw value
        raw_value = int(((temperature - self.min_temp) / (self.max_temp - self.min_temp)) * (self.max_raw - self.min_raw) + self.min_raw)
        return raw_value

   
class Adam6018ModbusClient:
    def __init__(self, host, port=502, unit_id=1):
        self.client = ModbusClient(host=host, port=port, unit_id=unit_id)
    
    def connect(self):
        if not self.client.is_open:
            if not self.client.open():
                print("Modbus TCP connection fail")
    
    def read_temperature(self, ch):
        if not 0 <= ch <= 7:
            raise ValueError(f"Channel value {ch} is out of bounds.")
        if self.client.is_open:
            return self.client.read_holding_registers(ch, 1)
        else:
            print("Modbus client does not open.")
            return None

def read(devinfo):
    
    mod_ip = "172.16.1."+devinfo['dev']
    modbus_client = Adam6018ModbusClient(mod_ip)
    modbus_client.connect()

    wdata = {}
    conv_ai = ThermocoupleConverter()
    for ch in range(devinfo['nch']):
        ch_ai   = modbus_client.read_temperature(ch)
        temp = conv_ai.raw_to_temperature(ch_ai[0])
        rtemp = round(temp, 2)
        wdata[f'ch{ch}'] = rtemp

    tdata = {
        'model' : model,
        'pos'   : devinfo['pos'],
        'ip'    : devinfo['dev'],
    }

    datapoint = {
        'measurement' : 'Thermocouple Temperature',
        'time'        : int(time.time()),
        'fields'      : wdata,
        'tags'        : tdata
    }
    
    return datapoint
    
def main():

    pos      = os.getenv('DEVICE_POS', '')
    dev      = os.getenv('DEVICE_IP',  '')
    nch      = os.getenv('DEVICE_NCH', '')
    dburl    = os.getenv('DB_URL',     '')
    dborg    = os.getenv('DB_ORG',     '')
    dbbucket = os.getenv('DB_BUCKET',  '')
    dbtoken  = os.getenv('DB_TOKEN',   '')
    
    devinfo = {
        'dev'   : dev,
        'pos'   : pos,
        'nch'   : int(nch),
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
            with p.open('w') as f:
                for d in data:
                    f.write(json.dumps(d)+'\n')

            time.sleep(60)
        except KeyboardInterrupt:
            logging.info('Good bye!')
            break
            
        except NameError:
            logging.exception('Exception: Wait')
            time.sleep(60)
            
        except:
            logging.exception('Exception: ')
            time.sleep(60)

if __name__ == '__main__':
    main()
