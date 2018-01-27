#! /usr/bin/env python3

import os
from time import sleep, time
import sys
import RPi.GPIO as GPIO
import httplib, urllib # open the link 
import Adafruit_DHT





sensor = Adafruit_DHT.DHT22
# Example using a Raspberry Pi with DHT sensor
# connected to GPIO2.
DHTpin = 2
fanPin = 17

desiredTmp = 45
sleepDuration = 3 # every 3 seconds the program is going to check the temperature set the new speed of the fan
dutyCycle = 0
tmp = 0
tmpSum = 0
dutyCycleSum = 0
measurements = 0

lastUploadTime = 0
class PIDs:
	p = 45
	i = 10
	d = 30
	integral = 0
	#delta_t = 3	# it means that every 3 seconds the program is going to check the temperature set the new speed of the fan
	previousValue = desiredTmp
	previousTime = time()
	currentTime = 0	# it is set before use

#postInterval = 60*10 # in seconds
#shouldUpload = 0

def getCpuTmp():
	global tmp
	tmpLine = os.popen('vcgencmd measure_temp').readline()
	tmp = (tmpLine.replace('temp=','').replace("'C\n",""))
	#print('CPU temperature: {0}'.format(tmp))
	return tmp
def PIDcontroller(realValue, setPoint):
	print('realValue: ' + str(realValue))
	print('setPoint: ' + str(setPoint))
	error = realValue - setPoint
	print('error: ' + str(error))

	P = PIDs.p*error
	print('P: ' + str(P))

	if PIDs.integral < 0 or error < -1:	# we do not want the integral to be negative, because we do not want the pi to be sad if it is under 45 degrees
		print('PIDs integral would be more negative (we do not want that)')
		PIDs.integral = 0
		I = 0
	else:
		PIDs.integral += error
		I = PIDs.i*PIDs.integral
		print('I: ' + str(I))

	# first time it is going to be wrong...
	PIDs.currentTime = time()
	print('difference:{0:0.2f}'.format(PIDs.currentTime - PIDs.previousTime))
	if PIDs.currentTime - PIDs.previousTime < 0.04:	# first time the difference is usually smaller than 0.04 (i usually got 0.01-0,02 but for safety lets take 0.04), and first time we do not want to use derivate part...
		D = 0
		print('skipping derivate part...')
	else:
		derivate = (PIDs.previousValue - realValue)/(PIDs.currentTime - PIDs.previousTime)
		D = PIDs.d*derivate
		print('D: {0:0.2f}'.format(D))
	PIDs.previousValue = realValue
	PIDs.previousTime = PIDs.currentTime

	print('total: {0:0.2f}'.format(P+I+D))
	return P + I + D
#def fan(command):
#	if command == 'on':
#		GPIO.output(fanPin, 1)
#		print('fan: ON')
#	else:
#		GPIO.output(fanPin,0)
#		print('fan: OFF')
#	return()
def handleFan():
	cpuTmp = float(getCpuTmp())
	global dutyCycle
	dutyCycle = PIDcontroller(cpuTmp, desiredTmp)
	
	if dutyCycle > 100:
		dutyCycle = 100
	elif dutyCycle < 30:
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
	return()
def postToThingSpeak():
	global measurements, tmpSum, dutyCycleSum, lastUploadTime, tmp, dutyCycle

	tmpSum += float(tmp)
	dutyCycleSum += dutyCycle
	measurements += 1

	currentTime = time()
	if currentTime-lastUploadTime >= 10*60:		# 10 minutes, time() return seconds
		# Try to grab a sensor reading.  Use the read_retry method which will retry up
		# to 15 times to get a sensor reading (waiting 2 seconds between each retry).
		humidityDHT, temperatureDHT = Adafruit_DHT.read_retry(sensor, DHTpin)

		# Note that sometimes you won't get a reading and
		# the results will be null (because Linux can't
		# guarantee the timing of calls to read the sensor).
		# If this happens try again!
		if humidityDHT is not None and temperatureDHT is not None:
			print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperatureDHT, humidityDHT))
		else:
			print('Failed to get reading. Try again!')
	
		print('Posting to thingspeak.com')
		
		#cpu_pc = psutil.cpu_percent()
		#mem_avail_mb = psutil.avail_phymem()/1000000
			
		params = urllib.urlencode({'field1': tmpSum/measurements, 'field2': dutyCycleSum/measurements,'field3': temperatureDHT, 'field4': humidityDHT,'key':'VEC1JDXFY3OWD3CJ'})
		headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
		conn = httplib.HTTPConnection("api.thingspeak.com:80")
		print("average CPU temperature: {0:0.1f}*C, average dutyCycle: {1:0.1f}".format(tmpSum/measurements, dutyCycleSum/measurements))
        
		try:
			conn.request("POST", "/update", params, headers)
			response = conn.getresponse()
			#print strftime("%a, %d %b %Y %H:%M:%S", localtime())
			data = response.read()
			print (response.status, response.reason)
			conn.close()
			print("Posted")
			#shouldUpload = 0
			tmpSum = 0
			dutyCycleSum = 0
			measurements = 0
			lastUploadTime = currentTime
		except:
			print ("connection failed")
	return()

try:
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(fanPin,GPIO.OUT)
	pwmFanPin = GPIO.PWM(fanPin,50)	# frequency is 50Hz
	pwmFanPin.start(0)	# duty cicle is 100%
	while True:
		handleFan()
		postToThingSpeak()
		sleep(sleepDuration)	# goes to sleep for 
except KeyboardInterrupt:	#CTRL+C = keyboard interrupt
	pwmFanPin.ChangeDutyCycle(0)
	print('KeyboardInterrupt')
	GPIO.cleanup() #resets all GPIO ports used by this program
