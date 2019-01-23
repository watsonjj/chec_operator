from chec_operator.runs.handler import RunHandler
from serial import Serial

class LEDInternalRun(RunHandler):

    def _apply_settings(self):
        self.runtype = "led"
        self.n_runs = 1
        self.n_events = 100
        self.rate = 50
        self.vped = 1050
        self.led_delay = 75e-9
        self.led_settings = ["/home/cta/Software/CHECInterface/trunk/config/flasher_setting/unit1_led1.cfg" for i in range(n_runs)]
        self.hv_settings = ["/home/cta/Software/CHECInterface/trunk/config/hvSetting_1.cfg" for i in range(n_runs)]

        self.connect_pulse_generator()

    def run(self):

        # write run card
        f = open(self.run_path, 'w')
        f.write("RunType=%s\n" % self.runtype)
        f.write("Directory=%s\n" % self.directory)
        f.write("FileFormat=%s\n" % self.fileformat)
        f.write("WatcherSleep=%i\n" % self.watchersleep)
        f.write("RunNumberFile=%s\n" % self.runnumber_path)
        f.close()

        # specific pulse generatore settings for pedestal run
        self.p.write(b'*IDN?\r\n')
        self.p.radline()
        self.p.write(b':PULS1:STAT OFF\r\n')  # disables output of Channel A
        self.p.readline()
        self.p.write(b':PULS2:STAT OFF\r\n')  # disables output of Channel B
        self.p.readline()

        # get current global run number from files/runnumber.dat
        myfile = open(runnumber_path, 'r')
        run_number = int(myfile.readline()[10:])
        myfile.close()

        # enable data sending
        self._server_handler.data_send_turn_on()

        # write pedestal config file with internal trigger enabled
        f = open(filename, 'w')
        f.write("BP|TriggerType=1\n")
        f.write("M:*/F|ASIC0_Vped=%i\n" % vped)
        f.write("M:*/F|ASIC1_Vped=%i\n" % vped)
        f.write("M:*/F|ASIC2_Vped=%i\n" % vped)
        f.write("M:*/F|ASIC3_Vped=%i\n" % vped)
        f.close()

        # send config file path to CameraServer
        self._server_handler.set_settings_filepath("%s" % filename)
        
        # go to ready to apply these settings
        self._server_handler.go_to_state("ready")

        
        
        # send run config file path to CameraServer
        self._server_handler.set_run_filepath("%s" % self.run_path)
    
        # go to observing and start the run
        self._server_handler.go_to_state("observing")

        # switch on pulse generator
        self.p.write(b':SPUL:STAT ON\r\n')  # set the pulse generator output to ON
        self.p.readline()
        
        # wait for some time to get 20,000 events -> add progress bar

        time.sleep(float(n_events) / rate)

        # switch off pulse generator
        self.p.write(b':SPUL:STAT OFF\r\n')  # set the pulse generator output to OFF
        self.p.readline()

        # stop the run
        self._server_handler.go_to_state("ready")
