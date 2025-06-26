#!/opt/monitor/venv/bin/python
import sys
import time
import logging
from pathlib import Path
import json
import os
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient

import asyncio
import re
import struct
from enum import IntEnum
from bleak import BleakClient

logging.basicConfig(stream=sys.stdout, format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO)

SLOWDIR = '/opt/monitor'
model   = 'RE_p2a'

# UUIDs for BLE characteristics
WRITE_UUID = "00001524-0000-1000-8000-00805f9b34fb"
MEAS_UUID  = "00001525-0000-1000-8000-00805f9b34fb"  # Device info query response
LOG_UUID   = "00001526-0000-1000-8000-00805f9b34fb"  # Measurement/log response

class Command(IntEnum):
    BLE_LOG_CLEAR               = 98
    BLE_LOG_DATA_SEND           = 97
    BLE_LOG_DATA_SEND_RECENT    = 99
    RD200_DATE_TIME_SET         = 85
    USER_CONFIG_SET             = 83
    DEVICE_INFO_QUERY           = 160  # 0xA0
    ENG_DC_FACTOR_SET           = 115
    ENG_OLED_CONST_SET          = 113
    ENG_OP_MODE                 = 116
    ENG_OP_MODE_QUERY           = 117
    ENG_SERIAL_No_SETUP         = 112
    LOG_PERCENT                 = 245
    MAIN_BLE_URL_SET            = 71
    MAIN_WIFI_SCAN_QUERY        = 74
    MAIN_WIFI_SET               = 69
    OTA_DATA_SEND               = 129
    OTA_RESULT                  = 130
    OTA_START                   = 128

# Build packet with checksum matching APK logic
def make_packet(cmd: int, payload: bytes = b"") -> bytearray:
    total = cmd + sum(payload)
    checksum = (255 - (total & 0xFF)) & 0xFF
    return bytearray([cmd]) + payload + bytearray([checksum])

# Parse info query response payload
def parse_device_info(data: bytes) -> dict:
    info = {}
    cmd = data[0]
    if cmd != Command.DEVICE_INFO_QUERY:
        raise ValueError(f"Unexpected cmd: {cmd}")

    # Extract ASCII sequences (length ≥4)
    ascii_seqs = re.findall(b'[ -~]{4,}', data)
    labels = ['serial', 'firmware', 'model_code']
    for lbl, seq in zip(labels, ascii_seqs):
        info[lbl] = seq.decode('ascii')
    # Example numeric fields at fixed offsets
    hw_major, hw_minor = data[13], data[14]
    build_lo, build_hi = data[15], data[16]
    info['hw_version']   = f"{hw_major}.{hw_minor}"
    info['build_number'] = (build_hi << 8) | build_lo
    info['battery_pct']  = data[17]
    return info

def convert_humidity(th_raw: int) -> int:
    i = th_raw & 0xFF  # 하위 8비트
    if i <= 0:
        i += 256
    return i % 128

def convert_temperature(th_raw: int) -> float:
    int_part = th_raw >> 8
    frac_bit = (th_raw >> 7) & 0x1
    return int_part + (0.5 if frac_bit == 1 else 0.0)

def parse_log_data(raw):
    entries = []
    data = raw[4:]  # Skip command header
    for i in range(0, len(data), 8):
        if i + 8 > len(data):
            break
        entry = data[i:i+8]
        ts_bytes = entry[0:4]
        radon_bytes = entry[4:6]
        temp_humi_bytes = entry[6:8]

        timestamp = int.from_bytes(ts_bytes, 'little') - 9 * 60 * 60

        radon_raw = int.from_bytes(radon_bytes, 'little')
        radon = radon_raw

        th_raw = int.from_bytes(temp_humi_bytes, 'little')
        
        temperature = convert_temperature(th_raw)
        humidity = convert_humidity(th_raw)
        
        entries.append({
            'measurement'   : 'RadonEye',
            'timestamp'     : timestamp,
            'radon'         : radon,
            'temperature'   : temperature,
            'humidity'      : humidity,
        })
    return entries

