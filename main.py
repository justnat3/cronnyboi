#!/bin/python3
__author__ = "Nathan Reed"

"""
Scheduling tasks with ease, provides an abstraction from crontab, sync not async.
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from enum import Enum
from pytz import utc
import subprocess
import argparse
import datetime
import time
import socket
import os
from os.path import isfile, isdir
## Vars


sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

parser = argparse.ArgumentParser(prog="webcron", description="Schedule Tasks With Ease")
parser.add_argument("-t", help="Target Task to Schedule", type=str, required=False)
parser.add_argument(
    "-a",
    help="restart, stop, start, :: DO NOT USE Disable/Enable",
    type=str,
    required=False,
)
parser.add_argument("-d", help="date ->  time", type=str, required=False)
parser.add_argument(
    "--status", help="get schedular current status", action='store_true', required=False
)
parser.add_argument("--stop", help="stops all instances of webcron", action='store_true', required=False)
parser.add_argument("--pause", help="pauses all instances of webcron", action='store_true', required=False)
args = parser.parse_args()

service: str = args.t
action: str = args.a
time_d: str = args.d
status: bool = args.status
stop: bool = args.stop
pause: bool = args.pause


# Config :: MemoryJobStore :: Blocked-Schedule
jobstores = {"memory": {"type": "memory"}}
executors = {
    "default": {"type": "threadpool", "max_workers": 1},
    "threadpool": ThreadPoolExecutor(max_workers=1),
}
job_defaults = {"coalesce": False, "max_instances": 1}

## Define Scheduler :: configure
scheduler = BlockingScheduler()
scheduler.configure(
    jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc
)


def main(service: str, action: str, time_d: str) -> None:

#TODO:
    """
    NOTES:
        Creating an abstraction for tasks to be handled.}
        if restart occurs, webcron forget process -> you will have to restart the task
        This program was not meant to be used for extended periods on servers or machines

        Requirements:
            5. monitor the status of the process with a arg
            6. if arg is call small window will show with current status of the program
        New_Requirements:

        Controller:
            STATUS OPER:
                when was task scheduled
                how long has task been running
                when is the next time it will run
                action it is running
            PAUSE:
                Pauses the scheduler
            STOP:
                Stops the scheduler -> kills the process
    """

    if os.getuid() != 0:
        print("--you are not root--")
        exit(130)


    _interval_days:int = 0
    _interval_hours:int = 0
    if time_d != None:

        if "days" in time_d:
            _result = time_d.split("days")
            _interval_days = int(_result[0])
        elif "hr" in time_d:
            _result = time_d.split("hr")
            _interval_hours = int(_result[0])
        else:
            print("Invalid time input given: Null")
            exit(130)

    if args.stop:
        _stop_sock()

    if service == None or action == None:
        print("No Tasks were scheduled")
    else:
        job_handler(service, action, _interval_hours, _interval_days)


def job_handler(service: str, action: str, _interval_hours:int=0, _interval_days:int=0):
    """Used for handling job to the apscheduler"""
    _time_start = "TIME_SCHEDULED: " + str(datetime.datetime.now())

    print(_time_start)

    """FLOW:
        Main => job_handler(task: object) => apscheduler(does magic)"""

    scheduler.add_job(
        task, "interval", days=_interval_days, hours=_interval_hours, args=(service, action)
    )
    _sock_connect()
    scheduler.start()


def task(service, action) -> None:
    subprocess.run(
        f"sudo systemctl {action} {service}", shell=True
    )

def start_to_sock():
    pass
def _stop_sock():
    """
    Description:
        Create a socket => forward STOP message to PID.

    Where we left off. socket refuses connection.
    could not get succesful close
    """
    try:
        sock.connect('/tmp/cronboi')
        sendData = 0
        sock.sendall(sendData.encode('utf-8'))
        while True:
            data = sock.recv(10)
            if data.decode("utf-8") == 0:
                print("Closed successfully")
                break
            elif data.decode("utf-8") == 1:
                print("Unclean")
                break
    except Exception as err:
        print(err)
        print("something bad happened in stop_sock")
        sock.close()
    finally:
        sock.close()

def pause_to_sock():
    pass


def _sock_connect():
    """
        0: pass
        1: fail
    """
    if isfile('/tmp/cronboi'):
        os.remove('/tmp/cronboi')
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind('/tmp/cronboi')
    sock.listen(1)
    while True:
        connection, _ = sock.accept()
        while True:
            endData = connection.recv(10)
            if endData:
                connection.sendall(0)
                if endData.decode('utf-8') == 0:
                    break
                    exit(130)
                else:
                    connection.sendall(1)
                    break


if __name__ == "__main__":
    main(service, action, time_d)
