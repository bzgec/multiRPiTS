#! /usr/bin/python

import os
import subprocess
from time import sleep, time
import sys
import RPi.GPIO as GPIO
import urllib
import Adafruit_DHT

import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import logging
import os.path

if not os.path.isfile('/home/pi/logs/multiRPiTS.log'):
	if not os.path.isdir('/home/pi/logs'):
		os.makedirs('/home/pi/logs')
	file = open('/home/pi/logs/multiRPiTS.log', 'w')
	file.close()

for i in sys.argv:
	if i == 'disable':	# if you run this script and add argument "disable" (python multiRPiTS.py disable)
		sys.stdout = open(os.devnull, "w")	# suppress console output

formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', '%Y/%m/%d %H:%M:%S')
def setup_logger(loggerName, log_file, level=logging.INFO, fileMode='a'):
	handler = logging.FileHandler(log_file, fileMode)        
	handler.setFormatter(formatter)
	logger = logging.getLogger(loggerName)
	logger.setLevel(level)
	logger.addHandler(handler)
	return logger

# set up logging to file
logger = setup_logger('defaultLogger', '/home/pi/logs/multi.log')
logger.warning('Program started')



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

thingSpeak_WRITE_API_KEY = 'INPUT YOUR API KEY HERE'

DHTTime = 10*60	# reads temperature and humidity every 10 minutes
uploadTime = 30*60	# uploads data to ThingSpeak every 30 minutes
lastDHTTime = 0
lastUploadTime = 0

class PIDs:
	p = 45
	i = 10
	d = 30
	integral = 0
	previousValue = desiredTemp
	previousTime = time()
	currentTime = 0	# it is set before use

#postInterval = 60*10 # in seconds
#shouldUpload = 0

def getCpuTemp():
	global temp
	#tempLine = os.popen('vcgencmd measure_temp').readline()
	tempLine = subprocess.check_output('vcgencmd measure_temp', shell=True)
	temp = (tempLine.replace('temp=','').replace("'C\n",""))
	#print('CPU temperature: ' + temp)
	return temp
def PIDcontroller(realValue, setPoint):
	print('realValue (CPU temperature): ' + str(realValue))
	print('setPoint: ' + str(setPoint))
	error = realValue - setPoint
	print('error/difference: ' + str(error))

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
	return(cpuTemp, P, I, D)
def postToThingSpeak():
	global measurements, tempSum, dutyCycleSum, lastUploadTime, temperatureDHT, humidityDHT, currentTime
	averageCPUTemp = format(format(tempSum/measurements, '.1f'))
	averageFanSpeed = format(format(dutyCycleSum/measurements, '.1f'))
	logger.info('Posting to thingSpeak.com: ' + 'temperature=' + str(temperatureDHT) + ', humidity=' + str(humidityDHT) + ', averageCPUTemp=' + averageCPUTemp + ', averageFanSpeed=' + averageFanSpeed)
		

	print('###################################################')
	print('Posting to thingspeak.com')
		
	#cpu_pc = psutil.cpu_percent()
	#mem_avail_mb = psutil.avail_phymem()/1000000
			
	link = 'https://api.thingspeak.com/update?api_key='
	data = '&field1=' + averageCPUTemp + '&field2=' + averageFanSpeed + '&field3=' + str(temperatureDHT) + '&field4=' + str(humidityDHT)
	print('temperature=' + str(temperatureDHT) + ', humidity=' + str(humidityDHT) + ', averageCPUTemp=' + averageCPUTemp + ', averageFanSpeed=' + averageFanSpeed)

	try:
		f = urllib.urlopen(link + thingSpeak_WRITE_API_KEY + data)
		#f.read()
		#print(f)
		print("Posted")
		tempSum = 0
		dutyCycleSum = 0
		measurements = 0
		lastUploadTime = currentTime
	except:
		print ("connection failed")
		logger.warning('FAILED to post to ThingSpeak')

	print('###################################################')
	return()
