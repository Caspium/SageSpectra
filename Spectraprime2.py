#!/usr/bin/python3

from picamera2 import Picamera2

from smbus import SMBus
import time
import os
import sys
import numpy as np
import io
from PIL import Image
import cv2

from csv import writer

from skimage.draw import disk
from skimage.draw import circle_perimeter

from adxl345 import ADXL345

import datetime

i2cbus = SMBus(1)
### LIGHT CONTROL ###
#Registers
MODE1 = 0x00
MODE2 = 0x01
PWM0 = 0x02
PWM1 = 0x03
PWM2 = 0x04
PWM3 = 0x05
PWM4 = 0x06
PWM5 = 0x07
PWM6 = 0x08
PWM7 = 0x09
GRPPWM = 0x0A
GRPFREQ = 0x0B
LEDOUT0 = 0x0C
LEDOUT1 = 0x0D

#Addresses
DRIVER1 = 0x40
DRIVER2 = 0x41
DRIVER3 = 0x42
DRIVER4 = 0x43
ALLCALL = 0x48

colorname = dict([(525,"525"), (590,"590"), (625,"625"), (680,"680"), (780,"780"), (810,"810"), (870,"870"), (930,"930")])
colorreg = dict([ (525,LEDOUT0), (590,LEDOUT0), (625,LEDOUT0), (680,LEDOUT0), (780,LEDOUT1), (810,LEDOUT1), (870,LEDOUT1), (930,LEDOUT1)])
colorregval = dict([(525,0x80), (590,0x20), (625,0x08), (680,0x02), (780,0x80), (810,0x20), (870,0x08), (930,0x02)])

class Light:
    def __init__(self, name, register_name, register_value):
        self.name = name
        self.register_name = register_name
        self.register_value = register_value

nm_525 = Light("525", LEDOUT0, 0x80)
nm_595 = Light("525", LEDOUT0, 0x80)
nm_625 = Light("525", LEDOUT0, 0x80)
nm_680 = Light("525", LEDOUT0, 0x80)
nm_780 = Light("525", LEDOUT0, 0x80)
nm_810 = Light("525", LEDOUT0, 0x80)
nm_870 = Light("525", LEDOUT0, 0x80)
nm_930 = Light("525", LEDOUT0, 0x80)



# initialize/reset the device
def initialize():
    i2cbus.write_byte_data(ALLCALL, MODE1, 0x01)

def color(wavelength):
    i2cbus.write_byte_data(ALLCALL, LEDOUT0, 0x00)
    i2cbus.write_byte_data(ALLCALL, LEDOUT1, 0x00)
    i2cbus.write_byte_data(ALLCALL,colorreg[wavelength], colorregval[wavelength])

def avgpxl(rgbarray, col):
    return np.average(rgbarray[Ycoords, Xcoords, col])

# Circle Specs
height = 1080
width = 1920
height_skew = 250
width_skew = 300
radius = 120
Ycoords, Xcoords = disk((height//2 + height_skew, width//2+width_skew), radius)
Y_outline, X_outline = circle_perimeter(height//2 + height_skew, width//2+width_skew, radius)

# ACCEL
adxl345 = ADXL345()


print("Initializing Ring")
initialize()
#brightnesses
ledbrightness = dict([(525,0xe6), (590,0xff), (625,0x9a), (680,0x8a), (780,0x10), (810,0x38), (870,0x3a), (930,0x80)])
pwmreg = dict([(525,PWM3), (590,PWM2), (625,PWM1), (680,PWM0), (780,PWM7), (810,PWM6), (870,PWM5), (930,PWM4)])
for wavelen,brightness in ledbrightness.items():
    i2cbus.write_byte_data(ALLCALL,pwmreg[wavelen], brightness)

print("Initializing Camera")
picam2 = Picamera2()
#picam2.still_configuration.main.format = "YUV420"
picam2.still_configuration.align()
picam2.configure("still")
picam2.set_controls({"ExposureTime": 1000, "AnalogueGain": 1.0, "AwbEnable": 0, "AeEnable": 0})
picam2.start()
time.sleep(1)

### ACTUAL TEST ###

## CAL

framedelay = 0.03
print("Frame delay:", framedelay)
# print("Generating Calibration Images")
# i = 0
# for wavelen,name in colorname.items():
#     color(wavelen)
#     time.sleep(framedelay)
#     array = picam2.capture_array("main")
#     if(i==0):
#         avg = avgpxl(picam2.capture_array("main"), 1)
#     else:
#         avg = avgpxl(picam2.capture_array("main"), 0)
#     print(name, ":", avg)
#     i+=1
#     array[Y_outline, X_outline] = [0,0,0]
#     array = Image.fromarray(array)
    
#     array.save(name + '_cal' + ".png")

testname = input("Input test nameE: ")
input("START PPG <enter>")

## PPG
fout = open(("DATA/" + testname + ".csv"), 'w')
writer = writer(fout)
start = time.perf_counter()
color(525)
now = 0
numpics = 0
while(now-start < 15):
    now = time.perf_counter()
    avg = avgpxl(picam2.capture_array("main"), 1)
    print(f"{now-start:.4f} , {avg:.5f}")
    axes = adxl345.get_axes(False)
    writer.writerow([(now-start), avg, axes['x'], axes['y'], axes['z']])
    numpics+=1
now = time.perf_counter()
print("FPS: ", (numpics/((now-start))))


input("START TEST <enter>")

# CYCLE
outputbuffer = [0,0,0,0,0,0,0,0]
writer.writerow(['time','525','590','625','680','780','810','870','930','x','y','z'])
try:
    while True:
        i = 0
        for wavelen, colorval in colorregval.items():
            color(wavelen)
            time.sleep(framedelay)
            if(i==0):
                avg = avgpxl(picam2.capture_array("main"), 1)
            else:
                avg = avgpxl(picam2.capture_array("main"), 0)
            outputbuffer[i] = avg
            i+=1
        axes = adxl345.get_axes(False)
        now = datetime.datetime.now()
        writer.writerow([str(datetime.datetime.now()), outputbuffer[0], outputbuffer[1], outputbuffer[2], outputbuffer[3], outputbuffer[4], outputbuffer[5], outputbuffer[6], outputbuffer[7], axes['x'], axes['y'], axes['z']])
        #print(f"{now-start:.4f} ", end='')
        print(outputbuffer)
except KeyboardInterrupt:
    pass

fout.close()