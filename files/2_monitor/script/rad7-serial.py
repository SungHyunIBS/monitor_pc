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

import re
logging.basicConfig(stream=sys.stdout, format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO)

SLOWDIR = '/opt/monitor'
BUFSIZE =102400

def read_until_prompt(ser):
    data = bytearray(BUFSIZE)
    for i in range(BUFSIZE):
        b = ser.read()
        if len(b) > 0:
            data[i] = b[0]
            if i >= 2:
                if data[i-2:i+1] == b'\r\n>':
                    logging.info('Prompt line founded')
                    break
        else:
            logging.info('Read timeout or no data')
            break
    return data.decode('ascii')

def test_start(ser):
    logging.info('Send ETX')
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    
    logging.info('Send Test Start')
    ser.write(b'Test Start\r\n')
    buf = ser.read(BUFSIZE)
    if len(buf) > 0:
        logging.info(buf.decode('ascii'))
    else:
        logging.error('No data')

def test_status(ser):
    logging.info('Send ETX')
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    
    logging.info('Send Test Status')
    ser.write(b'Test Status\r\n')
    buf  = ser.read(BUFSIZE)
    if len(buf) > 0:
        logging.info(buf.decode('ascii'))
    else:
        logging.error('No data')
        
    obuf = buf.decode('ascii')
    line = obuf.split('\r\n')
    text = line[2].split()
    status = text[1]

    return status
    
def test_clear(ser):
    logging.info('Send ETX')
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    
    logging.info('Send Test Clear')
    ser.write(b'Test Clear')
    logging.info('Send Yes')
    ser.write(b'Yes\r\n')
    buf = ser.read(BUFSIZE)
    if len(buf) > 0:
        logging.info(buf.decode('ascii'))
    else:
        logging.error('No data')

def data_erase(ser):
    logging.info('Send ETX')
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    
    logging.info('Send Data Erase')
    ser.write(b'Data Erase')
    logging.info('Send Yes')
    ser.write(b'Yes\r\n')
    buf = ser.read(BUFSIZE)
    if len(buf) > 0:
        logging.info(buf.decode('ascii'))
    else:
        logging.error('No data')
        
def test_stop(ser):
    logging.info('Send ETX')
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    
    logging.info('Send Test Stop')
    ser.write(b'Test Stop\r\n')
    buf = ser.read(BUFSIZE)
    if len(buf) > 0:
        logging.info(buf.decode('ascii'))
    else:
        logging.error('No data')

def parse_runnum(data):
    runnum = None
    for line in data.split('\r\n'):
        m = re.search('^([0-9]+)', line)
        if m is not None:
            runnum = int(m.group(1).strip()[:2])
    return runnum

def parse_data(data):

    dlst = list()
    v = data.split('\r\n')
    if(v[2] == "No tests stored."):
        raise NameError('Wait')
    
    for line in data.split('\r\n'):
        d = [ l.strip() for l in line.split(',') ]
        if d[0].isdigit():
            dlst.append(d)
    ret = list()
    for d in dlst:
        if d == dlst[-1]:
            try:
                t = time.strptime(' '.join(d[1:6]), '%y %m %d %H %M')
                tstamp = int(time.mktime(t))
                output = {
                    #'time': tstamp,
                    'recnum': float(d[0]),
                    'totc': float(d[6]),
                    'livet': float(d[7]),
                    'totcA': float(d[8]),
                    'totcB': float(d[9]),
                    'totcC': float(d[10]),
                    'totcD': float(d[11]),
                    'hvlvl': float(d[12]),
                    'hvcycle': float(d[13]),
                    'temp': float(d[14]),
                    'hum': float(d[15]),
                    'leaki': float(d[16]),
                    'batv': float(d[17]),
                    'pumpi': float(d[18]),
                    'flag': float(d[19]),
                    'radon': float(d[20]),
                    'radon_uncert': float(d[21]),
                    'unit': float(d[22]),
                }
                ret.append((tstamp, output))
                logging.debug((tstamp, output))
                
            except IndexError:
                logging.exception('Line parsing failed')
                continue
            
    return ret

def fetch(dev):
    with serial.Serial(dev, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=30) as ser:
        logging.info('Send ETX')
        ser.write(b'\x03\r\n')
        res = read_until_prompt(ser)
        ser.write(b'\x03\r\n')
        res = read_until_prompt(ser)

        logging.info('Send ETX')
        ser.write(b'\x03\r\n')
        res = read_until_prompt(ser)
        ser.write(b'\x03\r\n')
        res = read_until_prompt(ser)
        logging.info('Send Special Status')
        ser.write(b'Special Status\r\n')
        res = read_until_prompt(ser)
        runnum = parse_runnum(res)
        logging.debug(f'Run number is {runnum}')

        logging.info(f'Send Data Com {runnum:02d}')
        ser.write(f'Data Com {runnum:2d}\r\n'.encode('ascii'))
        res = read_until_prompt(ser)
        logging.info('Parse data')
        ret = parse_data(res)
        val = ret[-1][1]['recnum']
        # check recnum > 997 => run stop, clear
        if(val > 997):
            test_stop(ser)
            test_clear(ser)
            data_erase(ser)
            test_start(ser)
        
        return ret

def main():

    dev      = os.getenv('DEVICE',   None)
    pos      = os.getenv('DEVICE_POS', '')
    sn       = os.getenv('DEVICE_SN',  '')
    dburl    = os.getenv('DB_URL',     '')
    dborg    = os.getenv('DB_ORG',     '')
    dbbucket = os.getenv('DB_BUCKET',  '')
    dbtoken  = os.getenv('DB_TOKEN',   '')

    if len(pos) == 0 or len(sn) == 0:
        logging.error('No pos or sn error! Stop program.')
        sys.exit(1)
    logging.info('Start loop')

    # Check run Idle / Live ?
    with serial.Serial(dev, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=30) as ser:
        rst = test_status(ser)
        print(rst)
        if(rst == "Idle"):
            test_start(ser)
            
    while True:
        data = []
        try:
            ret = fetch(dev)
            for tstamp, wdata in ret:
                
                tdata = {
                    'dev'   : sn,
                    'pos'   : pos,
                }
                
                datapoint = {
                    'measurement' : 'rad7',
                    'time'        : tstamp,
                    'fields'      : wdata,
                    'tags'        : tdata
                }
                
                data.append(datapoint)

            logging.info(data)

            with InfluxDBClient(url=dburl, token=dbtoken, org=dborg) as cl:
                with cl.write_api() as wcl:
                    wcl.write(dbbucket, dborg, data, write_precision="s")

            p = Path(SLOWDIR) / 'data' / f'rad7-serial_{pos}_{sn}.dat'
            with p.open('a') as f:
                for d in data:
                    f.write(json.dumps(d)+'\n')

            time.sleep(7200)
        except ValueError:
            logging.exception('Parsing failed. Retry after 10 secs...')
            time.sleep(10)
        except NameError:
            logging.exception('Exception: Wait')
            time.sleep(600)
            
        except KeyboardInterrupt:
            logging.info('Good bye')
            break
        except:
            logging.exception('Exception: ')
            time.sleep(600)

if __name__ == '__main__':
    main()
