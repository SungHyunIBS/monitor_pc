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
saveopt   = 0
saveint   = 10 # 10 min
def main():
    cnt = 0
    id  = os.getenv('DEVICE_ID',  '')

    while True:
        try:
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1920)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

            ret, image = cap.read()
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            now = datetime.now()
            current_time = now.strftime("%Y%m%d_%H%M")

            output = 'webcam.png'
            outtxt = 'webcam.txt'
            outfile1 = Path(outputdir) / output
            outtime  = Path(outputdir) / outtxt
            cv2.imwrite(f'{outfile1}', image)
            cap.release()

            with outtime.open('w') as f:
                f.write(str(int(time.time()) * 1000)+'\n')
            
            if(saveopt == 1):
                logging.info("Save {} : {}, {}".format(output, current_time, cnt))
            else:
                logging.info("Save {} : {}".format(output, current_time))

            # copy to YemilabMonitor
            os.popen("scp {} ymmon:/monitor/www/html/{}/".format(outfile1, id))
            os.popen("scp {} ymmon:/monitor/www/html/{}/".format(outtime,  id))

            # Save webcam for every 'saveint'
            if(saveopt == 1):
                cnt += 1
                if(cnt == saveint):
                    cnt = 0
                    outfile2 = 'webcam_'+current_time+'.png'
                    logging.info("Copy {} : {}".format(outfile2, current_time))
                    os.popen("scp {} ymmon:/home/cupadmin/{}/{}".format(outfile1, id, outfile2))

            time.sleep(wait)
        except KeyboardInterrupt:
            logging.info('Good bye')
            break
        except:
            logging.exception('Exception')
            time.sleep(wait)

if __name__ == '__main__':
    main()
