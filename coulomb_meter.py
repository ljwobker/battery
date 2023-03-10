#!/usr/bin/env python3

from prettytable import PrettyTable


class KgfR50:
    def __init__(self, input_bytestr) -> None:
        # decode to string
        self.reading = input_bytestr.decode().split(',')
        if not self.reading[0].startswith(':r50='):
            raise ValueError('reading string must begin with :r50')

        self.commaddr = int(self.reading[0].split('=')[1])  # comm address, commonly=1
        self.checksum = int(self.reading[1])                # CRC8 I think
        self.voltage = float(self.reading[2]) / 100         # volts
        self.current = float(self.reading[3]) / 100         # amperes
        self.cap_remain = float(self.reading[4]) / 1000     # amp-hours    
        self.cap_cumul = float(self.reading[5]) / 1000 # amp-hours
        self.watthours = float(self.reading[6]) / 100       # watt-hours
        self.runningtime = int(self.reading[7])             # seconds
        self.temp = int(self.reading[8]) - 100              # degrees C
        self.reported_power = float(self.reading[9]) / 100  # watts
        self.power = round(self.voltage * self.current, 3)  # watts
        self.output_status = int(self.reading[10])          # enum, 0=ON
        self.direction = int(self.reading[11])              # 0 is forward, 1 is reverse
        self.batterylife = int(self.reading[12])            # minutes
        self.resistance = float(self.reading[13]) / 100     # milli-Ohms
        self.terminator = str(self.reading[14])             # newline char(s)

    def asDict(self):
        outDict = {k:v for (k,v) in self.__dict__.items()}
        outDict.pop('commaddr')
        outDict.pop('checksum')
        outDict.pop('terminator')
        outDict.pop('reading')
        return outDict

    def asCSV(self, formats=False):
        formatMap = [
            ('volt',      '^5', self.voltage,       '2.2f'),
            ('curr',      '^5', self.current,       '2.2f'),
            ('Ah_rem', '^5', self.cap_remain,    '3.1f'),
            ('Ah_cum', '^5', self.cap_cumul,     '3.1f'),
            ('Wh',     '^5', self.watthours,     '3.1f'),
            ('run_t',  '^6', self.runningtime,   '5.1f'),
            # ('rep_pwr','^6', self.reported_power,'3.2f'),
            ('pwr',    '^6', self.power,         '3.2f'),
            ('outstat','^5', self.output_status, '2.2f'),
            ('dir',    '^3', self.direction,     '1.0f'),
            ('batlif', '^6', self.batterylife,   '3.0f'),
            ('resist', '^5', self.resistance,    '3.1f'),
        ]
        ptable = PrettyTable([v[0] for v in formatMap])
        ptable.add_row([v[2] for v in formatMap])
        ptable.align = 'r'
        ptable.border = False

        return str(ptable)





class KgfSettings:
    def __init__(self, input_bytestr) -> None:
        # decode to string
        self.reading = input_bytestr.decode().split(',')
        if not self.reading[0].startswith(':r51='):
            raise ValueError('reading string must begin with :r50')
        self.commaddr = int(self.reading[0].split('=')[1])  # comm address, commonly=1
        self.checksum = int(self.reading[1])                # CRC8 I think
        self.voltage = float(self.reading[2]) / 100         # volts

        


# sample_50 = b':r50=1,233,1349,19,90000,87862,122559,137818,79,0,0,1,0,30000,\r\n'
# sample_51 = b':r51=1,27,0,0,0,0,0,100,0,0,900,100,100,100,0,0,1,\r\n'
# reading = KgfR50(sample_50)

