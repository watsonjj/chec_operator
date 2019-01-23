import threading
from time import sleep, ctime, time
from datetime import datetime
from chec_operator.utils.enums import CameraState


class ObservingThread(threading.Thread):

    def __init__(self, parent_handler, timedelta, triggerdelta):
        print("Creating observation thread")
        self.parent_handler = parent_handler
        self.timedelta = timedelta
        self.triggerdelta = triggerdelta
        self.starttime = 0
        self.starttrigger = 0
        self.currenttimedelta = 0
        self.currenttriggerdelta = 0
        self.get_trigger = self.parent_handler.get_backplane_trigger_count

        super(ObservingThread, self).__init__()
        self._observation_interrupt = threading.Event()
        self.observation_reached_end = False
        self.running = False
        self.lock = threading.Lock()

    def _check_time(self):
        if self.timedelta:
            self.currenttimedelta = datetime.now() - self.starttime
            return self.currenttimedelta >= self.timedelta
        else:
            return False

    def _check_trigger(self):
        if self.triggerdelta:
            self.currenttriggerdelta = self.get_trigger() - self.starttrigger
            return self.currenttriggerdelta >= self.triggerdelta
        else:
            return False

    def observation_ended(self):
        return self._observation_interrupt.isSet()

    def interrupt_observation(self):
        if self.lock.acquire(False):
            print("[WARNING] Interrupting observation thread!")
            self._observation_interrupt.set()
            self.join()

    def run(self):
        self.running = True
        self.starttime = datetime.now()
        self.starttrigger = self.get_trigger()
        print("[INFO] Starting observation thread, "
              "start time = {}, timedelta = {} s, triggerdelta = {}"
              .format(ctime(time()), self.timedelta, self.triggerdelta))

        while not self.observation_ended():
            if self._check_time() or self._check_trigger():
                self._finish_run()
                break

        self.running = False
        print("Observation Ended")

    def _finish_run(self):
        if self.lock.acquire(False):
            print("[INFO] Observation thread complete, "
                  "end time = {}, duration = {}, triggers {} (end) {} (actual)"
                  .format(ctime(time()), self.currenttimedelta,
                          self.currenttriggerdelta,
                          self.get_trigger() - self.starttrigger))
            self.observation_reached_end = True
            self.parent_handler.go_to_state(CameraState.READY)

    def wait_for_end(self):
        self.join()
        print("Observation Ended")
