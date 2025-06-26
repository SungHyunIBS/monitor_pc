#!/opt/monitor/venv/bin/python
import sys
import time
import logging
from pathlib import Path
import json
import os
from datetime import datetime
from influxdb_client import InfluxDBClient
from pysnmp.hlapi import *

logging.basicConfig(stream=sys.stdout, format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO)

port     = "161"
content  = "STDUPS"
SLOWDIR  = '/opt/monitor'

STD_OIDS = {
    '1.3.6.1.2.1.33.1.2.1.0':
    {
        'name': 'Battery Status',
        'short_name': 'battery_status',
        'type': 'code',
        'code' :
        {
            1: 'Unknown',
            2: 'Normal',
            3: 'Low',
            4: 'Depleted',
        },
    },
    '1.3.6.1.2.1.33.1.2.3.0':
    {
        'name': 'Battery Remain',
        'short_name': 'battery_remain',
        'type': 'gauge',
    },
    '1.3.6.1.2.1.33.1.2.4.0':
    {
        'name': 'Battery Charge',
        'short_name': 'battery_charge',
        'type': 'gauge',
    },
    '1.3.6.1.2.1.33.1.3.3.1.3.1':
    {
        'name': 'Input Voltage 1',
        'short_name': 'input_vol1',
        'type': 'gauge',
    },
    '1.3.6.1.2.1.33.1.3.3.1.3.2':
    {
        'name': 'Input Voltage 2',
        'short_name': 'input_vol2',
        'type': 'gauge',
    },
    '1.3.6.1.2.1.33.1.3.3.1.3.3':
    {
        'name': 'Input Voltage 3',
        'short_name': 'input_vol3',
        'type': 'gauge',
    },
    '1.3.6.1.2.1.33.1.4.1.0':
    {
        'name': 'Output Source',
        'short_name': 'output_source',
        'type': 'code',
        'code' :
        {
            1: 'other',
            2: 'none',
            3: 'normal',
            4: 'bypass',
            5: 'battery',
            6: 'booster',
            7: 'reducer',
        }
    },
    '1.3.6.1.2.1.33.1.4.4.1.2.1':
    {
        'name': 'Output Voltage 1',
        'short_name': 'output_vol1',
        'type': 'gauge',
    },
    '1.3.6.1.2.1.33.1.4.4.1.2.2':
    {
        'name': 'Output Voltage 2',
        'short_name': 'output_vol2',
        'type': 'gauge',
    },
    '1.3.6.1.2.1.33.1.4.4.1.2.3':
    {
        'name': 'Output Voltage 3',
        'short_name': 'output_vol3',
        'type': 'gauge',
    },
    '1.3.6.1.2.1.33.1.4.4.1.5.1':
    {
        'name': 'Output Load 1',
        'short_name': 'output_load1',
        'type': 'gauge',
    },
    '1.3.6.1.2.1.33.1.4.4.1.5.2':
    {
        'name': 'Output Load 2',
        'short_name': 'output_load2',
        'type': 'gauge',
    },
    '1.3.6.1.2.1.33.1.4.4.1.5.3':
    {
        'name': 'Output Load 3',
        'short_name': 'output_load3',
        'type': 'gauge',
    },
}

def fetch(devinfo):

    ret = None
    objs = [ ObjectType(ObjectIdentity(ObjectIdentifier(oid))) for oid in STD_OIDS.keys() ]

    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
               CommunityData('public', mpModel=0),
               UdpTransportTarget((devinfo['dev'], devinfo['port'])),
               ContextData(),
               *objs
        )
    )
    if errorIndication:
        logging.error(errorIndication)
    elif errorStatus:
        logging.error('%s at %s' % (errorStatus.prettyPrint(),
                                    errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
    else:
        wdata = {}
        for varBind in varBinds:
            logging.debug(' = '.join([x.prettyPrint() for x in varBind]))
            name, val = varBind

            wdata[STD_OIDS[str(name.getOid())]["short_name"]] = float(val)

            
        tdata = {
            'model' : devinfo['model'],
            'pos'   : devinfo['pos'],
            'ip'    : devinfo['dev'],
        }

        datapoint = {
            'measurement' : 'UPS Status',
            'time'        : int(time.time()),
            'fields'      : wdata,
            'tags'        : tdata
        }

    return datapoint

def main():

    pos      = os.getenv('DEVICE_POS', '')
    iph      = os.getenv('DEVICE_IPH',  '')
    ipl      = os.getenv('DEVICE_IPL',  '')
    ip       = iph+"."+ipl
    model    = os.getenv('DEVICE_DEV',  '')
    dburl    = os.getenv('DB_URL',     '')
    dborg    = os.getenv('DB_ORG',     '')
    dbbucket = os.getenv('DB_BUCKET',  '')
    dbtoken  = os.getenv('DB_TOKEN',   '')
    devinfo = {
        'dev'   : ip,
        'pos'   : pos,
        'model' : model,
        'port'  : port
    }

    while True:
        data = []
        try:
            datapoint = fetch(devinfo)
            data.append(datapoint)
            logging.info(data)
            
            with InfluxDBClient(url=dburl, token=dbtoken, org=dborg) as cl:
                with cl.write_api() as wcl:
                    wcl.write(dbbucket, dborg, data, write_precision="s")
            
            p = Path(SLOWDIR) / 'data' / f'{content}_{pos}_{model}.dat'
            with p.open('w') as f:
                for d in data:
                    f.write(json.dumps(d)+'\n')

            time.sleep(30)
        except KeyboardInterrupt:
            logging.info('Good bye')
            break
        except:
            logging.exception("Exception")
            time.sleep(30)

if __name__ == '__main__':
    main()
