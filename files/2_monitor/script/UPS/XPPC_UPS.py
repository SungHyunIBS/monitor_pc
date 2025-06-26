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
#### TO do : prescale import
port     = "101"
content  = "XPPCUPS"
SLOWDIR  = '/opt/monitor'

XPPC_OIDS = {
    '.1.3.6.1.4.1.935.1.1.1.2.2.1.0':
    {
        'name' : 'Battery Remain',
        'short_name' : 'Battery_remain',
        'type' : 'gauge',
    },

    '.1.3.6.1.4.1.935.1.1.1.2.2.3.0':
    {
        'name' : 'UPS Temperature',
        'short_name' : 'UPS_Temp',
        'type' : 'gauge',
        'pscale' : 10,
    },
    '.1.3.6.1.4.1.935.1.1.1.3.2.1.0':
    {
        'name' : 'Input Voltage',
        'short_name' : 'input_vol',
        'type' : 'gauge',
        'pscale' : 10,
    },
    '.1.3.6.1.4.1.935.1.1.1.3.2.4.0':
    {
        'name' : 'Input Frequnecy',
        'short_name' : 'input_freq',
        'type' : 'gauge',
        'pscale' : 10,
    },
    '.1.3.6.1.4.1.935.1.1.1.2.1.1.0':
    {
        'name' : 'Battery Status',
        'short_name' : 'battery_status',
        'type' : 'code',
        'code' :
        {
            2 : 'Normal',
            3 : 'Low',
        },
    },
    '.1.3.6.1.4.1.935.1.1.1.2.2.2.0':
    {
        'name' : 'Battery Voltage',
        'short_name' : 'battery_vol',
        'type' : 'gauge',
        'pscale' : 1,
    },
    '.1.3.6.1.4.1.935.1.1.1.4.2.3.0':
    {
        'name' : 'Output Load',
        'short_name' : 'output_load',
        'type' : 'gauge',
    },
    '.1.3.6.1.4.1.935.1.1.1.4.2.1.0':
    {
        'name' : 'Output Voltage',
        'short_name' : 'output_vol',
        'type' : 'gauge',
        'pscale' : 10,
    },
    '.1.3.6.1.4.1.935.1.1.1.4.1.1.0':
    {
        'name' : 'Output Source',
        'short_name' : 'output_source',
        'type' : 'code',
        'code' :
        {
            2 : 'OnLine',
            3 : 'Battery',
            6 : 'Bypass',
        },
    },
    '.1.3.6.1.4.1.935.1.1.1.4.2.2.0':
    {
        'name' : 'Output Frequnecy',
        'short_name' : 'output_freq',
        'type' : 'gauge',
        'pscale' : 10,
    },
}

def fetch(devinfo):

    ret  = None
    objs = [ObjectType(ObjectIdentity(ObjectIdentifier(oid))) for oid in XPPC_OIDS.keys()]

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
            
            # with InfluxDBClient(url=dburl, token=dbtoken, org=dborg) as cl:
            #     with cl.write_api() as wcl:
            #         wcl.write(dbbucket, dborg, data, write_precision="s")
            
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
