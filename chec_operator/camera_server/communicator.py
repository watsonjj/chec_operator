from time import sleep, time
import subprocess
from chec_operator.utils import filepaths
from chec_operator.utils.enums import OnOffState, CameraState, \
    CameraTriggerSettings


class Communicator:
    def __init__(self):
        self.cs = None
        self.beginning = b'CS> '
        self.get_done = "done"
        self.set_done = "done"
        self.timeout = 10

    def readable(self, p, timeout):
        return not p.stdout.peek() == self.beginning
        t = time()+timeout
        while True:
            r = not p.stdout.peek() == self.beginning
            if r:
                return True
            if time() > t:
                return False

    def connect(self, ip='0.0.0.0', log_path=filepaths.default_paths.log):
        """
        Returns a subprocess with stdin as blocking pipe and stdout as
        non-blocking pipe.
        """
        if self.cs:
            print("[ERROR] Server already connected, disconnect first")
            return
        exe_path = filepaths.default_paths.exe
        print("Connecting to camera sever:")
        print("\t exe: {}".format(exe_path))
        print("\t ip: {}".format(ip))
        print("\t log: {}".format(log_path))
        cmd = "{} {} -f {} --trust\n".format(exe_path, ip, log_path)
        print(cmd)

        try:
            p = subprocess.Popen(cmd, shell=True,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
            while self.readable(p, 1):
                line = p.stdout.readline()
                print(line)
            print("here")
            self.cs = p
        except OSError:
            print("[ERROR] Invalid cmd for subprocess: {}".format(cmd))
            raise
        print("CONNECTED")

    def disconnect(self):
        if not self.cs:
            print("[ERROR] No server connected")
            return
        print("Disconnecting from camera server")
        self.cs.stdin.write(b"exit\n")
        self.cs.stdin.flush()
        # try:
        #     done = self.readline(self.cs, self.timeout).strip()
        #     if not done == self.done:
        #         raise ValueError
        # except TimeoutError:
        #     print("[WARNING] disconnect timeout")
        # except ValueError:
        #     print("[ERROR] disconnect incorrect done string")
        #     raise
        self.cs = None
        print("DISCONNECTED")

    def readline(self, p, timeout=1.0):
        """
        Reads a line from a process's stdout. Raises TimeoutError if no data
        was available within timeout seconds. Careful, this will hang
        if bytes are received within the given timeout, but no newline
        is encountered.
        """
        # if not self.readable(p, timeout):
        #     raise TimeoutError
        # else:
        line = p.stdout.readline().decode()
        # print("line:", line)
        # print(type(line))
        return line

    def _get(self, cmd):
        response = None
        if self.cs:
            # print("Sending cmd: {}".format(cmd))
            self.cs.stdin.write("{}\n".format(cmd).encode())
            self.cs.stdin.flush()
            try:
                line = self.readline(self.cs, self.timeout)
                response = line.replace(self.beginning.decode(), '').strip()
                done = self.readline(self.cs, self.timeout).strip()
                if self.get_done not in done:
                    raise ValueError
            except TimeoutError:
                print("[WARNING] {} timeout".format(cmd))
            except ValueError:
                print("[ERROR] {} unexpected readline response".format(cmd))
                raise
            # print("SUCCESS")
        return response

    def _set(self, cmd):
        if self.cs:
            print("Sending cmd: {}".format(cmd))
            self.cs.stdin.write("{}\n".format(cmd).encode())
            self.cs.stdin.flush()
            try:
                done = self.readline(self.cs, self.timeout).strip()
                print(done, self.set_done, self.set_done in done)
                if self.set_done not in done:
                    raise ValueError
            except TimeoutError:
                print("[WARNING] {} timeout".format(cmd))
            except ValueError:
                print("[ERROR] {} unexpected readline response".format(cmd))
                raise
            print("SUCCESS")
        else:
            print("[WARNING] No connection to camera server")

    def get_current_state(self):
        response = self._get('state')
        if response:
            state = CameraState[response.upper().split()[-1]]
        else:
            state = CameraState.UNKNOWN
        # print("Current camera state: {}".format(state))
        return state

    def get_allowed_transitions(self):
        response = self._get('transition')
        if response:
            transitions_str = response.lower().split()
            transitions = [CameraState[s.upper()] for s in transitions_str]
        else:
            transitions = []
        # print("Allowed state transitions: {}".format(transitions))
        return transitions

    def get_hv_status(self):
        response = self._get('hvch')
        if response:
            hv = OnOffState(int(response.split()[-1]))
        else:
            hv = OnOffState.MAYBEON
        # print("Current hv state: {}".format(hv.name))
        return hv

    def get_flasher_status(self):
        response = self._get('flch')
        if response:
            flasher = OnOffState(int(response.split()[-1]))
        else:
            flasher = OnOffState.MAYBEON
        # print("Current flasher state: {}".format(flasher.name))
        return flasher

    def get_data_sending_status(self):
        response = self._get('dach')
        if response:
            ds = OnOffState(int(response.split()[-1]))
        else:
            ds = OnOffState.MAYBEON
        # print("Current data sending state: {}".format(ds.name))
        return ds

    def get_config_filepath(self):
        response = self._get('getconfig')
        if response:
            fp = response.split()[-1]
        else:
            fp = ""
        # print("Current config filepath: {}".format(fp))
        return fp

    def get_monitorconfig_filepath(self):
        response = self._get('getmon')
        if response:
            fp = response.split()[-1]
        else:
            fp = ""
        # print("Current monitorconfig filepath: {}".format(fp))
        return fp

    def get_settings_filepath(self):
        response = self._get('getset')
        if response:
            fp = response.split()[-1]
        else:
            fp = ""
        # print("Current settings filepath: {}".format(fp))
        return fp

    def get_run_filepath(self):
        response = self._get('getrun')
        if response:
            fp = response.split()[-1]
        else:
            fp = ""
        # print("Current run filepath: {}".format(fp))
        return fp

    def get_hv_filepath(self):
        response = self._get('gethv')
        if response:
            fp = response.split()[-1]
        else:
            fp = ""
        # print("Current hv filepath: {}".format(fp))
        return fp

    def get_led_filepath(self):
        response = self._get('getled')
        if response:
            fp = response.split()[-1]
        else:
            fp = ""
        # print("Current hv filepath: {}".format(fp))
        return fp

    def get_trigger_filepath(self):
        response = self._get('gettrigger')
        if response:
            fp = response.split()[-1]
        else:
            fp = ""
        # print("Current trigger filepath: {}".format(fp))
        return fp

    def get_trigger_type(self):
        response = self._get('trch')
        if response:
            trigger = CameraTriggerSettings(int(response.split()[-1]))
        else:
            trigger = CameraTriggerSettings.UNKNOWN
        # print("Current hv state: {}".format(hv.name))
        return trigger

    def get_backplane_trigger_count(self):
        response = self._get('trch')
        if response:
            count = int(response.split()[-1])
        else:
            count = 0
        return count

    def go_to_state(self, state):
        self._set('to{}'.format(state.name.lower()))

    def hv_turn_on(self):
        self._set('hvon')

    def hv_turn_off(self):
        self._set('hvoff')

    def flasher_turn_on(self):
        self._set('enflasher')

    def flasher_turn_off(self):
        self._set('disflasher')

    def data_send_turn_on(self):
        self._set('daon')

    def data_send_turn_off(self):
        self._set('daoff')

    def set_config_filepath(self, fp='', default=False):
        cmd = 'configfile {}'.format(fp)
        if default:
            cmd = cmd.strip()
        self._set(cmd)

    def set_monitorconfig_filepath(self, fp='', default=False):
        cmd = 'monfile {}'.format(fp)
        if default:
            cmd = cmd.strip()
        self._set(cmd)

    def set_settings_filepath(self, fp='', default=False):
        cmd = 'setfile {}'.format(fp)
        if default:
            cmd = cmd.strip()
        self._set(cmd)

    def set_run_filepath(self, fp='', default=False):
        cmd = 'runfile {}'.format(fp)
        if default:
            cmd = cmd.strip()
        self._set(cmd)

    def set_hv_filepath(self, fp='', default=False):
        cmd = 'hvfile {}'.format(fp)
        if default:
            cmd = cmd.strip()
        self._set(cmd)

    def set_led_filepath(self, fp='', default=False):
        cmd = 'ledfile {}'.format(fp)
        if default:
            cmd = cmd.strip()
        self._set(cmd)

    def set_trigger_filepath(self, fp='', default=False):
        cmd = 'trifile {}'.format(fp)
        if default:
            cmd = cmd.strip()
        self._set(cmd)


class DummyCommunicator:
    def __init__(self):
        print("Creating dummy communicator!")

        cs = CameraState
        self.allowed_transitions_dict = {
            cs.DISCONNECTED: [],
            cs.UNKNOWN: [cs.SAFE],
            cs.OFF: [cs.SAFE],
            cs.SAFE: [cs.STANDBY, cs.OFF],
            cs.STANDBY: [cs.READY, cs.MAINTENANCE, cs.SAFE, cs.STANDBY],
            cs.READY: [cs.OBSERVING, cs.CALIBRATION, cs.MAINTENANCE, cs.SAFE,
                       cs.READY],
            cs.OBSERVING: [cs.READY, cs.SAFE],
            cs.CALIBRATION: [cs.READY, cs.SAFE],
            cs.MAINTENANCE: [cs.READY, cs.SAFE],
            cs.FAULT: [cs.MAINTENANCE]
        }
        self.cs = None
        self.current_state = CameraState.READY#OFF
        self.hv_state = OnOffState.OFF
        self.flasher_state = OnOffState.OFF
        self.data_sending_state = OnOffState.OFF
        self.trigger_type = CameraTriggerSettings.INTERNAL
        self.backplane_trigger_count = 0

        self.default_config_filepath = '/path/to/config/file.config'
        self.default_monitorconfig_filepath = '/path/to/monitorconfig.config'
        self.default_settings_filepath = '/path/to/settings/file.config'
        self.default_run_filepath = '/path/to/run/file.config'
        self.default_hv_filepath = '/path/to/hv/file.config'
        self.default_led_filepath = '/path/to/led/file.config'
        self.default_trigger_filepath = '/path/to/trigger/file.config'

        self.config_filepath = self.default_config_filepath
        self.monitorconfig_filepath = self.default_monitorconfig_filepath
        self.settings_filepath = self.default_settings_filepath
        self.run_filepath = self.default_run_filepath
        self.hv_filepath = self.default_hv_filepath
        self.led_filepath = self.default_hv_filepath
        self.trigger_filepath = self.default_hv_filepath

    def connect(self, ip='0.0.0.0', log_path=filepaths.default_paths.log):
        if self.cs:
            print("[ERROR] Server already connected, disconnect first")
            return
        exe_path = filepaths.default_paths.exe
        print("Connecting to camera sever:")
        print("\t exe: {}".format(exe_path))
        print("\t ip: {}".format(ip))
        print("\t log: {}".format(log_path))
        self.cs = 'C'
        print("CONNECTED")

    def disconnect(self):
        if not self.cs:
            print("[ERROR] No server connected")
            return
        self.cs = None
        print("DISCONNECTED")

    def get_current_state(self):
        if self.cs:
            state = self.current_state
        else:
            state = CameraState.DISCONNECTED
        # print("Current camera state: {}".format(state))
        return state

    def get_allowed_transitions(self):
        transitions = []
        if self.cs:
            transitions = self.allowed_transitions_dict[self.current_state]
        # print("Allowed state transitions: {}".format(transitions))
        return transitions

    def get_hv_status(self):
        hv = OnOffState.MAYBEON
        if self.cs:
            hv = self.hv_state
        # print("Current hv state: {}".format(hv.name))
        return hv

    def get_flasher_status(self):
        flasher = OnOffState.MAYBEON
        if self.cs:
            flasher = self.flasher_state
        # print("Current flasher state: {}".format(flasher.name))
        return flasher

    def get_data_sending_status(self):
        data_sending = OnOffState.MAYBEON
        if self.cs:
            data_sending = self.data_sending_state
        # print("Current data sending state: {}".format(data_sending.name))
        return data_sending

    def get_config_filepath(self):
        fp = ""
        if self.cs:
            fp = self.config_filepath
        # print("Current config filepath: {}".format(fp))
        return fp

    def get_monitorconfig_filepath(self):
        fp = ""
        if self.cs:
            fp = self.monitorconfig_filepath
        # print("Current monitor filepath: {}".format(fp))
        return fp

    def get_settings_filepath(self):
        fp = ""
        if self.cs:
            fp = self.settings_filepath
        # print("Current settings filepath: {}".format(fp))
        return fp

    def get_run_filepath(self):
        fp = ""
        if self.cs:
            fp = self.run_filepath
        # print("Current run filepath: {}".format(fp))
        return fp

    def get_hv_filepath(self):
        fp = ""
        if self.cs:
            fp = self.hv_filepath
        # print("Current hv filepath: {}".format(fp))
        return fp

    def get_led_filepath(self):
        fp = ""
        if self.cs:
            fp = self.led_filepath
        # print("Current led filepath: {}".format(fp))
        return fp

    def get_trigger_filepath(self):
        fp = ""
        if self.cs:
            fp = self.trigger_filepath
        # print("Current trigger filepath: {}".format(fp))
        return fp

    def get_trigger_type(self):
        setting = CameraTriggerSettings.UNKNOWN
        if self.cs:
            setting = self.trigger_type
        return setting

    def get_backplane_trigger_count(self):
        self.backplane_trigger_count += 1
        return self.backplane_trigger_count

    def go_to_state(self, state):
        if self.cs:
            sleep(3)
            self.current_state = state
        else:
            print("[WARNING] No connection to camera server")

    def hv_turn_on(self):
        if self.cs:
            print("Turning hv ON")
            self.hv_state = OnOffState.ON
        else:
            print("[WARNING] No connection to camera server")

    def hv_turn_off(self):
        if self.cs:
            print("Turning hv OFF")
            self.hv_state = OnOffState.OFF
        else:
            print("[WARNING] No connection to camera server")

    def flasher_turn_on(self):
        if self.cs:
            print("Turning flasher ON")
            self.flasher_state = OnOffState.ON
        else:
            print("[WARNING] No connection to camera server")

    def flasher_turn_off(self):
        if self.cs:
            print("Turning flasher OFF")
            self.flasher_state = OnOffState.OFF
        else:
            print("[WARNING] No connection to camera server")

    def data_send_turn_on(self):
        if self.cs:
            print("Turning data sending ON")
            self.data_sending_state = OnOffState.ON
        else:
            print("[WARNING] No connection to camera server")

    def data_send_turn_off(self):
        if self.cs:
            print("Turning hv OFF")
            self.data_sending_state = OnOffState.OFF
        else:
            print("[WARNING] No connection to camera server")

    def set_config_filepath(self, fp='', default=False):
        if self.cs:
            if default:
                fp = self.default_config_filepath
            print("Setting config filepath: {}".format(fp))
            self.config_filepath = fp
        else:
            print("[WARNING] No connection to camera server")

    def set_monitorconfig_filepath(self, fp='', default=False):
        if self.cs:
            if default:
                fp = self.default_monitorconfig_filepath
            print("Setting monitorconfig filepath: {}".format(fp))
            self.monitorconfig_filepath = fp
        else:
            print("[WARNING] No connection to camera server")

    def set_settings_filepath(self, fp='', default=False):
        if self.cs:
            if default:
                fp = self.default_settings_filepath
            print("Setting settings filepath: {}".format(fp))
            self.settings_filepath = fp
        else:
            print("[WARNING] No connection to camera server")

    def set_run_filepath(self, fp='', default=False):
        if self.cs:
            if default:
                fp = self.default_run_filepath
            print("Setting run filepath: {}".format(fp))
            self.run_filepath = fp
        else:
            print("[WARNING] No connection to camera server")

    def set_hv_filepath(self, fp='', default=False):
        if self.cs:
            if default:
                fp = self.default_hv_filepath
            print("Setting hv filepath: {}".format(fp))
            self.hv_filepath = fp
        else:
            print("[WARNING] No connection to camera server")

    def set_led_filepath(self, fp='', default=False):
        if self.cs:
            if default:
                fp = self.default_led_filepath
            print("Setting led filepath: {}".format(fp))
            self.led_filepath = fp
        else:
            print("[WARNING] No connection to camera server")

    def set_trigger_filepath(self, fp='', default=False):
        if self.cs:
            if default:
                fp = self.default_trigger_filepath
            print("Setting trigger filepath: {}".format(fp))
            self.trigger_filepath = fp
            if "external" in fp.lower():
                self.trigger_type = CameraTriggerSettings.EXTERNAL
            elif "threshold" in fp.lower():
                self.trigger_type = CameraTriggerSettings.INTERNAL
        else:
            print("[WARNING] No connection to camera server")
