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

### Others
* Install library
	* `sudo apt install libopenblas-dev`

### InfluxDB-Client
* Install Influxdb-Client
	* `pip install influxdb_client`

### Module-communication
* Install py-serial
	* `pip install pyserial`

### APEX P3
* Install pyModbusTCP (APEXP3)
	* `pip install pyModbusTCP`
* Need wired connection using cross-cable
	* Settings for simultaneous use of wired and wireless Internet
	* Modify `/etc/dhcpcd.conf` and insert following lines
		* Wireless : 192.168.1.XXX
		* Wired    : 192.168.2.XXX

```
interface eth0
static ip_address=192.168.2.2/24
nogateway
```

## ETC
* In the [files](./files/2_supervisor),
	* `supervisord.conf`
		* (move to `/etc/supervisor/` with `sudo`)