#!/usr/bin/python

import serial
from time import sleep



with serial.Serial('/dev/ttyUSB1', baudrate=115200, timeout=1) as ser:
    # for line in range(10):
    #     x = ser.readline()
    #     print(x)
    status_check_str = b':R00=1,2,1,\n'
    get_values_str = b':R50=1,2,1,\n'
    output_on_str = b':W10=1,2,1,\n'
    output_off_str = b':W10=1,0,0,\n'


    for n in range(100):
        ser.write(get_values_str)
        print(ser.readline())
        sleep(10)


    # ser.write(output_off_str)
    # for line in range(10):
    #     x = ser.readline()
    #     print(x)

    # print("sleeping 5")
    # time.sleep(5)
    # print("awake")
    # ser.write(output_on_str)
    # for line in range(10):
    #     x = ser.readline()
    #     print(x)



exit()
