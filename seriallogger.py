from __future__ import print_function
import serial, time, io, datetime
from serial import Serial

addr = "/dev/ttyUSB0" ## serial port to read data from
baud = 115200 ## baud rate for instrument

ser = serial.Serial(
    port = addr,\
    baudrate = baud,\
    parity=serial.PARITY_NONE,\
    stopbits=serial.STOPBITS_ONE,\
    bytesize=serial.EIGHTBITS,\
    timeout=0)


print("Connected to: " + ser.portstr)

filename = input("Input File Name: ") + '.csv'
datafile = open(filename, 'w')

## this will store each line of data
seq = []

while True: 
    for i in ser.read():
        seq.append(chr(i)) ## convert from ACSII?
        #print(chr(i))
        joined_seq = ''.join(str(v) for v in seq) ## Make a string from array

        if chr(i) == '\n':
            datafile.write(str(datetime.datetime.now()) + ',' + joined_seq + " ") 
            print(str(datetime.datetime.now()) + ',' + joined_seq)
            seq = []
            break
datafile.close()
ser.close()