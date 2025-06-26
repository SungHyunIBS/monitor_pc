#!/opt/monitor/venv/bin/python
from datetime import datetime
import time
import cv2
import numpy as np
import sys
import logging
import os
from pathlib import Path

logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO)

minutes=1
wait=minutes*60
outputdir = '/opt/monitor/out'

def runcam(id):
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
    # 4k : 3840 x 2160
    # raspberry : 1920 x 1080
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  3840)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)

    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)       # 1 = manual mode
    cap.set(cv2.CAP_PROP_EXPOSURE, 300)
    cap.set(cv2.CAP_PROP_ZOOM, 200)
    
    ret, image = cap.read()
    cv2.imwrite(f'{outfile}', image)
    cap.release()

    now = datetime.now()
    current_time = now.strftime("%Y%m%d_%H%M")

    output = 'webcam.png'
    outtxt = 'webcam.txt'
    outfile = Path(SLOWDIR) / 'out' / output
    outtime = Path(SLOWDIR) / 'out' / outtxt
    
    with outtime.open('w') as f:
        f.write(str(int(time.time()) * 1000)+'\n')
    logging.info("Save {} : {}".format(output, current_time))

    os.popen("scp {} ymmon:/monitor/www/html/{}/".format(outfile, id))
    os.popen("scp {} ymmon:/monitor/www/html/{}/".format(outtime, id))

def main():

    id       = os.getenv('DEVICE_ID',  '')
    while True:
        try:
            runcam(id)
            time.sleep(wait)
        except KeyboardInterrupt:
            logging.info('Good bye')
            break
        except:
            logging.exception('Exception')
            time.sleep(wait)

if __name__ == '__main__':
    main()
