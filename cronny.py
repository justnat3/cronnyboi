#!/bin/python3
"""
MIT License

Copyright (c) 2020 Nathan Reed

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


__author__ = "Nathan Reed"
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from pytz import utc
import subprocess
import argparse
import datetime
import socket
import os
import sys
import time

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

parser = argparse.ArgumentParser(prog="cronny", description="Schedule Tasks With Ease")
parser.add_argument("-t", help="Target Task to Schedule", type=str, required=False)

parser.add_argument(
    "-a",
    help="restart, stop, start, :: DO NOT USE Disable/Enable",
    type=str,
    required=False,
)

parser.add_argument("-d", help="date -> cronny time", type=str, required=False)

parser.add_argument(
    "--status", help="get schedular current status", action="store_true", required=False
)

parser.add_argument(
    "--stop", help="stops a given instance of cronny", type=str, required=False
)

parser.add_argument(
    "--pause",
    help="pauses all instances of cronny",
    action="store_true",
    required=False,
)
args = parser.parse_args()

service: str = args.t
action: str = args.a
timeDate: str = args.d
status: bool = args.status
stop: str = args.stop
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


def getServiceTable() -> dict:
    """Returns a dict with the ServiceTable information"""
    serviceDict = {}
    for i in os.scandir("/tmp"):
        if not i.name.startswith(".") and not i.is_dir():
            if i.name[0:3] == "sck":
                serviceActionStringSplit = i.name.split("_")
                serviceDict[serviceActionStringSplit[1]] = serviceActionStringSplit[2]
    return serviceDict


def showFormattedServiceTable(ServiceTable: dict) -> None:
    """
    Parameters:
        ServiceTable (dict): A dictionary of Services & Actions

    Returns:
        A Pretty printed formatted table of the ServiceTable
    """
    print("{:<18} {:<21}".format("service", "action"))
    print("{:<18} {:<21}".format("-------", "------"))
    for k, v in ServiceTable.items():
        service, action = k, v
        print("{:<18} {:<21} ".format(k, v))
    print("\n")


def captureArgs() -> None:
    """Purely meant to clean up the capture argument function in main."""
    if os.getuid() != 0:
        print("--you are not root--")
        exit(130)
    if stop:
        print("stopping")
        stopSock(stop)
    if status:
        ServiceTable = getServiceTable()
        showFormattedServiceTable(ServiceTable)
        sys.exit(130)


def getInterval(timeDate: str) -> dict:
    """
    Parametrs:
        timeDate (str): A representation of when the action was scheduled
    Returns:
        returnedInterval (dict): 2 items in the dictionary, hours && Days.

    """
    returnedInterval = {}
    intervalDays: int = 0
    intervalHours: int = 0
    if timeDate != None:
        if "days" in timeDate:
            _result = timeDate.split("days")
            intervalDays = int(_result[0])
            returnedInterval["days"] = intervalDays
        if "days" not in timeDate:
            returnedInterval["days"] = 0
        if "hr" in timeDate:
            _result = timeDate.split("hr")
            intervalDays = int(_result[0])
            returnedInterval["hours"] = intervalHours
        if "hr" not in timeDate:
            returnedInterval["hours"] = 0
    return returnedInterval


def main(service: str, action: str, timeDate: str) -> None:
    """
    Parameters:
        service  (str): A service name to give to the scheduler
        action   (str): A action to feed the scheduler on the service given
        timeDate (str): The time at which the action on the service should be scheduled
    Returns:
        Nothing this is where most of the functionality is called in the program.
    """
    captureArgs()
    intervalDict = getInterval(timeDate)
    intervalHours, intervalDays = intervalDict["hours"], intervalDict["days"]

    if (
        service == None or action == None
    ):  # Check if there was a service//service provided
        print("No Tasks were scheduled")
    else:
        jobHandler(service, action, intervalDays, intervalHours)


def jobHandler(
    service: str, action: str, intervalDays: int = 0, intervalHours: int = 0
) -> None:
    """
    Parameters:
        service        (str): service name provided
        action         (str): action for the service provided
        intervalDays   (int): time in days for the scheduler
        intervalHours  (int): time in hours for the scheduler
    Returns:
        Nothing. This is where the UNIX Domain socket is activated.
                 The Job Scheduler is called
    """
    _time_start = "TIME_SCHEDULED: " + str(datetime.datetime.now())

    scheduler.add_job(
        task, "interval", days=intervalDays, hours=intervalHours, args=(service, action)
    )
    scheduler.start()
    sockConnect(service, action, _time_start)


def task(service, action) -> None:
    """
    Parameters:
        service (str): ServiceName to be started
        action  (str): action to inact on the service
    Returns:
        Nothing. Starts a child process with the task requested.
    """
    ##TODO: Check to see if service exists in systemd
    subprocess.run(f"sudo systemctl {action} {service}", shell=True)


def stopSock(service: str) -> None:
    """
    Parameters:
        service (str): service name
    Returns:
        Nothing. This sends a byte string to the sockConnect method to a rogue process to stop the python process remote
    """
    ServiceTable = getServiceTable()
    for k in ServiceTable:
        if k == service:
            sockFile = f"sck_{service}_{ServiceTable[k]}"
            try:
                sock.connect(sockFile)
                sock.sendall(b"stop")
            except Exception as err:
                print(err)
                break
            finally:
                # os.remove(os.path.join('/tmp',sockFile))
                sock.close()
                sys.exit(0)
        break


def sockConnect(service: str, status: str, timeStarted: str) -> None:
    """
    Parameters:
        service     (str): the service name given
        status      (str): the status of the procedure
        timeStarted (str): The time at which this process started
    Returns:
        Nothing. This starts a linux domain socket for the controller to connect to later.
    """
    serviceName = f"sck_{service}_{status}"
    ServiceTable = getServiceTable()
    for k in ServiceTable:
        if k == service:
            print("This is already in the Service Table")
            sys.exit(1)
    sock.bind(os.path.join("/tmp", serviceName))
    sock.listen(6)
    print(timeStarted)
    while True:
        connection, clientAddress = sock.accept()
        try:
            while True:
                data = connection.recv(1024)
                if data == b"stop":
                    break
        finally:
            connection.close()
            sys.exit(0)
        time.sleep(5)


if __name__ == "__main__":
    main(service, action, timeDate)
    sys.exit(1)
