#!/bin/bash
if [ $EUID != 0 ]; then
	echo "--you are not root--"
	exit;
fi
python3 cronny.py -t ssh -a restart -d 1hr &
sleep 1
python3 cronny.py --status
exit
