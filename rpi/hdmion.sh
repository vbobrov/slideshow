#!/usr/bin/bash
tvservice -s | grep -i off >/dev/null
if [ $? == 0 ]
then
	export DISPLAY=:0
	export Xauthority=/home/pi/.Xauthority
	tvservice -p
	fbset -depth 8
	fbset -depth 32
	xrefresh 
else
	echo Display is already on
fi
