from os.path import expanduser, join, basename
from chec_operator.utils.enums import GUITriggerSettings


def shorten_path(path):
    user = expanduser('~')
    path = path.replace(user, '~')
    if len(path) > 40:
        start = path[0:20]
        middle = '...'
        # end = path[-20:]
        # path = start + middle + end
        end = path[-40:]
        path = middle + end
    return path


class DefaultPaths:
    def __init__(self):
        home = expanduser('~')
        self.ci_source_dir = join(home, "Software/CHECInterface/trunk")
        self.log_dir = join(home, "CameraLog")

    @property
    def exe(self):
        return join(self.ci_source_dir, "../build/control_cs")

    @property
    def log(self):
        return join(self.ci_source_dir, "log/camera_driver.log")

    # @property
    # def log(self):
    #     return join(self.log_dir, "camera_driver.log")

    @property
    def config(self):
        return join(self.ci_source_dir, "config/checM.cfg")

    @property
    def monitorconfig(self):
        return join(self.ci_source_dir, "config/monitor.cfg")

    @property
    def setting(self):
        return join(self.ci_source_dir, "config/setting.cfg")

    @property
    def run(self):
        return join(self.ci_source_dir, "config/GUIRunConfig.cfg")

    @property
    def gui_run_settings(self):
        return join(self.ci_source_dir, "config/GUIRunSetting.cfg")

    @property
    def runnumber(self):
        return join(self.ci_source_dir, "files/runnumber.dat")

    @property
    def hv_low(self):
        return join(self.ci_source_dir, "config/hv_setting/hvSetting_1.cfg")

    @property
    def hv_medium(self):
        return join(self.ci_source_dir, "config/hv_setting/hvSetting_2.cfg")

    @property
    def hv_high(self):
        return join(self.ci_source_dir, "config/hv_setting/hvSetting_3.cfg")

    @property
    def trigger_external(self):
        return join(self.ci_source_dir, "config/triggerthreshold_setting/gui_external.cfg")

    def get_threshold_file(self, enum):
        s = enum.name.lower()
        if 'low' in s:
            hv = '1'
        elif 'med' in s:
            hv = '2'
        elif 'high' in s:
            hv = '3'
        else:
            raise AttributeError
        level = s[s.rfind('_') + 1:]
        dir_ = join(self.ci_source_dir, "config/triggerthreshold_setting")
        return join(dir_, "thresholdSetting_hvSet-{}_{}.cfg".format(hv, level))

    def get_threshold_enum(self, fp):
        name = basename(fp)
        if 'hvSet-1' in name:
            hv = 'HVLOW'
        elif 'hvSet-2' in name:
            hv = 'HVMED'
        elif 'hvSet-3' in name:
            hv = 'HVHIGH'
        else:
            raise AttributeError
        level = name[name.rfind('_') + 1:name.rfind('.')]
        enum = 'INTERNAL_{}_{}'.format(hv, level)
        return getattr(GUITriggerSettings, enum)


default_paths = DefaultPaths()
