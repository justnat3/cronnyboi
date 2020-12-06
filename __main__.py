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
from apscheduler.schedulers.background import BackgroundScheduler
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
import base64

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

parser = argparse.ArgumentParser(prog="cronny", description="Schedule Tasks With Ease")

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
scheduler = BackgroundScheduler()
scheduler.configure(
    jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc
)


def main(action: str, timeDate: str) -> None:
    """
    Parameters:
        action   (str): A action to feed the scheduler
        timeDate (str): The time at which the action on the action should be scheduled
    Returns:
        Nothing this is where most of the functionality is called in the program.
    """
    captureArgs()
    intervalDict = getInterval(timeDate)
    print(intervalDict)
    sys.exit(130)
    checkActionExists(action)
    jobHandler(action, 0, 0)


def encodeActionNameBase32(action: str) -> str:
    """
    Parameters:
        action (str): jobe name to encode
    Returns:
        encodedAction (str): encoded for sockFile
    """
    return base64.b32encode(bytearray(action, "ascii"))


def decodeActionNameBase32(encodedAction: str) -> str:
    """
    Parameters:
        encodedAction (str): job name to be decoded
    Returns:
        decodedAction (str): decoded job name
    """
    return base64.b32decode(encodedAction)


def checkActionExists(action: str) -> bool:
    """
    Parameters:
        action    ( str  ): action string
        isSystemd  ( bool ): If using the systemctl syntax, checks to see if the action exists
    Returns:
        A boolean value representing if the action given exists for systemd to call an action on
    SideEffects:
        Program will exit if the program or serviceFile does not exist
    """

    isSystemd = False
    if action.__contains__("systemctl") or action.__contains__("service"):
        for i in os.scandir("/lib/systemd/system"):
            if not i.name.startswith(".") and not i.is_dir():
                if i.name == actionSplit[2] or i.name == f"{actionSplit[2]}.service":
                    return True
    elif action.__contains__("/") == True:
        splitAction = action.split("/")
        for i in os.scandir("/usr/bin"):
            if not i.name.startswith(".") and not i.is_dir():
                if i.name == splitAction[-1]:
                    return True
    else:
        print("Input must be a path")
        sys.exit(130)

    print("ERROR :: EOFunction was reached")
    sys.exit(130)


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
    # TODO: NEEDS UPDATED
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


#   Worst Solution ever
def getInterval(timeDate: str) -> dict:
    t0 = time.time()
    """
    Parametrs:
        timeDate (str): A representation of when the action was scheduled
    Returns:
        returnedInterval (dict): 2 items in the dictionary, hours && Days.

    """
    returnedInterval: dict = {}
    intervalDays: int = 0
    intervalHours: int = 0
    intervalMinutes: int = 0

    collectedStr: str = ""
    collectedInt: int = ""
    setInterval = []
    if timeDate != None:
        for i in timeDate:
            if i.isdigit():
                collectedInt += str(i)
            if not i.isdigit():
                collectedStr += str(i)
            if i == " " or i == timeDate[-1]:
                returnedInterval[collectedStr] = int(collectedInt)
                collectedInt: int = ""
                collectedStr: str = ""
            continue

    t1 = time.time()
    print((t1 - t0) * 1000)  # 0.6580ms
    return returnedInterval


def jobHandler(action: str) -> None:
    """
    Parameters:
        action          (str): action for the action provided
        intervalDays    (int): time in days for the scheduler
        intervalMinutes (int): time in minutes for the scheduler
        intervalHours   (int): time in hours for the scheduler
    Returns:
        Nothing. This is where the UNIX Domain socket is activated.
                 The Job Scheduler is called
    """
    _time_start = "TIME_SCHEDULED: " + str(datetime.datetime.now())

    checkActionExists(action)
    print(len(action))
    interval: dict = getInterval()

    scheduler.add_job(task, "interval", minutes=interval["minutes"], args=(action))
    scheduler.start()
    sockConnect(action, "run", _time_start)


def task(action, *args, **kwargs) -> None:
    """
    Parameters:
        action  (str): action to execute
    Returns:
        Nothing. Starts a child process with the task requested.
    """
    from shlex import quote

    subprocess.run(quote(f"sudo {action}"), shell=True)


def stopSock(encodeAction: str) -> None:
    """
    Parameters:
        action(str): action name
    Returns:
        Nothing. This sends a byte string to the sockConnect method to a rogue process to stop the python process remote
    """

    ServiceTable = getServiceTable()
    for k, action in ServiceTable:
        if k == encodedAction:
            sockFile = f"sck_{encodedAction}_{ServiceTable[action]}"
            try:
                sock.connect(sockFile)
                sock.sendall(b"stop")
            except Exception as err:
                print(err)
                break
            finally:
                os.remove(os.path.join("/tmp", sockFile))
                sock.close()
                sys.exit(0)
        break


def sockConnect(action: str, status: str, timeStarted: str) -> None:
    """
    Parameters:
        action      (str): the action name given
        status      (str): the status of the procedure
        timeStarted (str): The time at which this process started
    Returns:
        Nothing. This starts a linux domain socket for the controller to connect to later.
    """
    encodedAction = encodeActionNameBase32(action)
    sockFile = f"sck_{encodedAction}_{status}"
    ServiceTable = getServiceTable()
    for k in ServiceTable:
        if k == decodeActionNameBase32(action):
            print("This is already in the Service Table")
            sys.exit(1)
    sock.bind(os.path.join("/tmp", sockFile))
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
    main(action, timeDate)
    sys.exit(1)
