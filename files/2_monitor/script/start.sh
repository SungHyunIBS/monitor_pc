#!/bin/bash
sleep 30
sudo supervisorctl start run_webcam
sudo supervisorctl start run_UA10
sudo supervisorctl start run_adam6018p
sudo supervisorctl start run_APEXP3
sudo supervisorctl start run_PCInfo
sudo supervisorctl start run_gasflow
sudo supervisorctl start run_MHB382
sleep 60
sudo supervisorctl start run_DSM101
sleep 210
udo supervisorctl start run_UA58
sleep 330
sudo supervisorctl start run_RS9A
sudo supervisorctl start run_UA20
sudo supervisorctl start run_UA50
sudo supervisorctl start run_REP2A
sudo supervisorctl start run_rad7
