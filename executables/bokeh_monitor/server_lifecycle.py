import argparse
from threading import Thread

from chec_operator.threads import monitor as monitor_thread


def on_server_loaded(server_context):
    description = 'Parser for thread creator'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-f', '--file', dest='monitor_path', action='store',
                        default=None, help='path to the monitor file')
    parser.add_argument('--ssh', dest='ssh', action='store',
                        default=None, help='connect to file via ssh')

    args = parser.parse_known_args()[0]

    t = Thread(target=monitor_thread.watch_monitor, args=(args.monitor_path,))
    t.setDaemon(True)
    t.start()
