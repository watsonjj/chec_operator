from chec_operator.readers.monitor import MonitorReader
from time import sleep

MONITOR_CONTAINER = None


def watch_monitor(file):
    global MONITOR_CONTAINER
    reader = MonitorReader(file)
    while True:
        reader.refresh()
        MONITOR_CONTAINER = reader.container
        sleep(0.1)
