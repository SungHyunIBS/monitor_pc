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

model    = "DSM101"

def read(devinfo):

    w_basic_info  = b'\x02\x12\x00\x00\xED\r\n'
    w_value_query = b'\x02\x10\x00\x00\xEF\r\n'
    datapoint = {}
    
    with serial.Serial(devinfo['dev'], 19200, timeout=1) as ser:
        ser.write(w_basic_info)
        # Read
        # STX(1), CMD(1), Size(2; lsb, msb), Data(23), Chksum(1)
        line = ser.readline()
        stx    = line[0]
        cmd    = line[1]
            
        if(stx == 0x02 and cmd == 0x13):
            sn = line[5:17].decode('utf-8').strip()
        else:
            raise NameError('Retry')

        ser.write(w_value_query)
    
        # Read
        # STX(1), CMD(1), Size(2; lsb, msb), Data(24), Chksum(1)
        line1 = ser.readline()
        if(len(line1) == 29):
            line = line1
        else:
            line2 = ser.readline()
            linea = bytearray()
            for nline in line1:
                linea.append(nline)
            for nline in line2:
                linea.append(nline)
            line = linea   

        #logging.info(f'Data size:  {len(line)}')
        
        if(len(line) == 29):
            stx    = line[0]
            cmd    = line[1]
            chksum = line[-1]
            if(stx == 0x02 and cmd == 0x11):
                size = line[3]*16 + line[2]
                if(size == 24):
                    data = line[4:28]
                    pm1_10min   = data[13] * 16 + data[12]
                    pm2d5_10min = data[15] * 16 + data[14]
                    pm10_10min  = data[17] * 16 + data[16]
                    wdata = {
                        'pm1'   : float(pm1_10min),
                        'pm2d5' : float(pm2d5_10min),
                        'pm10'  : float(pm10_10min),
                    }
                    
                    tdata = {
                        'dev'   : sn,
                        'model' : model,
                        'pos'   : devinfo['pos'],
                    }
                    
                    datapoint = {
                        'measurement' : 'Dust Counter',
                        'time'        : int(time.time()),
                        'fields'      : wdata,
                        'tags'        : tdata
                    }

                else:
                    raise NameError('Retry')
            else:
                raise NameError('Retry')
        else:
            raise NameError('Retry')
    
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

            time.sleep(600)
            
        except KeyboardInterrupt:
            logging.info('Good bye!')
            break
        except NameError:
            logging.exception('Exception: Retry')
            time.sleep(300)
        except:
            logging.exception('Exception: ')
            time.sleep(300)

if __name__ == '__main__':
    main()
