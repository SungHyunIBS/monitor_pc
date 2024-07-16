# Basic Setting
<hr/>

### Contents
1. [SSH setting](#ssh-setting)
2. [Text Mode](#text-mode)
3. [Terminal setting](#terminal-setting)
4. [Mirror setting](#mirror-setting)
5. [Remove unnecessary packages](#remove-package)
6. [Install necessary packages](#install-package)
7. [Python Environment](#python-environment)
8. [Screen Saver Off](#screen-saver-off)
9. [Internet Setting](#internet-setting)
10. [ETC](#etc)

<hr/>

## SSH Setting
* Go to Preferences &rarr; Raspberry Pi Configuration &rarr; Interfaces

<img src = "./images/basic-01.png" width = "80%"></img>

* Copy SSH public key (`cup_desk_id_rsa`, `cup_desk_id_rsa.pub`)
	* Copy `cup_desk_id_rsa.pub` &rarr; `authorized_keys`

* SSH config setting
	* `cd ~/.ssh; touch config`

	```
	Host ymmon
     Hostname ymmonitor.koreacentral.cloudapp.azure.com
     User cupadmin
     Port 22
     IdentityFile ~/.ssh/cup_desk_id_rsa
	```
	
## Text Mode
* Go to Preferences &rarr; Raspberry Pi Configuration &rarr; System

<img src = "./images/basic-02.png" width = "80%"></img>

## Terminal Setting
* Cpoy `bashrc` to `.bashrc`
* `source ~/.bashrc`
* Delete unnecessary term in `.profile`

```
if [ -d "$HOME/.local/bin" ] ; then
    PATH="$HOME/.local/bin:$PATH"
fi
```

## Mirror Setting
* Modify fastest mirror
	* `sudo nano /etc/apt/sources.list`
		* `deb [ arch=armhf ] http://ftp.kaist.ac.kr/raspbian/raspbian bookworm main contrib non-free rpi`

## Remove Package
* Remove unnecessary packages due to limited disk size

	* `sudo apt purge wolfram-engine`
	* `sudo apt purge libreoffice*`
	* `sudo apt clean`
	* `sudo apt autoremove`
	* `sudo apt update && sudo apt upgrade`

* Problem happen :
	* `sudo cp /etc/apt/trusted.gpg /etc/apt/trusted.gpg.d`
	
```
W: http://ftp.kaist.ac.kr/raspbian/raspbian/dists/bookworm/InRelease: 
Key is stored in legacy trusted.gpg keyring (/etc/apt/trusted.gpg),
see the DEPRECATION section in apt-key(8) for details.
```



## Install Package
* Install emacs
	* `sudo apt install emacs`

## Python Environment
* Working directory : `/opt/monitor`
	* `cd /opt; sudo mkdir monitor; sudo chown pi:pi monitor; cd monitor`
	* `mkdir -p data log out script supervisor/available`
* Python virtual evnironment
	* `python3 -m venv venv`
	* `source venv/bin/activate`
	* `pip install --upgrade pip`
		* `which pip`를 이용하여 `pip`를 위치를 확인
			*  `/opt/monitor/venv/bin/pip`

## Screen Saver Off
* `sudo nano /etc/lightdm/lightdm.conf`
	* modify 
		* `#xserver-command=X` &rarr;
		* `xserver-command=X -s 0 -dpms`
		* Reboot

## Internet Setting
* `sudo nmtui`
	
* (Option) `sudo raspi-config` 
	* `1 System Options` &rarr; `S1 Wireless LAN`
	* Set `SSID` and `PW` &rarr; Reboot

* Then reboot
	
## ETC
* In the [files](./files/1_basic_setting),
	* `bashrc` 
		* (move & rename to `~/.bashrc`)
	* `config, cup_desk_id_rsa`, `cup_desk_id_rsa.pub`
		* (move to `~/.ssh/`)
	* `sources.list`
		* (move to `/etc/apt/` with `sudo`)
	* `lightdm.conf`
		* (move to `/etc/lightdm/` with `sudo`)