def getTempAndHumidity():
	global temperatureDHT, humidityDHT, x, y, currentTime, lastDHTTime
	print('###################################################')
	print('Geting temperature and humidity')
	# Try to grab a sensor reading.  Use the read_retry method which will retry up
	# to 15 times to get a sensor reading (waiting 2 seconds between each retry).
	humidityDHT, temperatureDHT = Adafruit_DHT.read_retry(sensor, DHTpin)
	humidityDHT = float(format(humidityDHT, '.1f'))
	temperatureDHT = float(format(temperatureDHT, '.1f'))
	# Note that sometimes you won't get a reading and
	# the results will be null (because Linux can't
	# guarantee the timing of calls to read the sensor).
	# If this happens try again!
	if humidityDHT is not None and temperatureDHT is not None:
		print('Temp: ' + str(temperatureDHT) + '*C, Humidity: ' + str(humidityDHT))
		logger.info('Reading temperature: ' + 'temperature=' + str(temperatureDHT) + ', humidity=' + str(humidityDHT))
	else:
		print('Failed to get reading. Try again!')
		draw.text((x, y),    'FAILED to read DHT',  font=font, fill=255)
		logger.warning('Reading temperature&humidity FAILED trying adain')
		humidityDHT, temperatureDHT = Adafruit_DHT.read_retry(sensor, DHTpin)
		if humidityDHT is not None and temperatureDHT is not None:
			print('Temp: ' + str(temperatureDHT) + '*C, Humidity: ' + str(humidityDHT))
			logger.warning('Reading FOR SECOND TIME temperature: ' + 'temperature=' + str(temperatureDHT) + ', humidity=' + str(humidityDHT))
		else:
			print('Failed to get reading again...')
			draw.text((x, y),    'FAILED to read DHT',  font=font, fill=255)
	lastDHTTime = currentTime
	print('###################################################')
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


		tempSum += float(temp)
		dutyCycleSum += dutyCycle
		measurements += 1


		if currentTime-lastDHTTime >= DHTTime:
			getTempAndHumidity()

			
		disp.clear()
		draw.rectangle((0,0,widthOLED,heightOLED), outline=0, fill=0)
		y = padding
		draw.text((x, y),    'D:{0:0.1f}, R:{1:0.1f}, {2:0.1f}'.format(desiredTemp, cpuTemp, cpuTemp-desiredTemp),  font=font, fill=255)
		y += fontSize + linePadding
		draw.text((x, y),    'P:{0:0.1f}'.format(P),  font=font, fill=255)
		y += fontSize + linePadding
		draw.text((x, y),    'I:{0:0.1f}, PID sum:{1:0.1f}'.format(I, P+I+D),  font=font, fill=255)
		y += fontSize + linePadding
		draw.text((x, y),    'D:{0:0.1f}, delta_t:{1:0.1f}'.format(D, timeBetween),  font=font, fill=255)
		y += fontSize + linePadding

		draw.text((x, heightOLED-2*(fontSize+linePadding)),    'TEMP: {0:0.1f}*C'.format(temperatureDHT),  font=font, fill=255)
		draw.text((x, heightOLED-(fontSize+linePadding)), 'Humidity: {0:0.1f}%'.format(humidityDHT), font=font, fill=255)

		file = open('/home/pi/logs/dataMulti.log', 'w')
		file.write('desiredTemp=' +  format(desiredTemp, '.1f') + ', cpuTemp=' + format(cpuTemp) + ', differenceInTemp=' + format(cpuTemp-desiredTemp) + '\n')
		file.write('P=' + format(P, '.1f') + ', I=' + format(I, '.1f') + ', D=' + format(D, '.1f') + ', PIDsum='+ format(P+I+D, '.1f') + ', delta_t=' + format(timeBetween, '.1f') + '\n')
		file.write('temperature=' + str(temperatureDHT) + ', humidity=' + str(humidityDHT))
		file.close()

		if currentTime-lastUploadTime >= uploadTime:	
			postToThingSpeak()

		disp.image(image)
		disp.display()
		print('')
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
	sys.exit(1)
