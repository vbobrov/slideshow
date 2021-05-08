#!/usr/bin/bash
tvservice -s | grep -i off >/dev/null
if [ $? == 0 ]
then
	echo Display is already off
else
	tvservice -o
fi

