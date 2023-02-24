#!/usr/bin/python3
import serial
from time import sleep


while 1:
    sPort = '/dev/ttyUSB0'
    payloadW = [0x00,0x00,0x01,0x01,0xc0,0x74,0x0d,0x0a,0x00,0x00]

    s = serial.Serial(
        port = sPort,
        baudrate=9600,
        parity=serial.PARITY_MARK,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
    )
    s.write(serial.to_bytes(payloadW))
    #print("Woke up serial device")
    s.flush()
    s.close()
    sleep(1)


