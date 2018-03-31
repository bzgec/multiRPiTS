#! /usr/bin/python3

import sys
import subprocess
from time import sleep

try:
	while True:
		print('###################################')
		command = 'ps -ef | grep -v grep | grep multi.py'
		anwser = subprocess.getoutput(command)
		print(anwser)

		if anwser:
			print('Program is running.')
		else:
			print('Program is not running...')
			print('Starting: python /home/pi/scripts/multi.py disable')
			process = subprocess.Popen('python /home/pi/scripts/multi.py disable', shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)

		print('Going to sleep for 60s')
		print('')
		sleep(60)


except KeyboardInterrupt:	#CTRL+C
	print('KeyboardInterrupt')
	sys.exit(1)
