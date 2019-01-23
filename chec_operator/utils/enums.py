from enum import IntEnum


class CameraState(IntEnum):
    DISCONNECTED = 0
    UNKNOWN = 1
    OFF = 2
    SAFE = 3
    STANDBY = 4
    READY = 5
    OBSERVING = 6
    CALIBRATION = 7
    MAINTENANCE = 8
    FAULT = 9


class OnOffState(IntEnum):
    OFF = 0
    MAYBEON = -1
    ON = 1


class LowMedHighState(IntEnum):
    UNKNOWN = 0
    LOW = 1
    L = 1
    MED = 2
    MEDIUM = 2
    M = 2
    HIGH = 3
    H = 3


class GUITriggerSettings(IntEnum):
    UNKNOWN = 0
    EXTERNAL_10Hz = 1
    EXTERNAL_50Hz = 2
    EXTERNAL_300Hz = 3
    EXTERNAL_600Hz = 4
    INTERNAL_HVLOW_2pe = 5
    INTERNAL_HVLOW_5pe = 6
    INTERNAL_HVLOW_11pe = 7
    INTERNAL_HVLOW_78pe = 8
    INTERNAL_HVLOW_128pe = 9
    INTERNAL_HVLOW_178pe = 10
    INTERNAL_HVLOW_228pe = 11
    INTERNAL_HVMED_2pe = 12
    INTERNAL_HVMED_5pe = 13
    INTERNAL_HVMED_11pe = 14
    INTERNAL_HVMED_78pe = 15
    INTERNAL_HVMED_128pe = 16
    INTERNAL_HVMED_178pe = 17
    INTERNAL_HVMED_228pe = 18
    INTERNAL_HVHIGH_2pe = 19
    INTERNAL_HVHIGH_5pe = 20
    INTERNAL_HVHIGH_11pe = 21
    INTERNAL_HVHIGH_78pe = 22
    INTERNAL_HVHIGH_128pe = 23
    INTERNAL_HVHIGH_178pe = 24
    INTERNAL_HVHIGH_228pe = 25


class CameraTriggerSettings(IntEnum):
    UNKNOWN = -1
    EXTERNAL = 0
    INTERNAL = 1
