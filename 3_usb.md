# USB rules
* Will update
* `lsusb`
* `udevadm info -a -n /dev/ttyACM0 | grep '{serial}' |head -n1`
* `/etc/udev/rules.d`
* `sudo udevadm control --reload-rules`