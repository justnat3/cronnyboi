#!/bin/bash

if [ $EUID != 0 ]; then
	echo "--you are not root--"
	exit;
fi

rm -rf bin
mkdir bin

python3 -m pip install -r src/requirements.txt --target bin
python3 -m zipapp -p "/usr/bin/env python3" src

exit;
