"""
Sockets work
add named socket functionality 
add pause funcationity
"""

#!/bin/python3
__author__ = "Nathan Reed"

"""
Scheduling tasks with ease, provides an abstraction from crontab, sync not async.
"""
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
    "--status", help="get schedular current status", action='store_true', required=False
)
parser.add_argument("--stop", help="stops a given instance of cronny", type=str, required=False)
parser.add_argument("--pause", help="pauses all instances of cronny", action='store_true', required=False)
args = parser.parse_args()

service: str = args.t
action: str = args.a
time_d: str = args.d
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
    service_dict = {}
    for i in os.scandir('/tmp'):
        if not i.name.startswith('.') and not i.is_dir():
            if i.name[0:3] == 'sck':
                split_service_action = i.name.split('_')
                service_dict[split_service_action[1]] = split_service_action[2]
    return service_dict

def showFormattedServiceTable(ServiceTable: dict) -> None:
    print("\n")
    print("{:<18} {:<21}".format("service", "action"))
    print("{:<18} {:<21}".format("-------", "------"))
    for k,v in ServiceTable.items():
        service,action = k,v
        print("{:<18} {:<21} ".format(k,v))
    print("\n")

def captureArgs() -> None:
    if os.getuid() != 0:
        print("--you are not root--")
        exit(130)
    if stop:
        print("stopping")
        _stop_sock(stop)
    if status:
        ServiceTable = getServiceTable()
        showFormattedServiceTable(ServiceTable)
        sys.exit(130)
def getInterval(time_d: str) -> dict:
    """0th index is days - 1th index is hours"""
    returnedInterval = {}
    _interval_days:int = 0
    _interval_hours:int = 0
    if time_d != None:
        if "days" in time_d:
            _result = time_d.split("days")
            _interval_days = int(_result[0])
            returnedInterval["days"] = _interval_days
        if "days" not in time_d:
            returnedInterval["days"] = 0
        if "hr" in time_d:
            _result = time_d.split("hr")
            _interval_hours = int(_result[0])
            returnedInterval["hours"] = _interval_hours
        if "hr" not in time_d:
            returnedInterval["hours"] = 0
    return returnedInterval


def main(service: str, action: str, time_d: str) -> None:

    """
    NOTES:
        if restart occurs, cronny forget process -> you will have to restart the task
        This program was not meant to be used for extended periods on servers or machines
    """
    
    captureArgs()
    intervalDict = getInterval(time_d)
    _interval_hours, _interval_days = intervalDict["hours"], intervalDict["days"] 
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
    # task is a function
    scheduler.add_job(
        task, "interval", days=_interval_days, hours=_interval_hours, args=(service, action)
    )
    _sock_connect(service, action, _time_start)
    scheduler.start()


def task(service, action) -> None:
    subprocess.run(
        f"sudo systemctl {action} {service}", shell=True
    )


def _stop_sock(service: str):
    """
    Description:
        Create a socket => forward STOP message to PID.

    Where we left off. socket refuses connection.
    could not get succesful close
    """
    ServiceTable = getServiceTable()
    for k in ServiceTable:
        if k == service:
            sockFile = f"sck_{service}_{ServiceTable[k]}" 
            try:
                sock.connect(sockFile)
                sock.sendall(b'stop')
            except Exception as err:
                print(err)
                break
            finally:
                #os.remove(os.path.join('/tmp',sockFile))
                sock.close()
                sys.exit(0)
        break
        

def _sock_connect(service: str, status: str, timeStarted: str) -> None:
    service_name = f"sck_{service}_{status}"
    ServiceTable = getServiceTable()
    for k in ServiceTable:
        if k == service:
            print("This is already in the Service Table")
            sys.exit(1)
    sock.bind(os.path.join('/tmp',service_name ))
    sock.listen(6)
    while True:
        connection, client_address = sock.accept()
        try:
            while True:
                data = connection.recv(1024)
                if data == b'stop':
                    break
        finally:
            print(timeStarted)
            print('finally')
            connection.close()
            sys.exit(0)
        time.sleep(5)
if __name__ == "__main__":
    main(service, action, time_d)
    sys.exit(1)
