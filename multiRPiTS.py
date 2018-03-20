#! /usr/bin/env python3

import os
from time import sleep, time
import sys
import RPi.GPIO as GPIO
import httplib, urllib # open the link 
import Adafruit_DHT

import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


######################################################
# CONFIGURATION FOR DISPLAY
# Raspberry Pi pin configuration:
RST = 24
# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
disp.begin()
disp.clear()
disp.display()
# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
widthOLED = disp.width
heightOLED = disp.height
image = Image.new('1', (widthOLED, heightOLED))
# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)
# Draw a black filled box to clear the image.
draw.rectangle((0,0,widthOLED,heightOLED), outline=0, fill=0)
padding = 0
linePadding = 2
fontSize = 8
x = padding
y = padding
font = ImageFont.load_default()
#font = ImageFont.truetype('font1.otf', fontSize)
#font = ImageFont.truetype('font2.ttf', fontSize)
#font = ImageFont.truetype('font3.ttf', fontSize)

######################################################
# CONFIGURATION FOR DHT22
sensor = Adafruit_DHT.DHT22
# connected to GPIO2.
DHTpin = 27
temperatureDHT = 0
humidityDHT = 0

fanPin = 17

desiredTemp = 45
minFanSpeed = 30	# it is in %
sleepDuration = 3	# every 3 seconds the program is going to check the temperature set the new speed of the fan
dutyCycle = 0
temp = 0
tempSum = 0
dutyCycleSum = 0
measurements = 0

DHTTime = 10*60	# reads temperature and humidity every 10 minutes
uploadTime = 30*60	# uploads data to ThingSpeak every 30 minutes
lastDHTTime = 0
lastUploadTime = 0

class PIDs:
	p = 45
	i = 10
	d = 30
	integral = 0
	#delta_t = 3	# it means that every 3 seconds the program is going to check the temperature set the new speed of the fan
	previousValue = desiredTemp
	previousTime = time()
	currentTime = 0	# it is set before use

#postInterval = 60*10 # in seconds
#shouldUpload = 0

def getCpuTemp():
	global temp
	tempLine = os.popen('vcgencmd measure_temp').readline()
	temp = (tempLine.replace('temp=','').replace("'C\n",""))
	#print('CPU temperature: {0}'.format(temp))
	return temp
def PIDcontroller(realValue, setPoint):
	print('realValue: ' + str(realValue))
	print('setPoint: ' + str(setPoint))
	error = realValue - setPoint
	print('error: ' + str(error))

	######################################################
	# CALCULATING P
	P = PIDs.p*error
	print('P: ' + str(P))

	######################################################
	# CALCULATING I
	PIDs.integral += error	# only integral part needs next step, because it is remembered/sumed
	if PIDs.integral <= 0:	# PIDs integral would be more negative, meaning that we would like to heat up the CPU (we do not want that)
		PIDs.integral = 0
	I = PIDs.i*PIDs.integral
	print('I: ' + str(I))
		#if PIDs.integral <= 0 or error < -1:	# we do not want the integral to be negative, because we do not want the pi to be sad if it is under 45 degrees
	#	print('PIDs integral would be more negative, meaning that we would like to heat up the CPU (we do not want that)')
	#	PIDs.integral = 0
	#	I = 0
	#else:
	#	PIDs.integral += error
	#	I = PIDs.i*PIDs.integral
	#	print('I: ' + str(I))

	######################################################
	# CALCULATING D
	# first time it is going to be wrong...
	PIDs.currentTime = time()
	print('time since last PID regulation...:{0:0.2f}'.format(PIDs.currentTime - PIDs.previousTime))
	if PIDs.currentTime - PIDs.previousTime < 0.04:	# first time the difference is usually smaller than 0.04 (i usually got 0.01-0,02 but for safety lets take 0.04), and first time we do not want to use derivate part...
		D = 0
		print('skipping derivate part...')
	else:
		derivate = (PIDs.previousValue - realValue)/(PIDs.currentTime - PIDs.previousTime)
		D = PIDs.d*derivate
		print('D: {0:0.2f}'.format(D))

	PIDs.previousValue = realValue
	PIDs.previousTime = PIDs.currentTime

	print('total PID: {0:0.2f}'.format(P+I+D))
	return (P, I, D)
#def fan(command):
#	if command == 'on':
#		GPIO.output(fanPin, 1)
#		print('fan: ON')
#	else:
#		GPIO.output(fanPin,0)
#		print('fan: OFF')
#	return()
def handleFan():
	global dutyCycle, minFanSpeed
	cpuTemp = float(getCpuTemp())
	P, I, D = PIDcontroller(cpuTemp, desiredTemp)
	dutyCycle = P + I + D

	if dutyCycle > 100:
		dutyCycle = 100
	elif dutyCycle < minFanSpeed:
		dutyCycle = 0
	#if dutyCycle == 100 or dutyCycle == 0:
	#	if dutyCycle == 100:
	#		fan('on')
	#	else:
	#		fan('off')
	#else:
	pwmFanPin.ChangeDutyCycle(dutyCycle)
	#if dutyCycle == 0:
	#	fan('off')
	#elif dutyCycle == 100:
	#	fan('on')
	print('dutyCycle: {0:0.2f}'.format(dutyCycle))
	print('')
	return(cpuTemp, P, I, D)
