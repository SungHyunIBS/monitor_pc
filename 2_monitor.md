# Monitor
<hr/>

### Contents
1. [Install](#install)
2. [Script](#script)
3. [Supervisor](#supervisor)
4. [ETC](#etc)

<hr/>

## Install
* Install supervisor
	* `sudo apt install supervisor`
	* modify `/etc/supervisor/supervisord.conf`
		* [supervisord] logfile : location &rarr; /opt/monitor/log
		* [supervisord] childlogdir : location &rarr; /opt/monitor/log
		* [include] files : location &rarr; /opt/monitor/supervisor
* All supervisor config files will be located in 
	* `/opt/monitor/supervisor/available`
	* and make a link to `/opt/monitor/supervisor/`

* Run supervisor
	* `sudo systemctl start supervisor`
	* `sudo systemctl enable supervisor`

### Webcam
* Install webcam related libraries

```
sudo apt install cmake libhdf5-dev libhdf5-103 \
libgtk2.0-dev libgtk-3-dev \
gfortran libavformat-dev \
libxvidcore-dev libx264-dev libv4l-dev \
libtiff5-dev libswscale-dev libatlas-base-dev \
libjasper-dev libgdk-pixbuf2.0-dev
```
`pip install picamera[array] imutils`

* Currently (2023.02.04), V4.7.0.72 can be installed

`pip install opencv-python==4.7.0.72`

https://github.com/Comfy-Org/comfy-cli/issues/163
numpy version

### Others Library
* Install library
	* `sudo apt install libopenblas-dev`

### Pip Library
* Influxdb
	* `pip install influxdb_client`
* PC Info
	* `pip install psutil`
* Serial / USB
	* `pip install pyserial`
* Modbus, TCP
	* `pip install pyModbusTCP`
* Modbus, Serial
	* `pip install pymodbus`
* Bluetooth
	* `pip install bleak`
	* `pip install asyncio`
* Webcam Analysis
	* `pip install matplotlib`

## ETC
* In the [files](./files/2_supervisor),
	* `supervisord.conf`
		* (move to `/etc/supervisor/` with `sudo`)