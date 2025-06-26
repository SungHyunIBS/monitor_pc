#!/opt/monitor/venv/bin/python
from datetime import datetime
import time
import cv2
import numpy as np
import sys
import logging
import os
import json
from pathlib import Path

import cv2
import numpy as np
import matplotlib.pyplot as plt
from influxdb_client import InfluxDBClient

logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO)

minutes = 1
wait    = minutes*60
SLOWDIR = '/opt/monitor/'
day_prefix = ['mon','tue','wed','thu','fri','sat','sun']


# 2025 / 06 / 18 by shkim
# Resister
#───────────────────────────────────────────────────────────
# 1 - 2 - 3
# x : +- 205
segmentBox_resist = [
    ["A1", (145, 20)], ["B1", (206, 75)], ["C1", (195,203)],
    ["D1", (126,253)], ["E1", ( 65,197)], ["F1", ( 75, 70)],
    ["G1", (134,135)], 
    ["A2", (350, 20)], ["B2", (411, 75)], ["C2", (400,203)],
    ["D2", (331,253)], ["E2", (270,197)], ["F2", (280, 70)],
    ["G2", (339,135)], 
    ["A3", (556, 20)], ["B3", (616, 75)], ["C3", (605,203)],
    ["D3", (536,253)], ["E3", (475,197)], ["F3", (485, 70)],
    ["G3", (544,135)], 
    [".",  (435,266)]
]

digit_map_resist = { # A,B,C,D,E,F,G
    (1,1,1,1,1,1,0): "0", (0,1,1,0,0,0,0): "1",
    (1,1,0,1,1,0,1): "2", (1,1,1,1,0,0,1): "3",
    (0,1,1,0,0,1,1): "4", (1,0,1,1,0,1,1): "5",
    (1,0,1,1,1,1,1): "6", (1,1,1,0,0,0,0): "7",
    (1,1,1,1,1,1,1): "8", (1,1,1,1,0,1,1): "9"
}
# ───────────────────────────────────────────────────────────
# 1 - 2 - 3
segmentBox_temp = [
    ["A1", ( 42, 12)], ["B1", ( 65, 12)], ["C1", ( 85, 40)],
    ["D1", ( 80, 93)], ["E1", ( 56,118)], ["F1", ( 36,118)],
    ["G1", ( 20, 93)], ["H1", ( 25, 40)], ["I1", ( 37, 65)],
    ["J1", ( 63, 65)],
    ["A2", (138, 12)], ["B2", (158, 12)], ["C2", (178, 40)],
    ["D2", (173, 93)], ["E2", (149,118)], ["F2", (129,118)],
    ["G2", (113, 93)], ["H2", (118, 40)], ["I2", (130, 65)],
    ["J2", (156, 65)],
    ["A3", (231, 12)], ["B3", (251, 12)], ["C3", (271, 40)],
    ["D3", (267, 93)], ["E3", (242,118)], ["F3", (222,118)],
    ["G3", (206, 93)], ["H3", (210, 40)], ["I3", (223, 65)],
    ["J3", (249, 65)],
    [".",  (186,124)]
]

digit_map_temp = { # A,B,C,D,E,F,G,H,I,J
    (1,1,1,1,1,1,1,1,0,0): "0", (0,0,1,1,0,0,0,0,0,0): "1",
    (1,1,1,0,1,1,1,0,1,1): "2", (1,1,1,1,1,1,0,0,1,1): "3",
    (0,0,1,1,0,0,0,1,1,1): "4", (1,1,0,1,1,1,0,1,1,1): "5",
    (1,1,0,1,1,1,1,1,1,1): "6", (1,1,1,1,0,0,0,0,0,0): "7",
    (1,1,1,1,1,1,1,1,1,1): "8", (1,1,1,1,0,0,0,1,1,1): "9"
}

# ───────────────────────────────────────────────────────────
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
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    x1, y1, x2, y2 = 1170, 300, 2715, 1250
    roi            = image[y1:y2, x1:x2]

    now = datetime.now()
    current_time = now.strftime("%Y%m%d_%H%M")

    output = 'webcam.png'
    outtxt = 'webcam.txt'
    outfile = Path(SLOWDIR) / 'out' / output
    outtime = Path(SLOWDIR) / 'out' / outtxt
    cv2.imwrite(f'{outfile}', roi)
    cap.release()
    
    with outtime.open('w') as f:
        f.write(str(int(time.time()) * 1000)+'\n')
    logging.info("Save {} : {}".format(output, current_time))
    os.popen("scp {} amoremon:/monitor/www/html/{}/".format(outfile, id))
    os.popen("scp {} amoremon:/monitor/www/html/{}/".format(outtime, id))

    rx1, ry1, rx2, ry2 = 606, 350, 1251, 635
    tx1, ty1, tx2, ty2 = 786, 640, 1076, 785
    resist_roi     = roi[ry1:ry2, rx1:rx2]
    temp_roi       = roi[ty1:ty2, tx1:tx2]

    return resist_roi, temp_roi

