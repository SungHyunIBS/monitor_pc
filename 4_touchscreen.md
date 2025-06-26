# Touch Screen
<hr/>

### Contents
1. [Keyboard](#keyboard)
2. [CCTV](#cctv)

<hr/>

## Keyboard
* `sudo apt update`
* `sudo apt install matchbox-keyboard`

## CCTV
* Mobile app : Tapo
* RTSP protocol
	* `sudo apt install mpv`
* Add alias to `.bashrc` 
	* `alias cctv='mpv --no-audio --fs rtsp://COSINE:Eudum97@172.16.1.28:554/stream1'`
	* ID : COSINE, PW : Eudum97, IP : 172.16.1.28
