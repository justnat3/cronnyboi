#!/bin/python3
__author__ = "Nathan Reed"

"""
Scheduling tasks with ease, provides an abstraction from crontab, sync not async.
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from os.path import isfile as checkf
from enum import Enum
from pytz import utc
import subprocess
import argparse
import datetime
import os
import time

## Vars
parser = argparse.ArgumentParser(prog="webcron", description="Schedule Tasks With Ease")

parser.add_argument("-t", help="Target Task to Schedule", type=str, required=False)
parser.add_argument(
    "-a",
    help="restart, stop, start, :: DO NOT USE Disable/Enable",
    type=str,
    required=False,
)
parser.add_argument("-d", help="date -> webco time", type=str, required=False)
parser.add_argument(
    "--status", help="get schedular current status", nargs="?", required=False
)
parser.add_argument("--stop", help="stops all instances of webcron", required=False)
parser.add_argument("--pause", help="pauses all instances of webcron", required=False)
args = parser.parse_args()

Service_State: bool = False
service: str = args.t
action: str = args.a
time_d: str = args.d
status = args.status
stop = args.stop
pause = args.pause


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


class State(Enum):
    SHB_ACTIVE = 1
    SHB_SHUTDOWN = 2
    SHB_PAUSE = 3


def main(service: str, action: str, time_d: str) -> None:
    _interval_days:int = 0
    _interval_hours:int = 0

    if "days" in time_d:
        _result = time_d.split("days")
        _interval_days = int(_result[0])
    elif "hr" in time_d:
        _result = time_d.split("hr")
        _interval_hours = int(_result[0])
    else:
        print("Invalid time input given: Null")
        exit(130)


    """
    NOTES:
        Creating an abstraction for tasks to be handled.}
        if restart occurs, webcron forget process -> you will have to restart the task
        This program was not meant to be used for extended periods on servers or machines
    """

    # TODO:
    """
        Requirements:
            1. take target, action, interval
            2. parse target, action, interval
            3. add a job based on those three things
            4. start the job in a small process
            5. monitor the status of the process with a arg
            6. if arg is call small window will show with current status of the program
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

    # if the process does not exit this code is reachable
    # star the job handler
    job_handler(service, action, _interval_hours, _interval_days)


def job_handler(service: str, action: str, _interval_hours=0, _interval_days=0):
    """Used for handling job to the apscheduler"""
    _time_start = "TIME_SCHEDULED: " + str(datetime.datetime.now())

#    if _interval_hours != None:
#        print( "hours " + str(_interval_hours))
#    elif _interval_days != None:
#        print( "days " + str(_interval_days) )

    print(_time_start)
    """FLOW:
        Main => job_handler(task: object) => apscheduler(does magic)"""
    new_task = task(service, action)

    scheduler.add_job(
        new_task, "interval", days=_interval_days, hours=_interval_hours, args=(_interval_days,_interval_hours)
    )
    scheduler.add
    scheduler.start()

    while True:
        global status
        global pause
        global stop
        if status != None:
            print(_time_start)
            print(scheduler.status)
            status = None
        elif pause != None:
            scheduler.pause()
            pause = None
        elif stop != None:
            scheduler.stop()
            exit(130)
        time.sleep(4)


def task(service, action) -> None:
    subprocess.run(
        f"sudo systemctl {action} {service}", shell=True
    )


if __name__ == "__main__":
    main(service, action, time_d)
