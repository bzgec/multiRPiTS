#! /usr/bin/python
from __future__ import print_function

from multiprocessing import Process, Queue, Value, Lock, Array

import os
import subprocess
from time import sleep, time
import sys
import datetime

import logging
# import os.path

import variablesConfig

import fanProcess
import DHTProcess
import displayProcess
import uploadProcess

if not os.path.isfile(variablesConfig.path_log_file):
    if not os.path.isdir(variablesConfig.path_log_dir):
        os.makedirs(variablesConfig.path_log_dir)
    file = open(variablesConfig.path_log_file, 'w')
    file.close()

# checking what if command
for idx in range(len(sys.argv)):
    command = sys.argv[idx]
    if command == 'disablePipe':
        sys.stdout = open(os.devnull, "w")  # suppress console output


formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s', variablesConfig.dateFormat)


def setup_logger(loggerName, log_file, level=logging.INFO, fileMode='a'):
    handler = logging.FileHandler(log_file, fileMode)
    handler.setFormatter(formatter)
    logger = logging.getLogger(loggerName)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


# set up logging to file
logger = setup_logger('defaultLogger', variablesConfig.path_log_file)
logger.warning('Program started')

# def info(title):
# 	print(title)
# 	print('module name:', __name__)
# 	print('parent process:', os.getppid())
# 	print('process id:', os.getpid())


def sendMail(reciever, msg):
    string = 'python3 ' + variablesConfig.path_mailSender + \
        ' ' + reciever + ' ' + __file__ + ' '
    string += msg
    # print(string)
    subprocess.Popen(string, shell=True, stdout=subprocess.PIPE,
                     stdin=subprocess.PIPE, stderr=subprocess.STDOUT)


def sendMail_processNotRunning(processName, exitcode):
    string = 'Error: ' + processName + ' not running!"\n"'
    string += 'Exitcode: ' + str(exitcode) + '"\n"'
    string += 'Occurred at: ' + datetime.datetime.today().strftime(variablesConfig.dateFormat)
    # print(string)
    sendMail(variablesConfig.email_sendTo, string)

# def terminalCommand(command):
# subprocess.Popen( command, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)

