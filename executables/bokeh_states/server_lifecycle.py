import argparse
from threading import Thread, RLock
from chec_operator.threads import server as state_thread


def on_server_loaded(server_context):
    description = 'Parser for thread creator'
    parser = argparse.ArgumentParser(description=description)
    add = parser.add_argument
    add('--dummy', dest='dummy', action='store_true', default=False,
        help='create a dummy communicator (no connection to server)')

    args = parser.parse_known_args()[0]

    comm_lock = RLock()

    args = (args.dummy, comm_lock)
    t = Thread(target=state_thread.poll_state, args=args)
    t.setDaemon(True)
    t.start()
