from serial import Serial, SerialException
from threading import RLock


class PulseGeneratorCommunicator:
    def __init__(self):
        self.p = None
        self.active = None
        self.rate = None
        self.lock = RLock()

    def connect(self, name="/dev/pulsegen", baudrate=115200):
        with self.lock:
            print("Connecting to pulse generator")
            try:
                self.p = Serial(name, baudrate=baudrate)

                # some default settings for pulse generator
                self.p.write(b':SPUL:TRIG:MOD DIS\r\n')  # disables trigger mode
                self.p.readline()
                self.p.write(b':SPUL:MOD NORM\r\n')  # enables normal mode for periodic triggering
                self.p.readline()
                self.p.write(b':PULS1:OUTP:AMPL 4.0\r\n')  # set pulse amplitude to 3 V
                self.p.readline()
                self.p.write(b':PULS1:WIDT 2e-7\r\n')  # set pulse width tp 200 ns
                self.p.readline()
                self.p.write(b':PULS2:OUTP:AMPL 3.0\r\n')  # set pulse amplitude to 3 V
                self.p.readline()
                self.p.write(b':PULS2:WIDT 2e-5\r\n')  # set pulse width tp 200 ns
                self.p.readline()
                self.p.write(b':PULS3:STAT OFF\r\n')  # disables output of Channel C
                self.p.readline()
                self.p.write(b':PULS4:STAT OFF\r\n')  # disables output of Channel D
                self.p.readline()

                self.set_rate(10)
                self.deactivate()
            except SerialException:
                print("[ERROR] Connecting to the pulse generator failed")
                raise

    def activate(self):
        with self.lock:
            print("Activating pulse generator")
            if self.p:
                self.p.write(b':SPUL:STAT ON\r\n')  # set the pulse generator output to ON
                self.p.readline()
                self.active = True
            else:
                print("[WARNING] Pulse generator is not connected.")

    def deactivate(self):
        with self.lock:
            print("Deactivating pulse generator")
            if self.p:
                self.p.write(b':SPUL:STAT OFF\r\n')  # set the pulse generator output to OFF
                self.p.readline()
            else:
                print("[WARNING] Pulse generator is not connected.")
            self.active = False

    def set_rate(self, rate):
        with self.lock:
            print("Setting pulse generator rate to {}".format(rate))
            if self.p:
                self.p.write(b':SPUL:PER %f \r\n' % float(1. / rate))
                self.p.readline()
            else:
                print("[WARNING] Pulse generator is not connected.")
            self.rate = rate

    def setup_pedestal(self):
        with self.lock:
            print("Setting up pulse generator for pedestal")
            if self.p:
                # specific pulse generatore settings for pedestal run
                self.p.write(b'*IDN?\r\n')
                self.p.readline()
                self.p.write(b':SPUL:TRIG:MOD DIS\r\n')  # disables trigger mode
                self.p.readline()
                self.p.write(b':SPUL:MOD NORM\r\n')  # enables normal mode for periodic triggering
                self.p.readline()
                self.p.write(b':PULS1:OUTP:AMPL 4.0\r\n')  # set pulse amplitude to 3 V
                self.p.readline()
                self.p.write(b':PULS1:WIDT 2e-7\r\n')  # set pulse width tp 200 ns
                self.p.readline()
                self.p.write(b':PULS1:DEL 0\r\n')  # set pulse delay to 0 s
                self.p.readline()
                self.p.write(b':PULS1:STAT ON\r\n')  # enables output of Channel A
                self.p.readline()
                self.p.write(b':PULS2:STAT OFF\r\n')  # disables output of Channel B
                self.p.readline()
                self.p.write(b':PULS3:STAT OFF\r\n')  # disables output of Channel C
                self.p.readline()
                self.p.write(b':PULS4:STAT OFF\r\n')  # disables output of Channel D
                self.p.readline()
            else:
                print("[WARNING] Pulse generator is not connected.")

    def setup_transfer_function(self):
        with self.lock:
            print("Setting up pulse generator for transfer function")
            if self.p:
                self.p.write(b':PULS1:DEL 0\r\n')  # set pulse delay to 0 s
                self.p.readline()
                self.p.write(b':PULS1:STAT ON\r\n')  # enables output of Channel A
                self.p.readline()
                self.p.write(b':PULS2:STAT OFF\r\n')  # disables output of Channel B
                self.p.readline()
            else:
                print("[WARNING] Pulse generator is not connected.")