import time
import board
import busio
import digitalio
import sys
import json
import array
import max6675



spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D2)
try:
    sensor = max6675.MAX6675(spi, cs)
except RuntimeError as e:
    print(e)
    print("Unable to connect to the thermocouple sensor.")
    sys.exit(1)

oven = digitalio.DigitalInOut(board.D4)
oven.direction = digitalio.Direction.OUTPUT

def oven_control(enable=False):
    #board.D4
    oven.value = enable

check_temp = 100
print("This program will determine calibration settings ")
print("for your oven to use with the EZ Make Oven.\n\n")
for i in range(10):
    print("Calibration will start in %d seconds..." % (10-i))
    time.sleep(1)
print("Starting...")
print("Calibrating oven temperature to %d C" % check_temp)
finish = False
oven_control(True)
maxloop=300
counter = 0
while not finish:
    time.sleep(1)
    counter += 1
    current_temp = sensor.temperature
    print("%.02f C" % current_temp)
    if current_temp >= check_temp:
        finish = True
        oven_control(False)
    if counter >= maxloop:
        raise Exception("Oven not working or bad sensor")
#5 minutes of execution to determine what the lag time and lag temp are?
print("checking oven lag time and temperature")
finish = False
start_time = time.monotonic()
start_temp = sensor.temperature
last_temp = start_temp

while not finish:
    time.sleep(1)
    current_temp = sensor.temperature
    print(current_temp)
    if current_temp <= last_temp:
        finish = True
    last_temp = current_temp

lag_temp = last_temp - check_temp
lag_time = int(time.monotonic() - start_time)

print("** Calibration Results **")
print("Modify config.json with these values for your oven:")
print("calibrate_temp:", lag_temp)
print("calibrate_seconds:",lag_time)
with open("config.json", mode="r") as fpr:
        config = json.load(fpr)
        fpr.close()
    config["calibrate_temp"] = lag_temp
    config["calibrate_seconds"] = lag_time    
    with open("config.json", mode="w") as fpr:
        json.dump(config,fpr)
        fpr.close()
