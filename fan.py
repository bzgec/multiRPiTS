#! /usr/bin/env python3

import os
from time import sleep
import sys
import RPi.GPIO as GPIO

fanPin = 17
desiredTmp = 45
class PIDs:
	p = 45
	i = 15
	d = 30
	integral = 0
	delta_t = 3	# it means that every 3 seconds the program is going to check the temperature set the new speed of the fan
	previousValue = desiredTmp

def getCpuTmp():
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
	if PIDs.integral < 0:	# we do not want the integral to be negative, because we do not want the pi to be sad if it is under 45 degrees
		print('PIDs integral would be more negative (we do not want that)')
		PIDs.integral = 0
		I = 0
	else:
		PIDs.integral += error
		I = PIDs.i*PIDs.integral
		print('I: ' + str(I))
	derivate = (PIDs.previousValue - realValue)/PIDs.delta_t
	PIDs.previousValue = realValue
	D = PIDs.d*derivate
	print('D: ' + str(D))
	print('total: ' + str(P+I+D))
	return P + I + D
def fan(command):
	if command == 'on':
		GPIO.output(fanPin, 1)
		print('fan: ON')
	else:
		GPIO.output(fanPin,0)
		print('fan: OFF')
	return()
def handleFan():
	cpuTmp = float(getCpuTmp())
	dutyCycle = PIDcontroller(cpuTmp, desiredTmp)
	
	if dutyCycle > 100:
		dutyCycle = 100
	elif dutyCycle < 20:
		dutyCycle = 0
	#if dutyCycle == 100 or dutyCycle == 0:
	#	if dutyCycle == 100:
	#		fan('on')
	#	else:
	#		fan('off')
	#else:
	pwmFanPin.ChangeDutyCycle(dutyCycle)
	if dutyCycle == 0:
		fan('off')
	elif dutyCycle == 100:
		fan('on')
	print('dutyCycle: ' + str(dutyCycle))
	print('')
	return()
try:
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(fanPin,GPIO.OUT)
	pwmFanPin = GPIO.PWM(fanPin,50)	# frequency is 50Hz
	pwmFanPin.start(100)	# duty cicle is 50%
	while True:
		handleFan()
		sleep(PIDs.delta_t)	# goes to sleep for delta_t
except KeyboardInterrupt:	#CTRL+C = keyboard interrupt
	pwmFanPin.ChangeDutyCycle(0)
	print('KeyboardInterrupt')
	GPIO.cleanup() #resets all GPIO ports used by this program
