from chec_operator.camera_server.handler import TransitionError
from chec_operator.utils.enums import CameraState
from chec_operator.utils import filepaths


class RunHandler:
    def __init__(self, server_handler):
        self._server_handler = server_handler
        self._pulse_gen = server_handler._pulse_gen
        self.running = False

        self.runtype = None  # run type: can be ped, tf, flash, obs, other
        self.directory = "/d1/checM/Paris_March2017/"  # directory where files are stored
        self.fileformat = "tio"  # data file format
        self.watchersleep = 40000

        self.n_runs = None  # number of runs
        self.n_events = None  # number of events per run
        self.rate = None  # periodic rate per run
        self.vped = None  # vped values you want to set
        self.default_vped = 1050
        self.settings_path = filepaths.default_paths.gui_run_settings
        self.runnumber_path = filepaths.default_paths.runnumber
        self.run_path = filepaths.default_paths.run

        self._apply_settings()

    def _apply_settings(self):
        pass

    def _read_run_number(self):
        with open(self.runnumber_path, 'r') as file:
            run_number = int(file.readline()[10:])
        return run_number

    def _set_vped(self, vped):
        print("Setting vped to {}".format(vped))
        with open(self.settings_path, 'w') as f:
            f.write("M:*/F|ASIC0_Vped=%i\n" % vped)
            f.write("M:*/F|ASIC1_Vped=%i\n" % vped)
            f.write("M:*/F|ASIC2_Vped=%i\n" % vped)
            f.write("M:*/F|ASIC3_Vped=%i\n" % vped)

        # send config file path to CameraServer
        self._server_handler.set_settings_filepath(self.settings_path)

        # go to ready to apply these settings
        try:
            self._server_handler.apply_settings_files()
        except TransitionError:
            print("[WARNING] Not in READY, could not set vped to {}".format(vped))

    def _write_runcard(self):
        with open(self.run_path, 'w') as f:
            f.write("RunType=%s\n" % self.runtype)
            f.write("Directory=%s\n" % self.directory)
            f.write("FileFormat=%s\n" % self.fileformat)
            f.write("WatcherSleep=%i\n" % self.watchersleep)
            f.write("RunNumberFile=%s\n" % self.runnumber_path)

    def _begin_run(self, run_type='?'):
        run_number = self._read_run_number()

        print("[START] Run type: {}, Run number: {}".format(run_type, run_number))

        # send run config file path to CameraServer
        self._server_handler.set_run_filepath("%s" % self.run_path)

        seconds = self.n_events / self.rate
        self._server_handler.set_observation_time(seconds=seconds)

        # go to observing and start the run
        self._server_handler.go_to_state(CameraState.OBSERVING)

        # print("[FINISHED] pedestal (Run {})".format(run_number))