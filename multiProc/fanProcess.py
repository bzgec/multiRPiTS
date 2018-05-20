def fanProcessScript(fanProcessFlag, printFlag_fanProcess, lock_fanFile, fanQueue, fanArr):
	# info('fanProcess function')
	import os
	import subprocess
	from time import sleep, time
	import sys
	import RPi.GPIO as GPIO
	import datetime
	import json

	import variablesConfig

	if variablesConfig.xlsxwriter_flag:
		import xlsxwriter
		# Create an new Excel file and add a worksheet.
		workbook = xlsxwriter.Workbook('fanProc.xlsx')
		worksheet = workbook.add_worksheet('Sheet 1')


	print(__name__ + ' id: ' + str(os.getpid()))
	# print('process id:', os.getpid())

	if printFlag_fanProcess.value == False:
		sys.stdout = open(os.devnull, "w")	# suppress console output

	global desiredTemp
	desiredTemp = variablesConfig.fanScript_desiredTemp
	global dutyCycle

	class PIDs:
		# these are constants, terms
		P = variablesConfig.fanScript_P
		I = variablesConfig.fanScript_I
		D = variablesConfig.fanScript_D
		# these change evey time
		p = 0
		i = 0
		d = 0
		integral = 0
		timeBetween = 0
		previousValue = desiredTemp
		previousTime = time()
		currentTime = 0	# it is set before use

	def getCpuTemp():
		global cpuTemp
		#tempLine = subprocess.check_output('vcgencmd measure_temp', shell=True, universal_newlines=True)	# universal_newlines=True -> By default, this function will return the data as encoded bytes. The actual encoding of the output data may depend on the command being invoked, so the decoding to text will often need to be handled at the application level.
		#cpuTemp = (tempLine.replace('temp=','').replace("'C\n",""))
		#tempLine = subprocess.getoutput('vcgencmd measure_temp')	# if using python3
		tempLine = subprocess.check_output('vcgencmd measure_temp', shell=True)	# if using python
		cpuTemp = (tempLine.replace('temp=','').replace("'C",""))
		#print('CPU temperature: ' + temp)
		cpuTemp = convertToFloatPoint(float(cpuTemp))
		return ()
	def PIDcontroller(realValue, setPoint):
		print('realValue (CPU temperature): ' + str(realValue))
		print('setPoint: ' + str(setPoint))
		error = realValue - setPoint
		print('error/difference: {0:0.1}'.format(error))

		######################################################
		# CALCULATING P
		PIDs.p = convertToFloatPoint(PIDs.P*error)
		print('p: ' + str(PIDs.p))

		######################################################
		# CALCULATING I
		PIDs.integral += error	# only integral part needs next step, because it is remembered/sumed
		if PIDs.integral <= 0:	# PIDs integral would be more negative, meaning that we would like to heat up the CPU (we do not want that)
			PIDs.integral = 0
		if error < 0:	# if error is positive it means that we need integral part
			if abs(error) >= variablesConfig.fanScript_I_OFF:	# when there is high load on CPU cuted down suddenly then the integral part is really high 
				PIDs.integral = 0								# which plays the main role in setting the dutyCycle, so the dutyCycle would be on 100%
																# even if realValue would be smaller then setPoint
		PIDs.i = convertToFloatPoint(PIDs.I*PIDs.integral)
		print('i: ' + str(PIDs.i))
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
		PIDs.timeBetween = convertToFloatPoint( PIDs.currentTime - PIDs.previousTime )
		print('time since last PID regulation...:{0:0.2f}'.format(PIDs.timeBetween))
		if PIDs.timeBetween < 0.1:	# first time we do not want to use derivate part...
			PIDs.d = 0
			print('skipping derivate part...')
		else:
			derivate = (PIDs.previousValue - realValue)/(PIDs.timeBetween)
			PIDs.d = convertToFloatPoint(PIDs.D*derivate)
			print('d:' + str(PIDs.d))

		PIDs.previousValue = realValue
		PIDs.previousTime = PIDs.currentTime

		print('total pid: ' + format(PIDs.p+PIDs.i+PIDs.d, '.1f'))
		return ()
	def handleFan():
		global dutyCycle, cpuTemp, desiredTemp
		getCpuTemp()
		PIDcontroller(cpuTemp, desiredTemp)
		dutyCycle = PIDs.p + PIDs.i + PIDs.d

		if dutyCycle > 100:
			dutyCycle = 100
		elif dutyCycle < variablesConfig.fanScript_minFanSpeed:
			dutyCycle = 0

		pwmFanPin.ChangeDutyCycle(dutyCycle)

		print('dutyCycle: ' + str(dutyCycle))
		return()
	def convertToFloatPoint(variable):
		variable = float(format(variable, '.1f'))
		return variable


	GPIO.setmode(GPIO.BCM)
	GPIO.setup(variablesConfig.fanScript_fanPin,GPIO.OUT)
	pwmFanPin = GPIO.PWM(variablesConfig.fanScript_fanPin,50)	# frequency is 50Hz
	pwmFanPin.start(0)	# duty cicle is 100%
	# subprocess.Popen('python3 /home/pi/scripts/mailSender.py fanScript.py Program started: ' + datetime.datetime.today().strftime('%Y/%m/%d %H:%M:%S'), shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)	
	# os.system('python3 /home/pi/scripts/mailSender.py fanScript.py Program started: ' + datetime.datetime.today().strftime('%Y/%m/%d %H:%M:%S'))

	if variablesConfig.xlsxwriter_flag:
		row = 1
		print('writing first row')
		worksheet.write(0, 0, 'desiredTemp')
		worksheet.write(0, 1, 'cpuTemp')
		worksheet.write(0, 2, 'difference')
		worksheet.write(0, 3, 'dutyCycle')
		worksheet.write(0, 4, 'p')
		worksheet.write(0, 5, 'i')
		worksheet.write(0, 6, 'd')
		worksheet.write(0, 7, 'sum')
		worksheet.write(0, 8, 'timeBetween')

	try:
		while fanProcessFlag.value:
			runTime = time()
			handleFan()

			jsonString = json.JSONEncoder().encode({'desiredTemp':desiredTemp, 
													'cpuTemp':cpuTemp, 
													'differenceInTemp':convertToFloatPoint(cpuTemp-desiredTemp),
													'dutyCycle':dutyCycle,
													'p':PIDs.p,
													'i':PIDs.i,
													'd':PIDs.d,
													'pidsum':convertToFloatPoint(PIDs.p+PIDs.i+PIDs.d),
													'delta_t':PIDs.timeBetween
													})

			fanArr[0] = desiredTemp
			fanArr[1] = cpuTemp
			fanArr[2] = convertToFloatPoint(cpuTemp-desiredTemp)
			fanArr[3] = dutyCycle
			fanArr[4] = PIDs.p
			fanArr[5] = PIDs.i
			fanArr[6] = PIDs.d
			fanArr[7] = convertToFloatPoint(PIDs.p+PIDs.i+PIDs.d)
			fanArr[8] = PIDs.timeBetween

			# fanQueue.put([desiredTemp, cpuTemp, (cpuTemp-desiredTemp), dutyCycle, PIDs.p, PIDs.i, PIDs.d, (PIDs.p+PIDs.i+PIDs.d), PIDs.timeBetween])
			fanQueue.put([cpuTemp, dutyCycle])

			if variablesConfig.xlsxwriter_flag:
				if row < 1000:
					print('writing to file row: ' + str(row))
					column = 0
					worksheet.write_number(row, column, desiredTemp)
					column += 1
					worksheet.write_number(row, column, cpuTemp)
					column += 1
					worksheet.write_number(row, column, convertToFloatPoint(cpuTemp-desiredTemp))
					column += 1
					worksheet.write_number(row, column, dutyCycle)
					column += 1
					worksheet.write_number(row, column, PIDs.p)
					column += 1
					worksheet.write_number(row, column, PIDs.i)
					column += 1
					worksheet.write_number(row, column, PIDs.d)
					column += 1
					worksheet.write_number(row, column, convertToFloatPoint(PIDs.p+PIDs.i+PIDs.d))
					column += 1
					worksheet.write_number(row, column, PIDs.timeBetween)
					column += 1
				row+=1

			# file = open('/home/pi/logs/fanScript_DATA.log', 'w', os.O_NONBLOCK)	# os.O_NONBLOCK that two programs can read/write a file at the same time
			# file.write(jsonString)
			# file.flush()
			# file.close()

			lock_fanFile.acquire()
			with open('/home/pi/logs/process_fan_DATA.txt', 'w') as file:
				file.write(jsonString)
				# json.dump(jsonString, file)
			lock_fanFile.release()

			print('fanProcess: Runned for: {0:0.4}'.format(time()-runTime) + 's')
			print('fanProcess: Going to sleep for ' + str(variablesConfig.fanScript_sleepDuration) + 's\n')
			sleep(variablesConfig.fanScript_sleepDuration)	# goes to sleep for 

	except KeyboardInterrupt:	# CTRL+C
		print('KeyboardInterrupt')
	except:
		# this catches ALL other exceptions including errors.  
		# You won't get any error messages for debugging  
		# so only use it once your code is working  
		print ("Other error or exception occurred!")
	finally:  # program will run until it finishes, or a keyboard interrupt or other exception occurs. Whichever of these occurs, the "finally:" will run, cleaning up the GPIO ports on exit.
		print('Leaving fanProcess')
		pwmFanPin.ChangeDutyCycle(0)
		GPIO.cleanup() #resets all GPIO ports used by this program
		# sys.exit(1)
