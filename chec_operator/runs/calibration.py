from threading import Thread
from chec_operator.runs.handler import RunHandler
from chec_operator.utils.enums import OnOffState, CameraState


class PedestalRun(RunHandler):
    def _apply_settings(self):
        self.runtype = "ped"
        self.n_runs = 1
        self.n_events = 20000
        self.rate = 600

    def run(self):
        self.running = True
        self._server_handler.disable_gui_config()
        self._write_runcard()
        self._pulse_gen.setup_pedestal()
        self._pulse_gen.set_rate(self.rate)
        self._server_handler.set_data_sending_state(OnOffState.ON)
        self._server_handler.enable_external_trigger()
        self._set_vped(self.default_vped)

        t = Thread(target=self.run_thread)
        t.start()


    def run_thread(self):
        self._begin_run("PED")
        ot = self._server_handler.observing_thread
        ot.wait_for_end()
        if not ot.observation_reached_end:
            print("[WARNING] Pedestal Interrupted")
        self._server_handler.enable_gui_config()
        self.running = False


class TFRun(RunHandler):
    def _apply_settings(self):
        self.runtype = "tf"
        self.n_runs = 50
        self.n_events = 1000
        self.rate = 600
        self.vped = [800+i*40 for i in range(self.n_runs)]

    def run(self):
        self.running = True
        self._server_handler.disable_gui_config()
        self._write_runcard()
        self._pulse_gen.setup_transfer_function()
        self._pulse_gen.set_rate(self.rate)
        self._server_handler.set_data_sending_state(OnOffState.ON)
        self._server_handler.enable_external_trigger()

        t = Thread(target=self.run_thread)
        t.start()

    def run_thread(self):
        for v in self.vped:
            self._set_vped(v)
            self._begin_run("TF")
            ot = self._server_handler.observing_thread
            ot.wait_for_end()
            if not ot.observation_reached_end:
                print("[WARNING] Transfer Function Interrupted")
                break
        self._set_vped(self.default_vped)
        self._server_handler.enable_gui_config()
        self.running = False
