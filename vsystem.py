#!/usr/bin/python 

import crcmod
import serial, serial.rs485
import threading, logging, time
from decimal import *
import vcmd
import time
import datetime
import batt_influx
from dotenv import load_dotenv
import os
import argparse
import sys





logging.basicConfig(
     level=logging.INFO,
     format= '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
     datefmt='%H:%M:%S'
 )

def ph(b):
    r = ''
    for i in b:
        r += '%3.2X' % i
    return r


class vModule:
    '''
    Class to represent a U27-12XP Rev.2, at least to start.
    '''
    moduleUCVoltage = 0
    moduleVoltage = 0
    moduleTemp = 0
    cellVoltage = [0,0,0,0]
    cellTemp = [0,0,0,0]
    cellBalStatus = [0,0,0,0]
    hiCellT = 0
    hiCellV = 0
    loCellT = 0
    loCellV = 0
    soc = 0
    current = 0
    moduleID = 0
    softCMaxV = 3.800
    hardCMaxV = 3.900
    softCMinV = 3.000
    hardCMinV = 2.800

    softCMaxT = 60.00   # alarm
    hardCMaxT = 65.00   # shutdown
    hardCMinTD = -10.0  # shutdown
    hardCMinTC = 0      # shutdown
    softPCBMaxT = 80
    hardPCBMaxT = 85     # shutdown
    seriesPosition = 0
    stringID = 0

    def __init__(self,moduleID,seriesPosition,stringID):
        '''
        init..
        '''
        self.moduleID = moduleID
        self.seriesPosition = seriesPosition
        self.stringID = stringID

    @property
    def ok(self):
        maxv = max(self.cellVoltage)
        minv = min(self.cellVoltage)
        maxt = max(self.cellTemp)
        mint = max(self.cellTemp)
        if maxv < self.myMaxV and minv > self.myMinV and maxt < self.myMaxT and mint > self.myMinT:
            return True
        return False

    # @property
    # def maxV(self):
    #     return max(self.cellVoltage)

