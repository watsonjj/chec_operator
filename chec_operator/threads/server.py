from chec_operator.camera_server.communicator import Communicator, DummyCommunicator
from chec_operator.peripherals.pulse_generator import PulseGeneratorCommunicator
from chec_operator.camera_server.handler import ServerHandler
from time import sleep

SERVER_HANDLER = None


def poll_state(dummy, lock):
    global SERVER_HANDLER
    pulse_gen = PulseGeneratorCommunicator()
    if dummy:
        communicator = DummyCommunicator()
    else:
        communicator = Communicator()
        pulse_gen.connect()

    SERVER_HANDLER = ServerHandler(communicator, pulse_gen, lock)
    while True:
        SERVER_HANDLER.refresh()
        sleep(1)