if __name__ == '__main__':
    try:
        # info('main line')
        print(__name__ + ' id: ' + str(os.getpid()) +
              ' (PARENT of all processes)')
        printFlag_fanProcess = Value('i', variablesConfig.printFlag_fan)
        printFlag_DHTProcess = Value('i', variablesConfig.printFlag_DHT)
        printFlag_displayProcess = Value('i', variablesConfig.printFlag_display)
        printFlag_uploadProcess = Value('i', variablesConfig.printFlag_upload)

        lock_fanFile = Lock()
        fanProcessFlag = Value('i', True)
        fanQueue = Queue()
        # desiredTemp, cpuTemp, differenceInTemp, dutyCycle, p, i, d, pidsum, delta_t
        fanArr = Array('d', [0, 0, 0, 0, 0, 0, 0, 0, 0])
        p_fanProcess = Process(target=fanProcess.fanProcessScript, args=(
            fanProcessFlag, printFlag_fanProcess, lock_fanFile, fanQueue, fanArr))
        p_fanProcess.start()

        lock_DHTFile = Lock()
        DHTProcessFlag = Value('i', True)
        DHTQueue = Queue()
        dhtArr = Array('d', [0, 0, 0])  # temperature, humidity, dhtErr
        p_DHTProcess = Process(target=DHTProcess.DHTProcessScript, args=(
            DHTProcessFlag, printFlag_DHTProcess, lock_DHTFile, DHTQueue, dhtArr))
        p_DHTProcess.start()

        displayProcessFlag = Value('i', True)
        p_displayProcess = Process(target=displayProcess.displayProcessScript, args=(
            displayProcessFlag, printFlag_displayProcess, dhtArr, fanArr))
        p_displayProcess.start()

        uploadProcessFlag = Value('i', True)
        p_uploadProcess = Process(target=uploadProcess.uploadProcessScript, args=(
            uploadProcessFlag, printFlag_uploadProcess, fanQueue, DHTQueue))
        p_uploadProcess.start()

        previousTimeSleepCycle = time()
        while True:
            # print(str(p_fanProcess) + ': ' + str(p_fanProcess.is_alive()) )
            # print(str(p_DHTProcess) + ': ' + str(p_DHTProcess.is_alive()) )
            # print(str(p_displayProcess) + ': ' + str(p_DHTProcess.is_alive()) )
            # print(str(p_uploadProcess) + ': ' + str(p_DHTProcess.is_alive()) )
            runTime = time()
            timeBetweenSleepCycles = time() - previousTimeSleepCycle
            if timeBetweenSleepCycles >= 2 * variablesConfig.checkIfAlive:
                logger.error(
                    'time between two checking if alive controlls is too big (more than 2x) time between=' + str(timeBetweenSleepCycles))
                data = subprocess.check_output(
                    'uptime', shell=True)  # also load on CPUs
                sendString = 'Time timeBetween two fan speed controlls is too big (more than 2x)'
                sendString += '"\n\t"timeBetween = ' + \
                    str(timeBetweenSleepCycles)
                sendString += '"\n\t"someInfo = ' + data
                sendString += '"\n\t"Rebooting Raspberry Pi!!!'
                # print(sendString)

                sendMail(variablesConfig.email_sendTo, sendString)
                logger.error('someInfo: ' + data)
                subprocess.Popen('reboot', shell=True, stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE, stderr=subprocess.STDOUT)

            if (p_fanProcess.is_alive() == False):
                logger.warning(
                    'p_fanProcess was not running!!! ' + str(p_fanProcess.exitcode))
                sendMail_processNotRunning(
                    'p_fanProcess', p_fanProcess.exitcode)
                p_fanProcess = Process(target=fanProcess.fanProcessScript, args=(
                    fanProcessFlag, printFlag_fanProcess, lock_fanFile, fanQueue, fanArr))
                p_fanProcess.start()
            if (p_DHTProcess.is_alive() == False):
                logger.warning(
                    'p_DHTProcess was not running!!! ' + str(p_DHTProcess.exitcode))
                sendMail_processNotRunning(
                    'p_DHTProcess', p_DHTProcess.exitcode)
                p_DHTProcess = Process(target=DHTProcess.DHTProcessScript, args=(
                    DHTProcessFlag, printFlag_DHTProcess, lock_DHTFile, DHTQueue, dhtArr))
                p_DHTProcess.start()
            if (p_displayProcess.is_alive() == False):
                logger.warning(
                    'p_displayProcess was not running!!! ' + str(p_displayProcess.exitcode))
                sendMail_processNotRunning(
                    'p_displayProcess', p_displayProcess.exitcode)
                p_displayProcess = Process(target=displayProcess.displayProcessScript, args=(
                    displayProcessFlag, printFlag_displayProcess, dhtArr, fanArr))
                p_displayProcess.start()
            if (p_uploadProcess.is_alive() == False):
                logger.warning(
                    'p_uploadProcess was not running!!! ' + str(p_uploadProcess.exitcode))
                sendMail_processNotRunning(
                    'p_uploadProcess', p_uploadProcess.exitcode)
                p_uploadProcess = Process(target=uploadProcess.uploadProcessScript, args=(
                    uploadProcessFlag, printFlag_uploadProcess, fanQueue, DHTQueue))
                p_uploadProcess.start()

            if (variablesConfig.printFlag_main):
                print('mainProcess: Runned for: {0:0.4}'.format(
                    time() - runTime) + 's')
                print('mainProcess: Going to sleep for ' +
                      str(variablesConfig.checkIfAlive) + 's\n')

            previousTimeSleepCycle = time()
            sleep(variablesConfig.checkIfAlive)
        # p.join()

    except KeyboardInterrupt:  # CTRL+C = keyboard interrupt
        print('KeyboardInterrupt')
    except Exception as e:
        # this catches ALL other exceptions including errors.
        # You won't get any error messages for debugging
        # so only use it once your code is working
        logger.error('Error: ' + str(e))
        print ("Other error or exception occurred!")
        sendString = 'Error: ' + str(e)
        sendMail(variablesConfig.email_sendTo, sendString)
        print('\nError:\n' + str(e))

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

        sys.exit(0)