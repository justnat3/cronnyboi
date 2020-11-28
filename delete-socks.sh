#!/bin/bash
if [ $EUID != 0 ]; then
	echo "--you are not root--"
	exit
fi
rm /tmp/sck* && python3 cronny.py --status
