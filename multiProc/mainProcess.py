#! /usr/bin/python
from multiprocessing import Process, Queue, Value, Lock, Array

import os
import subprocess
from time import sleep, time
import sys
import datetime

import logging
#import os.path

import variablesConfig

import fanProcess
import DHTProcess
import displayProcess
import uploadProcess

if not os.path.isfile('/home/pi/logs/multiProc_LOG.log'):
	if not os.path.isdir('/home/pi/logs'):
		os.makedirs('/home/pi/logs')
	file = open('/home/pi/logs/multiProc_LOG.log', 'w')
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
logger = setup_logger('defaultLogger', '/home/pi/logs/multiProc_LOG.log')
logger.warning('Program started')

# def info(title):
# 	print(title)
# 	print('module name:', __name__)
# 	print('parent process:', os.getppid())
# 	print('process id:', os.getpid())

def sendMail(processName, exitcode):
	string = 'python /home/pi/scripts/mailSender.py '
	string += 'mainProcess '
	string += 'Error: ' + processName + ' not running!"\n"'
	string += 'Exitcode: ' + str(exitcode) + '"\n"'
	string += 'Occurred at: ' + datetime.datetime.today().strftime('%Y/%m/%d %H:%M:%S')
	#print(string)
	os.system(string)	

if __name__ == '__main__':
	try:
		# info('main line')
		print(__name__ + ' id: ' + str(os.getpid()) + ' (PARENT of all processes)')
		printFlag_fanProcess = Value('i', variablesConfig.printFlag_fan)
		printFlag_DHTProcess = Value('i', variablesConfig.printFlag_DHT)
		printFlag_displayProcess = Value('i', variablesConfig.printFlag_display)
		printFlag_uploadProcess = Value('i', variablesConfig.printFlag_upload)

		lock_fanFile = Lock()
		fanProcessFlag = Value('i', True)
		fanQueue = Queue()
		fanArr = Array('d', [0,0,0,0,0,0,0,0,0])	# desiredTemp, cpuTemp, differenceInTemp, dutyCycle, p, i, d, pidsum, delta_t
		p_fanProcess = Process(target=fanProcess.fanProcessScript, args=(fanProcessFlag, printFlag_fanProcess, lock_fanFile, fanQueue, fanArr))
		p_fanProcess.start()

		lock_DHTFile = Lock()
		DHTProcessFlag = Value('i', True)
		DHTQueue = Queue()
		dhtArr = Array('d', [0,0,0])	# temperature, humidity, dhtErr
		p_DHTProcess = Process(target=DHTProcess.DHTProcessScript, args=(DHTProcessFlag, printFlag_DHTProcess, lock_DHTFile, DHTQueue, dhtArr))
		p_DHTProcess.start()

		displayProcessFlag = Value('i', True)
		p_displayProcess = Process(target=displayProcess.displayProcessScript, args=(displayProcessFlag, printFlag_displayProcess, dhtArr, fanArr))
		p_displayProcess.start()

		uploadProcessFlag = Value('i', True)
		p_uploadProcess = Process(target=uploadProcess.uploadProcessScript, args=(uploadProcessFlag, printFlag_uploadProcess, fanQueue, DHTQueue))
		p_uploadProcess.start()

		while True:
			runTime = time()
			# print(str(p_fanProcess) + ': ' + str(p_fanProcess.is_alive()) )
			# print(str(p_DHTProcess) + ': ' + str(p_DHTProcess.is_alive()) )
			# print(str(p_displayProcess) + ': ' + str(p_DHTProcess.is_alive()) )
			# print(str(p_uploadProcess) + ': ' + str(p_DHTProcess.is_alive()) )

			if ( p_fanProcess.is_alive() == False ):
				sendMail('p_fanProcess', p_fanProcess.exitcode)
				p_fanProcess = Process(target=fanProcess.fanProcessScript, args=(fanProcessFlag, printFlag_fanProcess, lock_fanFile, fanQueue, fanArr))
				p_fanProcess.start()
			if ( p_DHTProcess.is_alive() == False ):
				sendMail('p_DHTProcess', p_DHTProcess.exitcode)
				p_DHTProcess = Process(target=DHTProcess.DHTProcessScript, args=(DHTProcessFlag, printFlag_DHTProcess, lock_DHTFile, DHTQueue, dhtArr))
				p_DHTProcess.start()
			if ( p_displayProcess.is_alive() == False ):
				sendMail('p_displayProcess', p_displayProcess.exitcode)
				p_displayProcess = Process(target=displayProcess.displayProcessScript, args=(displayProcessFlag, printFlag_displayProcess, dhtArr, fanArr))
				p_displayProcess.start()
			if ( p_uploadProcess.is_alive() == False ):
				sendMail('p_uploadProcess', p_uploadProcess.exitcode)
				p_uploadProcess = Process(target=uploadProcess.uploadProcessScript, args=(uploadProcessFlag, printFlag_uploadProcess, fanQueue, DHTQueue))
				p_uploadProcess.start()

			if (variablesConfig.printFlag_main):
				print('mainProcess: Runned for: {0:0.4}'.format(time()-runTime) + 's')
				print('mainProcess: Going to sleep for ' + str(variablesConfig.checkIfAlive) + 's\n')
			sleep(variablesConfig.checkIfAlive)
		#p.join()

	except KeyboardInterrupt:	#CTRL+C = keyboard interrupt
		print('KeyboardInterrupt')
	except:
		# this catches ALL other exceptions including errors.  
		# You won't get any error messages for debugging  
		# so only use it once your code is working  
		print ("!!! Other error or exception occurred !!!")

	finally:
		print('Terminating processes')
		fanProcessFlag.value = False
		DHTProcessFlag.value = False
		displayProcessFlag.value = False
		uploadProcessFlag.value = False
		p_fanProcess.join()
		p_DHTProcess.join()
		p_displayProcess.join()
		p_uploadProcess.join()
		print('All terminated successfully')
		# p_fanProcess.terminate()
		# p_DHTProcess.terminate()
		# p_displayProcess.terminate()
		# p_uploadProcess.terminate()

		sys.exit(1)