from chec_operator.utils.enums import OnOffState, LowMedHighState, \
    GUITriggerSettings, CameraState, CameraTriggerSettings
from chec_operator.utils import filepaths
from os.path import dirname, realpath, join
from datetime import timedelta
from time import sleep
from chec_operator.threads.observation import ObservingThread


class ServerStatus:
    def __init__(self):
        self.state = None
        self.transitions = None
        self.hv = None
        self.flasher = None
        self.data_sending = None
        self.configpath = None
        self.monitorconfigpath = None
        self.settingspath = None
        self.runpath = None
        self.hvpath = None
        self.ledpath = None
        self.triggerpath = None
        self.hv_level = None
        self.gui_trigger = None
        self.camera_trigger = None


class TransitionError(RuntimeError):
    pass


class ServerHandler:
    def __init__(self, communicator, pulse_gen, lock):
        self.known_states = list(CameraState.__members__.values())
        self.known_filetypes = ['config', 'monitorconfig', 'trigger',
                                'settings', 'run', 'hv', 'led']

        self._communicator = communicator
        self._pulse_gen = pulse_gen
        self.lock = lock
        self._gui_config_update = False
        dir_ = dirname(realpath(__file__))
        self.gui_config_path = join(dir_, '../config/gui.cfg')
        self.server_status = None
        self.building_status = None

        self._observation_time_duration = timedelta(0)
        self._observation_trigger_duration = 0
        self.pulse_generator_active = False
        self.observing_thread = None

    def connect(self):
        with self.lock:
            self._communicator.connect()
            self.enable_gui_config()

    def disconnect(self):
        with self.lock:
            self._communicator.disconnect()
            self.disable_gui_config()

    def refresh(self):
        with self.lock:
            c = self._communicator
            if self._communicator.cs:
                self.building_status = ServerStatus()
                bs = self.building_status
                bs.state = c.get_current_state()
                bs.transitions = c.get_allowed_transitions()
                bs.hv = c.get_hv_status()
                bs.flasher = c.get_flasher_status()
                bs.data_sending = c.get_data_sending_status()
                bs.configpath = c.get_config_filepath()
                bs.monitorconfigpath = c.get_monitorconfig_filepath()
                bs.settingspath = c.get_settings_filepath()
                bs.runpath = c.get_run_filepath()
                bs.hvpath = c.get_hv_filepath()
                bs.ledpath = c.get_led_filepath()
                bs.triggerpath = c.get_trigger_filepath()
                bs.hv_level = self._refresh_hv_level(bs.hvpath)
                bs.gui_trigger = self._refresh_trigger(bs.triggerpath)
                bs.camera_trigger = c.get_trigger_type()
                self.server_status = self.building_status
                self._write_gui_config()
            elif self.server_status:
                self.building_status = ServerStatus()
                bs = self.building_status
                bs.state = CameraState.DISCONNECTED
                bs.transitions = []
                bs.hv = self.server_status.hv
                bs.flasher = self.server_status.flasher
                bs.data_sending = self.server_status.data_sending
                bs.configpath = self.server_status.configpath
                bs.monitorconfigpath = self.server_status.monitorconfigpath
                bs.settingspath = self.server_status.settingspath
                bs.runpath = self.server_status.runpath
                bs.hvpath = self.server_status.hvpath
                bs.ledpath = self.server_status.ledpath
                bs.triggerpath = self.server_status.triggerpath
                bs.hv_level = self._refresh_hv_level(bs.hvpath)
                bs.gui_trigger = self._refresh_trigger(bs.triggerpath)
                bs.camera_trigger = self.server_status.camera_trigger
                self.server_status = self.building_status
            else:
                self.building_status = ServerStatus()
                bs = self.building_status
                bs.state = CameraState.DISCONNECTED
                bs.transitions = []
                bs.hv = c.get_hv_status()
                bs.flasher = c.get_flasher_status()
                bs.data_sending = c.get_data_sending_status()
                bs.configpath = c.get_config_filepath()
                bs.monitorconfigpath = c.get_monitorconfig_filepath()
                bs.settingspath = c.get_settings_filepath()
                bs.runpath = c.get_run_filepath()
                bs.hvpath = c.get_hv_filepath()
                bs.ledpath = c.get_led_filepath()
                bs.triggerpath = c.get_trigger_filepath()
                bs.hv_level = self._refresh_hv_level(bs.hvpath)
                bs.gui_trigger = self._refresh_trigger(bs.triggerpath)
                bs.camera_trigger = c.get_trigger_type()
                self.server_status = self.building_status
            print(self.server_status.camera_trigger)
            print(self.get_observation_time())

    @staticmethod
    def _refresh_hv_level(fp):
        level = LowMedHighState.UNKNOWN
        if fp == filepaths.default_paths.hv_low:
            level = LowMedHighState.LOW
        elif fp == filepaths.default_paths.hv_medium:
            level = LowMedHighState.MEDIUM
        elif fp == filepaths.default_paths.hv_high:
            level = LowMedHighState.HIGH
        return level

    def _refresh_trigger(self, fp):
        level = GUITriggerSettings.UNKNOWN
        try:
            if fp == filepaths.default_paths.trigger_external:
                rate = self._pulse_gen.rate
                print("_refresh_trigger", rate)
                level = getattr(GUITriggerSettings, "EXTERNAL_{}Hz".format(rate))
            else:
                level = filepaths.default_paths.get_threshold_enum(fp)
        except AttributeError:
            pass
        return level

    def get_backplane_trigger_count(self):
        with self.lock:
            return self._communicator.get_backplane_trigger_count()

    def go_to_state(self, req_state):
        with self.lock:
            status = self.server_status
            try:
                print("Going to state: {}".format(req_state.name))
                if req_state not in self.known_states:
                    raise KeyError
                if req_state not in status.transitions:
                    raise ValueError
                if self.observing_thread:
                    self._interrupt_observation()
                self._communicator.go_to_state(req_state)
                if req_state == CameraState.OBSERVING:
                    self._begin_observation()
            except KeyError:
                print("Attempted transition to unknown state "
                      "refused: {}".format(req_state.name))
            except ValueError:
                print("Attempt to perfom restricted transition refused: "
                      "{} -> {}".format(status.state.name, req_state.name))
            if not self._communicator.get_current_state() == req_state:
                msg = ("[ERROR] State transition failed: {} -> {}"
                       .format(status.state.name, req_state.name))
                raise TransitionError(msg)

    def _begin_observation(self):
        with self.lock:
            time = self._observation_time_duration
            triggers = self._observation_trigger_duration
            ct = self.server_status.camera_trigger
            if ct == CameraTriggerSettings.EXTERNAL:
                self._pulse_gen.activate()
            if time or triggers:
                self.observing_thread = ObservingThread(self, time, triggers)
                self.observing_thread.start()

    def _interrupt_observation(self):
        self.observing_thread.interrupt_observation()
        self.observing_thread = None
        ct = self.server_status.camera_trigger
        if ct == CameraTriggerSettings.EXTERNAL:
            self._pulse_gen.deactivate()

    def apply_settings_files(self):
        with self.lock:
            status = self.server_status
            if not status.state == CameraState.READY:
                msg = "Must be in READY to apply settings"
                raise TransitionError(msg)
            self._communicator.go_to_state(CameraState.READY)

    def set_observation_time(self, seconds=0, minutes=0, hours=0):
        with self.lock:
            print("Setting observation time to {}h {}m {}s"
                  .format(hours, minutes, seconds))
            td = timedelta(seconds=seconds, minutes=minutes, hours=hours)
            # if not td == timedelta(0):
            self._observation_time_duration = td
            # else:
            #     self._observation_time_duration = None

    def set_observation_time_from_string(self, string):
        with self.lock:
            print("Setting observation time to {}".format(string))
            if string:
                td = timedelta(**{k: float(v) for k, v in
                                  zip(['hours', 'minutes', 'seconds'],
                                      string.split(':'))})
                self._observation_time_duration = td
            # else:
            #     self._observation_time_duration = None

    def get_observation_time(self):
        with self.lock:
            # if self._observation_time_duration:
            return str(self._observation_time_duration)
            # else:
            #     return ""

    def set_hv_state(self, req_state):
        with self.lock:
            if req_state == OnOffState.ON:
                self._communicator.hv_turn_on()
            elif req_state == OnOffState.OFF:
                self._communicator.hv_turn_off()

    def set_flasher_state(self, req_state):
        with self.lock:
            if req_state == OnOffState.ON:
                self._communicator.flasher_turn_on()
            elif req_state == OnOffState.OFF:
                self._communicator.flasher_turn_off()

    def set_data_sending_state(self, req_state):
        with self.lock:
            # self.go_to_state(CameraState.STANDBY)
            if req_state == OnOffState.ON:
                self._communicator.data_send_turn_on()
            elif req_state == OnOffState.OFF:
                self._communicator.data_send_turn_off()
            # self.go_to_state(CameraState.READY)

    def set_config_filepath(self, fp='', default=False):
        with self.lock:
            self._communicator.set_config_filepath(fp, default)

    def set_monitorconfig_filepath(self, fp='', default=False):
        with self.lock:
            self._communicator.set_monitorconfig_filepath(fp, default)

    def set_settings_filepath(self, fp='', default=False):
        with self.lock:
            self._communicator.set_settings_filepath(fp, default)

    def set_run_filepath(self, fp='', default=False):
        with self.lock:
            self._communicator.set_run_filepath(fp, default)

    def set_hv_filepath(self, fp='', default=False):
        with self.lock:
            self._communicator.set_hv_filepath(fp, default)

    def set_led_filepath(self, fp='', default=False):
        with self.lock:
            self._communicator.set_led_filepath(fp, default)

    def set_trigger_filepath(self, fp='', default=False):
        with self.lock:
            self._communicator.set_trigger_filepath(fp, default)

    def set_hv_level(self, level):
        with self.lock:
            print("Setting hv to: {}".format(level.name))
            if self._communicator.get_current_state() == CameraState.READY:
                if level == LowMedHighState.LOW:
                    self.set_hv_filepath(filepaths.default_paths.hv_low)
                elif level == LowMedHighState.MEDIUM:
                    self.set_hv_filepath(filepaths.default_paths.hv_medium)
                elif level == LowMedHighState.HIGH:
                    self.set_hv_filepath(filepaths.default_paths.hv_high)
            else:
                print("[WARNING] Cannot set hv, not in READY")

    def set_trigger(self, level):
        with self.lock:
            print("Setting trigger to: {}".format(level.name))
            if self._communicator.get_current_state() == CameraState.READY:
                dp = filepaths.default_paths
                if level == GUITriggerSettings.EXTERNAL_10Hz:
                    self.enable_external_trigger()
                    self._pulse_gen.set_rate(10)
                elif level == GUITriggerSettings.EXTERNAL_50Hz:
                    self.enable_external_trigger()
                    self._pulse_gen.set_rate(50)
                elif level == GUITriggerSettings.EXTERNAL_300Hz:
                    self.enable_external_trigger()
                    self._pulse_gen.set_rate(300)
                elif level == GUITriggerSettings.EXTERNAL_600Hz:
                    self.enable_external_trigger()
                    self._pulse_gen.set_rate(600)
                else:
                    try:
                        self.set_trigger_filepath(dp.get_threshold_file(level))
                        self.apply_settings_files()
                    except AttributeError:
                        pass
            else:
                print("[WARNING] Cannot set trigger, not in READY")

    def enable_external_trigger(self):
        fp = filepaths.default_paths.trigger_external
        with open(fp, 'w') as f:
            f.write("BP|TriggerType=0\n")
        self.set_trigger_filepath(fp)
        self.apply_settings_files()

    def _write_gui_config(self):
        with self.lock:
            if self._gui_config_update:
                with open(self.gui_config_path, 'w') as f:
                    ss = self.server_status
                    f.write("config {}\n".format(ss.configpath))
                    f.write("monitorconfig {}\n".format(ss.monitorconfigpath))
                    f.write("trigger {}\n".format(ss.gui_trigger))
                    f.write("triggerfile {}\n".format(ss.triggerpath))
                    f.write("settings {}\n".format(ss.settingspath))
                    f.write("run {}\n".format(ss.runpath))
                    f.write("hv {}\n".format(ss.hvpath))
                    f.write("led {}\n".format(ss.ledpath))
                    f.write("obstime {}\n".format(self.get_observation_time()))

    def _read_gui_config(self):
        with self.lock:
            if self._gui_config_update:
                print("Loading gui config: {}".format(self.gui_config_path))
                try:
                    with open(self.gui_config_path, 'r') as f:
                        for line in f.readlines():
                            l = line.strip().replace('\n', '').split(" ")
                            type_ = l[0]
                            try:
                                val = l[1]
                            except IndexError:
                                val = ''
                            if type_ == 'config':
                                self.set_config_filepath(val)
                            elif type_ == 'monitorconfig':
                                self.set_monitorconfig_filepath(val)
                            elif type_ == 'triggerfile':
                                self.set_trigger_filepath(val)
                                self._refresh_trigger(val)
                            elif type_ == 'settings':
                                self.set_settings_filepath(val)
                            elif type_ == 'run':
                                self.set_run_filepath(val)
                            elif type_ == 'hv':
                                self.set_hv_filepath(val)
                            elif type_ == 'led':
                                self.set_led_filepath(val)
                            elif type_ == 'obstime':
                                self.set_observation_time_from_string(val)
                except FileNotFoundError:
                    pass

    def enable_gui_config(self):
        with self.lock:
            self._gui_config_update = True
            self._read_gui_config()

    def disable_gui_config(self):
        with self.lock:
            self._gui_config_update = False

    @staticmethod
    def get_description(state):
        case = {'off':
                """
                This is the state of the camera when powered off.
                """,
                'safe':
                """
                Initial state after the power-on (cold start-up of the
                Camera) and the state in which the Camera is during the
                day during normal operation.At the end of the night or
                during some emergency situation (e.g. strong wind,
                other telescope device problems that do not allow
                to use the telescope for observing) the camera must be
                in this state. In this state the health and safety
                function of the Camera are monitored. In case a
                power-off is needed the camera must be in Safe state.
                """,
                'standby':
                """
                In this state all subsystem are powered on (depends on camera
                type) and the camera reached the nominal temperature. After a
                cold start(e.g. after a power outage) this state can be
                reached after some time depending on the time need to cool
                the camera.
                """,
                'ready':
                """
                The camera is ready to be used for science data acquisition
                (lid is closed?). This is the normal waiting state. An
                external controller can ask to take data only if the camera
                is in ready state. Preset of the camera configuration for a
                particular kind or data taking can be donesending a non
                triggering event while the camera is in this state.
                """,
                'observing':
                """
                The camera is getting science data. Interleaved calibration
                data taking and special calibration data to be acquired at
                the beginning and at the end of the night are not triggering
                special external states. A purpose data taking flag and all
                will be send to the camera. After each run (ofany kind) the
                camera will automatically do a transition to ready. If there
                are problems during exposure the camera can do an automatic
                transition to FAULT state.
                """,
                'calibration':
                """
                The camera should enter in this state any time a calibration
                procedure involving also other telescope subsystems is
                requested. When in this state the Camera can perform actions
                that can be performed also in Ready or Observing.
                """,
                'maintenance':
                """
                The camera can be used in engineering mode. All the other
                states can be reached. The telescope cannot be used to acquire
                science data. This state is the only one that can be reached
                from the Fault state using a direct access to the camera
                engineering mode.
                """,
                'fault':
                """
                This is an automatic event triggered state at any time a
                severe internal error is raised (e.g. a subsystem is no more
                working, a power supply is out of order etc). To exit form
                fault state human intervention is needed. This also in the
                case an error can be automatically recoveredby an automatic
                procedure. The execution of a recovery procedure must be
                acknowledged by an operator. All recovery procedure must be
                executed while the Camera is in Maintenance state.
                The telescope hosting a camera in Fault/Maintenance state
                will be inoperable.
                """
                }
        return case[state]
