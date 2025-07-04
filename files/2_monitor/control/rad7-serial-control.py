#!/opt/monitor/venv/bin/python

import sys
import logging
import serial
import re
import time

logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG)


DEV='/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A9KGLBIW-if00-port0'
BUFSIZE=102400

def read_until_prompt(ser):
    data = bytearray(BUFSIZE)
    for i in range(BUFSIZE):
        b = ser.read()
        if len(b) > 0:
            data[i] = b[0]
            if i >= 2:
                if data[i-2:i+1] == b'\r\n>':
                    logging.debug('Prompt line founded')
                    break
        else:
            logging.debug('Read timeout or no data')
            break
    return data.decode('ascii')

def test_start():
    with serial.Serial(DEV, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=10) as ser:
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

def test_status():
    with serial.Serial(DEV, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=10) as ser:
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
        print(text[1])

def test_clear():
    with serial.Serial(DEV, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=10) as ser:
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

def data_erase():
    with serial.Serial(DEV, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=10) as ser:
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
        
def setup_recycle():
    with serial.Serial(DEV, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=10) as ser:
        logging.info('Send ETX')
        ser.write(b'\x03\r\n')
        res = read_until_prompt(ser)
        ser.write(b'\x03\r\n')
        res = read_until_prompt(ser)

        logging.info('Send Setup Recycle')
        ser.write(b'Setup Recycle\r\n')
        res = read_until_prompt(ser)
        logging.debug(res)
        ser.write(b'00\r\n')
        res = read_until_prompt(ser)
        logging.debug(res)

def test_stop():
    with serial.Serial(DEV, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=10) as ser:
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

def test_purge():
    with serial.Serial(DEV, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=10) as ser:
        logging.info('Send ETX')
        ser.write(b'\x03\r\n')
        res = read_until_prompt(ser)
        ser.write(b'\x03\r\n')
        res = read_until_prompt(ser)

        logging.info('Send Test Purge')
        ser.write(b'Test Purge\r')
        res = read_until_prompt(ser)
        time.sleep(900)
            
        logging.info("Purge Stop")
        ser.write(b'Yes\r\n')
        res = read_until_prompt(ser)

def parse_runnum(data):
    runnum = None
    for line in data.split('\r\n'):
        m = re.search('^([0-9]+)', line)
        if m is not None:
            runnum = int(m.group(1).strip()[:2])
    return runnum

def run_status():
    with serial.Serial(DEV, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=10) as ser:
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

def parse_data(data):
    logging.debug(data)
    dlst = list()

    v = data.split('\r\n')
    if(v[2] == "No tests stored."):
        logging.info("No tests stored")
        
    for line in data.split('\r\n'):
        d = [ l.strip() for l in line.split(',') ]
        if d[0].isdigit():
            dlst.append(d)

    ret = list()
    for d in dlst:
        try:
            t = time.strptime(' '.join(d[1:6]), '%y %m %d %H %M')
            tstamp = int(time.mktime(t))
            output = {
                'time': tstamp,
                'recnum': int(d[0]),
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
                'flag': int(d[19]),
                'radon': float(d[20]),
                'radon_uncert': float(d[21]),
                'unit': int(d[22]),
            }
            ret.append((tstamp, output))
            logging.debug((tstamp, output))
        except IndexError:
            logging.exception('Line parsing failed')
            continue
    return ret

def main():
    #test_purge()
    test_start()
#    test_status()
#    run_status()
#    test_clear()
#    data_erase()
    #    test_status()
#    test_stop()

#    print("Asdasd")
    run_status()
    test_status()

if __name__ == '__main__':
    main()
