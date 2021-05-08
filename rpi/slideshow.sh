#!/usr/bin/bash
killall feh
sleep 2
export DISPLAY=:0
export Xauthority=/home/pi/.Xauthority
while [ 1 == 1 ]
do
	find /home/pi/slideshow/downloader/slideshow|sort -R|feh -Y -x -q -D 15 -B black -F -Z --on-last-slide=quit -f -
	if [ $? -gt 128 ]
	then
		break
	fi
done
