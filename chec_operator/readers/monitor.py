from datetime import datetime, timedelta
from copy import deepcopy
import pandas as pd
import numpy as np


class MonitorContainer:
    def __init__(self, n_records):
        self.start_time = 0
        index = np.arange(n_records)
        columns = ['dt', 'measurement', 'component', 'value']
        self.df = pd.DataFrame(np.nan, index=index, columns=columns)

    def update(self, row):
        if not self.df['dt'].isnull().any():
            self.df.shift(-1)
        self.df.fillna(row, limit=1)


class MonitorReader:
    def __init__(self, path):
        self._path = None

        self.file = None
        self.lines = None
        self.container = None

        h = 12
        self.earliest_record = datetime.now() - timedelta(hours=h)
        self.max_records = h * 60 * 60

        self.building_container = MonitorContainer(self.max_records)

        self.path = path

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, val):
        self._path = val
        self.file = open(val, "r")
        self.init_file(self.file)

    def init_file(self, file):
        print("Initialising monitor file, ignoring entries before: {}"
              .format(self.earliest_record))
        lines = self.file.readlines()
        if lines:
            for line in lines:
                data = line.replace('\n', '').split(" ")
                try:
                    dt = datetime.strptime("{} {}".format(data[0], data[1]),
                                           "%Y-%m-%d %H:%M:%S:%f")
                    if dt < self.earliest_record:
                        continue
                    else:
                        self.parse_line(line)
                except IndexError:
                    pass
        print("Monitor file initialised")

    def parse_line(self, line):
        try:
            bc = self.building_container
            if 'Start Monitoring' in line:
                start = line.replace('\n', '').split(" ")
                sdt = datetime.strptime("{} {}".format(start[2], start[3]),
                                        "%Y-%m-%d %H:%M:%S:%f")
                bc.start_time = sdt
                return
            if 'Number of packets' in line:
                return
            if 'Monitoring Event Done' in line:
                self.container = deepcopy(bc)
                return
            data = line.replace('\n', '').split(" ")
            dt = datetime.strptime("{} {}".format(data[0], data[1]),
                                   "%Y-%m-%d %H:%M:%S:%f")
            type = data[2]
            if type == 'Temperature0':
                d = dict(dt=dt,
                         measurement='temperature',
                         component='TM{}_{}'.format(data[4], '0'),
                         value=float(data[5]))
                bc.update(d)
            elif type == 'Temperature1':
                d = dict(dt=dt,
                         measurement='temperature',
                         component='TM{}_{}'.format(data[4], '1'),
                         value=float(data[5]))
                bc.update(d)
            elif type == 'DACQ1':
                if data[3] == 'Temperature':
                    d = dict(dt=dt,
                             measurement='temperature',
                             component='DACQ1',
                             value=float(data[4]))
                    bc.update(d)
            elif type == 'DACQ2':
                if data[3] == 'Temperature':
                    d = dict(dt=dt,
                             measurement='temperature',
                             component='DACQ2',
                             value=float(data[4]))
                    bc.update(d)
            elif type == 'Chiller':
                if data[3] == 'GetAmbientTemperature':
                    d = dict(dt=dt,
                             measurement='temperature',
                             component='chiller_ambient',
                             value=float(data[4]))
                    bc.update(d)
                elif data[3] == 'GetWaterTemperature':
                    d = dict(dt=dt,
                             measurement='temperature',
                             component='chiller_water',
                             value=float(data[4]))
                    bc.update(d)
            elif type == 'SBSensor':
                if 'TMON_EX' in data[3]:
                    d = dict(dt=dt,
                             measurement='temperature',
                             component=data[3].replace('TMON_', ''),
                             value=float(data[4]))
                    bc.update(d)
        except ValueError:
            print("ValueError on following line:")
            print(line)
            return
        except IndexError:
            print("IndexError on following line:")
            print(line)
            return

    def refresh(self):
        # line = self.file.readline()
        # if line:
        #     self.parse_line(line)

        lines = self.file.readlines()
        if lines:
            for line in lines:
                self.parse_line(line)