class vSystem:
    modules = []
    sModules = 0
    pStrings = 0
    serialPort = ''
    sthread = None
    crc = None # function.
    dataLock = threading.Lock()
    newModuleData = threading.Event()
    newSysData = threading.Event()

    # we start with hardware rs485.. self.wakeBMS will change it to software if hardware has problems.
    rsfunc = serial.Serial

    def send(self, b):
        buf = b + self.crc(b).to_bytes(2, byteorder='little') + b'\r\n'
        self.ser.write(buf)

    def __init__(self, seriesModules, parallelStrings, serialPort):
        self.sModules = seriesModules
        self.pStrings = parallelStrings
        self.serialPort = serialPort
        self.crc = crcmod.mkCrcFun(poly=0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
        mID = 0
        # if this is a 4s2p bank, then string 1 will have mod id's 1,2,3,4 and string 2 will be 5,6,7,8.
        for p in range(1, self.pStrings+1):
            for s in range(1,self.sModules+1):
                mID +=1
                self.modules.append(vModule(mID, s, p))

        self.sthread = threading.Thread(target=self.serialThread, daemon=True)
        self.sthread.start()

    def payload(self, b):
        p = b[:-4]
        if self.crc(p).to_bytes(2, byteorder='little') == b[-4:-2]:
            p = b[3:-4]
            n = 2

            return [int.from_bytes(p[i:i+n],'big') for i in range(0, len(p), n)]

    def runCmd(self,module,cmdNum):
        self.send(bytes([module.moduleID]) + (vcmd.cmds[cmdNum]['cmd']))
        seg = self.ser.read(vcmd.cmds[cmdNum]['rlen'])
        return self.payload(seg)

    def signed(self,i):
        # converts unsigned word to signed word.
        if i > 32768:
            return i - 65536
        return i

    def wakeBMS(self):
        # first, knock knock.
        # DING DING DING  open and send wake command at 9600 baud...
        try:
            with self.rsfunc(port=self.serialPort,
                             baudrate=9600,
                             bytesize=serial.EIGHTBITS,
                             parity=serial.PARITY_MARK,
                             stopbits=serial.STOPBITS_ONE,
                             timeout=.1,
                             xonxoff=False,
                             rtscts=False,
                             dsrdtr=False,
                             ) as ser:
                ser.rs485_mode = serial.rs485.RS485Settings()
                ser.write(vcmd.startBatteries)
                time.sleep(.1)
        except Exception as e:
            # Exception... hopefully it's because the serial port driver does not support the RS485 ioctl.
            # Let's try again using the software emulation:
            self.rsfunc = serial.rs485.RS485
            with self.rsfunc(port=self.serialPort,
                             baudrate=9600,
                             bytesize=serial.EIGHTBITS,
                             parity=serial.PARITY_MARK,
                             stopbits=serial.STOPBITS_ONE,
                             timeout=.1,
                             xonxoff=False,
                             rtscts=False,
                             dsrdtr=False,
                             ) as ser:
                ser.rs485_mode = serial.rs485.RS485Settings()
                ser.write(vcmd.startBatteries)
                time.sleep(.1)
                # If this exceptions out, it's probably due to a bad com port setting. We'll not trap it.

    def serialThread(self):
        self.wakeBMS()
        # next, we can start the real process.
        with self.rsfunc(port=self.serialPort,
                         baudrate=115200,
                         bytesize=serial.EIGHTBITS,
                         parity=serial.PARITY_MARK,
                         stopbits=serial.STOPBITS_ONE,
                         timeout=.2,
                         xonxoff=False,
                         rtscts=False,
                         dsrdtr=False,
                         ) as self.ser:
            self.ser.rs485_mode = serial.rs485.RS485Settings()
            m1 = Decimal('.1')
            m01 = Decimal('.01')
            m001 = Decimal('.001')

            # Core battery communication loop.
            while True:
                for module in self.modules:
                    # 1 get voltages..
                    p4 = self.runCmd(module,4)
                    # 2 get temperatures..
                    p5 = self.runCmd(module,5)
                    # 3 get SOC.
                    p10 = self.runCmd(module,10)
                    # 4 get module voltage
                    p12 = self.runCmd(module,12)
                    # get lock, we're going to set stuff.
                    self.dataLock.acquire(True)
                    try:
                        # 1 get voltages..
                        if p4 is not None:
                            module.cellVoltage = [Decimal(v) * m001 for v in p4[3:7]]
                            module.hiCellV = Decimal(p4[0]) * m001
                            module.loCellV = Decimal(p4[1]) * m001
                            module.moduleUCVoltage = Decimal(p4[2]) * m001
                        # 2 get temperatures..
                        if p5 is not None:
                            module.cellTemp = [Decimal(self.signed(t)) * m01 for t in p5[1:5]]
                            module.moduleTemp =Decimal(self.signed(p5[0])) * m01
                        # 3 get SOC.
                        if p10 is not None:
                            module.soc = Decimal(p10[0]) * m1
                        # 4 get module voltage
                        if p12 is not None:
                            module.current = Decimal(self.signed(p12[7])) * m01
                            module.moduleVoltage = Decimal(p12[9]) * m001
                            module.cellBalStatus = [not (p12[6] >> 8+x) & 1 for x in range(0,4)]
                    except Exception as e:
                        print(e)
                        self.dataLock.release()
                    self.dataLock.release()
                    # Trigger new module data event
                    self.newModuleData.set()
                # Trigger new system data event
                self.newSysData.set()

    def asDict(self, moduleID, formats=False) -> dict:
        """
        return the module reading values as a dict.  if formats=True, returns a tuple of the 
        values and a dictionary of the print formats for convenience.
        If formats = False, returns only the reading values dictionary.
        """
        mod = [m for m in self.modules if m.moduleVoltage > 1][0]  # find the matching moduleID
        keynames = ['moduleID','soc','moduleVoltage','moduleUCVoltage','sumCellVoltage','moduleTemp','current']        
        datafields = [mod.moduleID,mod.soc,mod.moduleVoltage,mod.moduleUCVoltage,sum(mod.cellVoltage),mod.moduleTemp,mod.current]
        print_fmts = ['2.0f','3.2f','2.2f','2.2f','2.2f','2.1f','2.2f']
        out_d = { k:v for (k,v) in zip(keynames, datafields) }
        out_fmts = { k:v for (k,v) in zip(keynames, print_fmts) }
        for cell in range(0,4):
            out_fmts[f'cellVoltage_{cell}'] = '1.2f'
            out_fmts[f'cellTemp_{cell}'] = '2.1f'
            out_fmts[f'Balancing_{cell}'] = '1.0f'
            out_d[f'cellVoltage_{cell}'] = mod.cellVoltage[cell]
            out_d[f'cellTemp_{cell}'] = mod.cellTemp[cell]
            if mod.cellBalStatus[cell]:   
                out_d[f'Balancing_{cell}'] = 1
            else:
                out_d[f'Balancing_{cell}'] = 0
        
        assert len(out_fmts) == len(out_d), f"values dict and print formats dict must be same length!"
        if formats:
            return(out_d, out_fmts)
        else:
            return(out_d)



    def printStats(self, format='text'):

        m = 0
        self.dataLock.acquire()

        if format == 'csv':
            for mod in [m for m in self.modules if m.moduleVoltage > 1]:
                outstr = []
                (val_strings, fmt_strings) = self.asDict(mod.moduleID, formats=True)
                for key in val_strings:
                    outstr.append(f'{val_strings[key]:{fmt_strings[key]}}')
                # outstr = ','.join( [f'{v:{f}}' for v,f in zip(val_strings, fmt_strings)]  )
                print(outstr)
            pass    

        
        if format == 'csv2':
            self.moduleReadings = {}
            for mod in self.modules:
                m += 1
                self.outrow = [time.time(),mod.moduleID,mod.soc,mod.moduleVoltage,mod.moduleUCVoltage,sum(mod.cellVoltage),mod.moduleTemp,mod.current]
                self.keynames = ['time','moduleID','soc','moduleVoltage','moduleUCVoltage','sumCellVoltage','moduleTemp','current']
                self.fmts = ['10.6f','2.0f','3.2f','2.2f','2.2f','2.2f','2.1f','2.2f']
                for cell in range(0,4):
                    self.outrow = self.outrow + [mod.cellVoltage[cell],mod.cellTemp[cell]]
                    if mod.cellBalStatus[cell]:
                        self.outrow.append(1)
                    else:
                        self.outrow.append(0)
                    self.fmts = self.fmts + ['1.2f','2.1f','1.0f']
                    self.keynames = self.keynames + [f'cellVoltage_{cell}', f'cellTemp_{cell}', f'Balancing_{cell}']
                self.outstr = ','.join( [f'{v:{f}}' for v,f in zip(self.outrow,self.fmts)]  )
                if (mod.moduleVoltage > 1):
                    print(','.join(self.keynames))
                    print(self.outstr)
                
                    self.moduleReadings[mod.moduleID] = {k:v for (k,v) in zip(self.keynames[2:], self.outrow[2:])}
                    self.moduleReadings[mod.moduleID]['time'] = time.time()
                    pass

        if format == 'text': 
            for module in self.modules:
                m += 1
                print('Module:%3d    %7.3fv - %7.3fv (%7.3fv)  %5.2fc  current: %5.2fa  SOC: %4.1f%%' % (module.moduleID,module.moduleVoltage,module.moduleUCVoltage,sum(module.cellVoltage),module.moduleTemp,module.current,module.soc))
                for cell in range(0,4):
                    cellLine = '      Cell %3d  %5.3fv  %5.2fc' % (cell+1+((m-1)*4), module.cellVoltage[cell],module.cellTemp[cell])
                    if module.cellBalStatus[cell] == 1:
                        cellLine += " (Balancing) "
                    print(cellLine)
    
        self.dataLock.release()




    def writeToInflux(self, fluxClient):
        #build a data point
        
        good_data = [{
            "measurement": "h2o_feet",
            "tags": {"location": "coyote_creek"},
            "fields": {"water_level": 1, "poop_amount": 'low'},
            # "time": 1,
            }]

        for mod in [self.asDict(n) for n in range(len(self.modules))]:
            fields = {}
            for (k,v) in mod.items():
                if isinstance(v, Decimal):
                    v = float(v)
                fields[k] = v

            my_data = [{
                "measurement": "Battery_Data",
                "tags": {"moduleTag": str(mod['moduleID'])},
                "fields": fields,

                # "time": 1,
                }]

        # fluxClient.write_data(my_data)




def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--time_interval", type=int, default=10, help="seconds between subsequent runs - default 30 sec")
    parser.add_argument("-n", "--num_runs", type=int, default=4, help="number of runs to execute")
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        # sys.exit(1)
    return parser.parse_args()





if __name__ == '__main__':
    args = parseArgs()
    sys = vSystem(1, 2, '/dev/ttyUSB0')
    load_dotenv()
    token = os.getenv('IFDB_TOKEN')
    org = os.getenv('IFDB_ORG')
    bucket = os.getenv('IFDB_BUCKET')
    fluxClient = batt_influx.InfluxClient(token, org, bucket)


    run_num = 0
    while True:
        run_num += 1
        sys.newSysData.wait()
        sys.newSysData.clear()
        sys.printStats(format='csv')
        sys.writeToInflux(fluxClient)
        if run_num < args.num_runs:
            time.sleep(args.time_interval)
        else:
            break


    