async def readdata(devinfo):
    
   async with BleakClient(devinfo['dev']) as client:

        logging.debug(f"Connected: {client.is_connected}")

        # Display characteristic properties for WRITE_UUID
        services = client.services
        char = services.get_characteristic(WRITE_UUID)
        logging.debug(f"WRITE_UUID props: {char.properties}")

        wdata  = None
        parsed = None
        
        # Device info notification callback
        def info_cb(handle, data):
            nonlocal parsed
            raw = bytes(data)
            logging.debug(f"[INFO RAW] {raw.hex()}")
            if raw[0] != Command.DEVICE_INFO_QUERY:
                logging.debug("info_cb: Not DEVICE_INFO_QUERY, skip.")
                return
            try:
                parsed = parse_device_info(raw)
                logging.info(f"[INFO PARSED] {parsed}")
                tdata = parsed
            except Exception as e:
                logging.debug(f"Parse error (info): {e}")

        def log_cb(handle, data):
            nonlocal wdata
            raw = bytes(data)
            logging.debug(f"[LOG RAW] {raw.hex()}")
            entries = parse_log_data(raw)
            for e in entries:
                logging.debug(f"[LOG ENTRY] {e}")
            wdata = entries[-1]
            logging.info(f"[LOG ENTRY] {wdata}")
            
        # Subscribe to notifications
        await client.start_notify(MEAS_UUID, info_cb)
        await client.start_notify(LOG_UUID,  log_cb)

        # 1) Send device info query (A0)
        pkt = make_packet(Command.DEVICE_INFO_QUERY)
        logging.debug(f"→ Send INFO QUERY (no-response): {pkt.hex()}")
        await client.write_gatt_char(WRITE_UUID, pkt, response=False)
        await asyncio.sleep(2)

        # 2) Send measurement value request (0x61)
        pkt = make_packet(Command.BLE_LOG_DATA_SEND)
        logging.debug(f"→ Send BLE_LOG_DATA_SEND (no-response): {pkt.hex()}")
        await client.write_gatt_char(WRITE_UUID, pkt, response=False)

        # 3) Send recent log request (0x63)
        pkt = make_packet(Command.BLE_LOG_DATA_SEND_RECENT)
        logging.debug(f"→ Send BLE_LOG_DATA_SEND_RECENT (no-response): {pkt.hex()}")
        await client.write_gatt_char(WRITE_UUID, pkt, response=False)

        # 4) Send op mode query (0x75)
        pkt = make_packet(Command.ENG_OP_MODE_QUERY)
        logging.debug(f"→ Send ENG_OP_MODE_QUERY (no-response): {pkt.hex()}")
        await client.write_gatt_char(WRITE_UUID, pkt, response=False)

        # Wait for notification responses
        await asyncio.sleep(2)

        # Unsubscribe
        await client.stop_notify(MEAS_UUID)
        await client.stop_notify(LOG_UUID)

        ts = wdata.get('timestamp')

        tdata = {
            'dev'   : parsed['serial'],
            'model' : model,
            'pos'   : devinfo['pos'],
        }

        wdata.pop('timestamp', None)
        
        datapoint = {
            'measurement' : 'RadonEye',
            'time'        : ts,
            'fields'      : wdata,
            'tags'        : tdata
        }

        return datapoint

async def main():

    addr     = os.getenv('DEVICE_ADDR', '')
    pos      = os.getenv('DEVICE_POS',  '')
    dburl    = os.getenv('DB_URL',      '')
    dborg    = os.getenv('DB_ORG',      '')
    dbbucket = os.getenv('DB_BUCKET',   '')
    dbtoken  = os.getenv('DB_TOKEN',    '')

    devinfo = {
        'dev'   : addr,
        'pos'   : pos,
    }

    while True:
        data = []
        try:
            datapoint = await readdata(devinfo)
            data.append(datapoint)
            dev       = datapoint['tags']['dev']
            logging.debug(data)

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

        except:
            logging.exception('Exception: ') 
            time.sleep(600)

if __name__ == "__main__":

    asyncio.run(main())
