#!/usr/bin/python


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
        self.power = self.voltage * self.current            # watts
        self.output_status = int(self.reading[10])          # enum, 0=ON
        self.direction = int(self.reading[11])              # 0 is forward, 1 is reverse
        self.batterylife = int(self.reading[12])            # minutes
        self.resistance = float(self.reading[13]) / 100     # milli-Ohms
        self.terminator = str(self.reading[14])             # newline char(s)


class KgfSettings:
    def __init__(self, input_bytestr) -> None:
        # decode to string
        self.reading = input_bytestr.decode().split(',')
        if not self.reading[0].startswith(':r51='):
            raise ValueError('reading string must begin with :r50')
        self.commaddr = int(self.reading[0].split('=')[1])  # comm address, commonly=1
        self.checksum = int(self.reading[1])                # CRC8 I think
        self.voltage = float(self.reading[2]) / 100         # volts

        


sample_50 = b':r50=1,233,1349,19,90000,87862,122559,137818,79,0,0,1,0,30000,\r\n'
sample_51 = b':r51=1,27,0,0,0,0,0,100,0,0,900,100,100,100,0,0,1,\r\n'

reading = KgfR50(sample_50)
exit(0)
