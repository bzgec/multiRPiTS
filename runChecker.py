#! /usr/bin/python3

import sys
import subprocess
from time import sleep
import logging
import os.path

if not os.path.isfile('/home/pi/logs/runChecker.log'):
	if not os.path.isdir('/home/pi/logs'):
		os.makedirs('/home/pi/logs')
	file = open('/home/pi/logs/runChecker.log', 'w')
	file.close()

# set up logging to file
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%Y/%m/%d %H:%M:%S',
                    filename='/home/pi/logs/runChecker.log')

logging.warning('Program started')

try:
	while True:
		print('###################################')
		command = 'ps -ef | grep -v grep | grep multi.py'
		anwser = subprocess.getoutput(command)
		print(anwser)

		if anwser:
			print('Program is running.')
			#logging.info('multi.py is running.')
		else:
			print('Program is not running...')
			print('Starting: sudo python /home/pi/scripts/multiRPiTS.py disable')
			logging.warning('multi.py is NOT running, starting it again')
			process = subprocess.Popen('python /home/pi/scripts/multiRPiTS.py disable', shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)

		print('Going to sleep for 60s')
		print('')
		sleep(60)


except KeyboardInterrupt:	#CTRL+C
	print('KeyboardInterrupt')
	sys.exit(1)