def decode_segments(active, typename):

    pos_ids = sorted({p for _,p in active if _ != "."}) #1, 2, 3
    if typename == "resist":
        seg_order = ['A','B','C','D','E','F','G']
        digit_map = digit_map_resist
    else:
        seg_order = ['A','B','C','D','E','F','G','H','I','J']
        digit_map = digit_map_temp

    pos_map = {pid:set() for pid in pos_ids}

    dot = any(lbl=="." for lbl,_ in active)
    for lbl, pid in active:
        if lbl == ".": 
            continue
        pos_map[pid].add(lbl[0])

    digits = []
    for pid in pos_ids:
        flags = tuple(int(s in pos_map[pid]) for s in seg_order)
        digits.append(digit_map.get(flags, "?"))
    if dot and len(digits)>=2:
        return "".join(digits[:-1]) + "." + digits[-1]
    return "".join(digits)

def decode_by_color(img, segmentBox, thresh, roi_size):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    result = {}
    for label, (cx, cy) in segmentBox:
        x1 = max(cx-roi_size, 0)
        y1 = max(cy-roi_size, 0)
        x2 = min(cx+roi_size, gray.shape[1]-1)
        y2 = min(cy+roi_size, gray.shape[0]-1)
        roi = gray[y1:y2+1, x1:x2+1]
        mean_val = round(float(np.mean(roi)), 2)
        if mean_val < thresh:
            on = True
        else:
            on = False

        result[label] = (mean_val, on)

        # (디버깅용) 이미지에 표시
        color = (0,255,0) if on else (0,0,255)
        cv2.rectangle(img, (x1,y1),(x2,y2), color, 1)
        cv2.putText(img, f"{label}:{int(on)}", (cx-5, cy-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    return result

def read_value(img, typename, threshold):

    if typename == "resist":
        segmentBox = segmentBox_resist
    else:
        segmentBox = segmentBox_temp
    res = decode_by_color(img, segmentBox, thresh=threshold, roi_size=3)
    active_segments = [(label, label[-1]) 
                              for label,(mean,on) in res.items() 
                              if on]
    number = decode_segments(active_segments, typename)
    return number

def main():

    id       = os.getenv('DEVICE_ID',  '')
    dburl    = os.getenv('DB_URL',     '')
    dborg    = os.getenv('DB_ORG',     '')
    dbbucket = os.getenv('DB_BUCKET',  '')
    dbtoken  = os.getenv('DB_TOKEN',   '') 
    
    while True:
        data = []
        try:
            resist_roi, temp_roi = runcam(id)
            
            resist = read_value(resist_roi, "resist", 120)
            temp   = read_value(temp_roi,   "temp",   170)

            resist = float(resist)
            #temp   = float(temp)
            
            wdata = {
                'resist' : resist,
            #    'temp'   : temp,
            }
            datapoint = {
                'measurement' : 'WCMD Env',
                'time'        : int(time.time()),
                'fields'      : wdata
            }
            data.append(datapoint)
            logging.info(data)

            with InfluxDBClient(url=dburl, token=dbtoken, org=dborg) as cl:
                 with cl.write_api() as wcl:
                     wcl.write(dbbucket, dborg, data, write_precision="s")

            p = Path(SLOWDIR) / 'data' / f'{id}.dat'
            with p.open('a') as f:
                for d in data:
                    f.write(json.dumps(d)+'\n')

            now    = datetime.now()
            prefix = day_prefix[now.weekday()]
            timestamp = now.strftime("%H%M")

            infile  = 'webcam.png'
            infilet = Path(SLOWDIR) / 'out' / infile
            outfile = Path(SLOWDIR) / 'webcam' / f'webcam_{prefix}_{timestamp}.png'

            os.system(f'cp {infilet} {outfile}')
                    
            time.sleep(60 - now.second)
        except KeyboardInterrupt:
            logging.info('Good bye')
            break
        except:
            logging.exception('Exception')
            time.sleep(wait)
    
if __name__=="__main__":
    main()