def postToThingSpeak():
	global measurements, tempSum, dutyCycleSum, lastUploadTime, temperatureDHT, humidityDHT, currentTime


	print('Posting to thingspeak.com')
		
	#cpu_pc = psutil.cpu_percent()
	#mem_avail_mb = psutil.avail_phymem()/1000000
			
	params = urllib.urlencode({'field1': tempSum/measurements, 'field2': dutyCycleSum/measurements,'field3': temperatureDHT, 'field4': humidityDHT,'key':'VEC1JDXFY3OWD3CJ'})
	headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
	conn = httplib.HTTPConnection("api.thingspeak.com:80")
	print("average CPU temperature: {0:0.1f}*C, average dutyCycle: {1:0.1f}".format(tempSum/measurements, dutyCycleSum/measurements))
	print("Temperature: {0:0.1f}*C, Humidity: {1:0.1f}%").format(temperatureDHT, humidityDHT)
        
	try:
		conn.request("POST", "/update", params, headers)
		response = conn.getresponse()
		#print strftime("%a, %d %b %Y %H:%M:%S", localtime())
		data = response.read()
		print (response.status, response.reason)
		conn.close()
		print("Posted")
		#shouldUpload = 0
		tempSum = 0
		dutyCycleSum = 0
		measurements = 0
		lastUploadTime = currentTime
	except:
		print ("connection failed")
	return()
def getTempAndHumidity():
	global temperatureDHT, humidityDHT, x, y, currentTime, lastDHTTime
	# Try to grab a sensor reading.  Use the read_retry method which will retry up
	# to 15 times to get a sensor reading (waiting 2 seconds between each retry).
	humidityDHT, temperatureDHT = Adafruit_DHT.read_retry(sensor, DHTpin)

	# Note that sometimes you won't get a reading and
	# the results will be null (because Linux can't
	# guarantee the timing of calls to read the sensor).
	# If this happens try again!
	if humidityDHT is not None and temperatureDHT is not None:
		print('Temp: {0:0.1f}*C, Humidity: {1:0.1f}%'.format(temperatureDHT, humidityDHT))

	else:
		print('Failed to get reading. Try again!')
		draw.text((x, y),    'FAILED to read DHT',  font=font, fill=255)
	lastDHTTime = currentTime
	return()

try:
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(fanPin,GPIO.OUT)
	pwmFanPin = GPIO.PWM(fanPin,50)	# frequency is 50Hz
	pwmFanPin.start(0)	# duty cicle is 100%
	while True:
		currentTime = time()
		timeBetween = currentTime - PIDs.previousTime
		cpuTemp, P, I, D = handleFan()

		if measurements < 10:	# this is because when the raspberry boots up CPU is quite hot and after some cycles it should stabilize, we do not want the the boot CPU temperature displayed in Thing Speak graph
			tempSum += float(temp)
			dutyCycleSum += dutyCycle

		measurements += 1


		if currentTime-lastDHTTime >= DHTTime:
			getTempAndHumidity()
			# Display image.
			
		disp.clear()
		draw.rectangle((0,0,widthOLED,heightOLED), outline=0, fill=0)
		y = padding
		draw.text((x, y),    'D:{0:0.1f}, R:{1:0.1f}, {2:0.1f}'.format(desiredTemp, cpuTemp, cpuTemp-desiredTemp),  font=font, fill=255)
		y += fontSize + linePadding
		draw.text((x, y),    'P:{0:0.1f}'.format(P),  font=font, fill=255)
		y += fontSize + linePadding
		draw.text((x, y),    'I:{0:0.1f}, PID sum:{1:0.1f}'.format(I, P+I+D),  font=font, fill=255)
		y += fontSize + linePadding
		draw.text((x, y),    'D:{0:0.1f}, delta-t:{1:0.1f}'.format(D, timeBetween),  font=font, fill=255)
		y += fontSize + linePadding

		draw.text((x, heightOLED-2*(fontSize+linePadding)),    'TEMP: {0:0.1f}*C'.format(temperatureDHT),  font=font, fill=255)
		draw.text((x, heightOLED-(fontSize+linePadding)), 'Humidity: {0:0.1f}%'.format(humidityDHT), font=font, fill=255)

		if currentTime-lastUploadTime >= uploadTime:	
			postToThingSpeak()

		disp.image(image)
		disp.display()
		sleep(sleepDuration)	# goes to sleep for 
except KeyboardInterrupt:	#CTRL+C = keyboard interrupt
	pwmFanPin.ChangeDutyCycle(0)
	print('KeyboardInterrupt')
	disp.clear()
	draw.rectangle((0,0,widthOLED,heightOLED), outline=0, fill=0)
	x = 30
	y = 20
	draw.text((x, y),    'multiRPiTS.py',  font=font, fill=255)
	y += fontSize + linePadding
	draw.text((x, y), 'NOT RUNNING', font=font, fill=255)
	disp.image(image)
	disp.display()
	GPIO.cleanup() #resets all GPIO ports used by this program
