#!/bin/bash

./compile.sh

if [ $EUID != 0 ]; then
	echo "you are not root"; exit; fi

ServiceTableTest () {
	local -r testName="ServiceTableTest"
	local -r errExist=`test -f error`
	./src.pyz --status 2>error; tail -n7 error; rm error;
	if [ $? -eq 0 ]; then echo "TEST_SUCCESS $testName"; 
	else [ errExist != 0 ]; then echo "TEST_FAILED $testName: RETURNED $?"; fi
}

ScheduleTaskTest () {
	local -r testName="ScheduleTaskTest"
	./src.src.pyz -a "sudo systemctl restart ssh" 2>error;
	case "$(pidof ssh | wc -w)" in
		0) 	echo "TEST_FAILED $testName: RETURNED $?"
			;;
		1) 	echo "TEST_SUCCESS $testName: RETURNED $?"
			;;
		*) 	echo "UNKNOWN_RETURN $testName: RETURNED $?"
			;;
	esac
}

# Run Tests
ServiceTableTest
ScheduleTaskTest
