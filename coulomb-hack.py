#!/usr/bin/env python3

import serial
from time import sleep
from dotenv import load_dotenv
import os
import sys
from coulomb_meter import KgfR50
from batt_influx import InfluxClient
from time import sleep
import argparse




print("hi")

def writeToInflux(self, fluxClient):
    self.dataLock.acquire()
    
    for vMod in self.modules:
        mod_dict = self.asDict(vMod.moduleID)
        fields = {}
        for (k,v) in mod_dict.items():
            fields[k] = v

        reading_data = [{
            "measurement": "Battery_Data",
            "tags": {"moduleTag": str(mod_dict['moduleID'])},
            "fields": fields,
            }]

        fluxClient.write_data(reading_data)
    self.dataLock.release()

print("hi")

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--time_interval", type=int, default=10, help="seconds between subsequent runs")
    parser.add_argument("-n", "--num_runs", type=int, default=4, help="number of runs to execute")
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        # sys.exit(1)
    return parser.parse_args()
print("hi")

def getReading(cmdstring=b':R50=1,2,1,\n', dev='/dev/TTYUSB1'):
    with serial.Serial(dev, baudrate=115200, timeout=1) as ser:
        # for line in range(10):
        #     x = ser.readline()
        #     print(x)
        status_check_str = b':R00=1,2,1,\n'
        get_values_str = b':R50=1,2,1,\n'
        output_on_str = b':W10=1,2,1,\n'
        output_off_str = b':W10=1,0,0,\n'

        ser.write(cmdstring)
        reading = ser.readline()
        return reading

print("hi")

if __name__ == '__main__':
    print("hi")
    args = parseArgs()
    load_dotenv()
    token = os.getenv('IFDB_TOKEN')
    org = os.getenv('IFDB_ORG')
    bucket = os.getenv('IFDB_BUCKET')
    fluxClient = InfluxClient(token, org, bucket)


    run_num = 0
    while True:
        run_num += 1
        ## get_data
        reading = getReading()
        print(reading)
        if run_num < args.num_runs:
            sleep(args.time_interval)
        else:
            break

exit()
