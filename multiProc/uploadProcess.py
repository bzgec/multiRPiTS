from __future__ import print_function


def uploadProcessScript(uploadProcessFlag, printFlag_uploadProcess, fanQueue, DHTQueue):

    import os
    import subprocess
    from time import sleep, time
    import sys
    import urllib3
    import datetime
    # import json

    import variablesConfig

    import logging
    if not os.path.isfile(variablesConfig.path_log_file_uploadProcess):
        if not os.path.isdir(variablesConfig.path_log_dir):
            os.makedirs(variablesConfig.path_log_dir)
        file = open(variablesConfig.path_log_file_uploadProcess, 'w')
        file.close()

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
    logger = setup_logger('defaultLogger', variablesConfig.path_log_file_uploadProcess)
    logger.warning('Program started')

    def sendMail(reciever, msg):
        string = 'python3 ' + variablesConfig.path_mailSender + \
            ' ' + reciever + ' ' + __file__ + ' '
        string += msg
        # print(string)
        subprocess.Popen(string, shell=True, stdout=subprocess.PIPE,
                         stdin=subprocess.PIPE, stderr=subprocess.STDOUT)

    # print('module name:', __name__)
    # print('parent process:', os.getppid())
    # print('process id:', os.getpid())
    print(__name__ + ' id: ' + str(os.getpid()))

    if printFlag_uploadProcess.value == False:
        sys.stdout = open(os.devnull, "w")  # suppress console output

    class uploadProcessScript:
        tempSum = 0
        dutyCycleSum = 0
        measurements_fan = 0

        tempDHTSum = 0
        humidityDHTSum = 0
        measurements_DHT = 0
        dhtErrCount = 0
        # global uploadProcessScript.lastUploadTime
        # it uploads first data after upload time (this is because if you just run program connected from TeamViewer, the cpu temp would be very high and first upload would not be really accurate)
        lastUploadTime = time()

    def terminalCommand(command):
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                         stdin=subprocess.PIPE, stderr=subprocess.STDOUT)

    def postToThingSpeak():
        print('###################################################')
        print('Posting to thingspeak.com')
        print('uploadProcessScript.measurements_fan: ' +
              str(uploadProcessScript.measurements_fan))
        print('uploadProcessScript.measurements_DHT: ' +
              str(uploadProcessScript.measurements_DHT))
        print('uploadProcessScript.dhtErrCount: ' +
              str(uploadProcessScript.dhtErrCount))
        # global uploadProcessScript.measurements_fan, uploadProcessScript.measurements_DHT, uploadProcessScript.tempSum, uploadProcessScript.dutyCycleSum, uploadProcessScript.lastUploadTime, uploadProcessScript.tempDHTSum, uploadProcessScript.humidityDHTSum, uploadProcessScript.dhtErrCount
        averageCPUTemp = format(
            uploadProcessScript.tempSum / uploadProcessScript.measurements_fan, '.1f')
        averageFanSpeed = format(
            uploadProcessScript.dutyCycleSum / uploadProcessScript.measurements_fan, '.1f')
        if uploadProcessScript.dhtErrCount != uploadProcessScript.measurements_DHT:  # do not divide with zero
            averageTempDHT = format(uploadProcessScript.tempDHTSum / (
                uploadProcessScript.measurements_DHT - uploadProcessScript.dhtErrCount), '.1f')
            averageHumidityDHT = format(uploadProcessScript.humidityDHTSum / (
                uploadProcessScript.measurements_DHT - uploadProcessScript.dhtErrCount), '.1f')
        else:
            averageTempDHT = 'Err'
            averageHumidityDHT = 'Err'
        # logger.info('Posting to thingSpeak.com: ' + 'averageCPUTemp=' + averageCPUTemp + ', averageFanSpeed=' + averageFanSpeed + ', averageTempDHT=' + averageTempDHT + ', averageHumidityDHT=' + averageHumidityDHT)

        if uploadProcessScript.dhtErrCount != 0:
            logger.warning('Error in DHT uploadProcessScript.dhtErrCount: ' +
                           str(uploadProcessScript.dhtErrCount))

            sendString = 'Uploaded to ThingSpeak: ' + datetime.datetime.today().strftime(variablesConfig.dateFormat) + \
                '"\n"measurements:' + \
                '"\n\t"fan: ' + str(uploadProcessScript.measurements_fan) + \
                '"\n\t"DHT: ' + str(uploadProcessScript.measurements_DHT) + \
                '"\n"dhtErrCount: ' + str(uploadProcessScript.dhtErrCount) + \
                '"\n"averageCPUTemp: ' + averageCPUTemp + ', averageFanSpeed: ' + averageFanSpeed + \
                '"\n"averageTempDHT: ' + averageTempDHT + ', averageHumidityDHT: ' + averageHumidityDHT

            sendMail(variablesConfig.email_sendTo, sendString)

        # cpu_pc = psutil.cpu_percent()
        # mem_avail_mb = psutil.avail_phymem()/1000000

        link = 'https://api.thingspeak.com/update?api_key='
        data = '&field1=' + averageCPUTemp + '&field2=' + averageFanSpeed
        # if it is equal of grater, do not upload to data to ThingSpeak, because it would be 0...
        if uploadProcessScript.dhtErrCount < uploadProcessScript.measurements_DHT:
            data += '&field3=' + averageTempDHT + '&field4=' + averageHumidityDHT
        print('averageCPUTemp=' + averageCPUTemp + ', averageFanSpeed=' + averageFanSpeed +
              ', averageTempDHT=' + averageTempDHT + ', averageHumidityDHT=' + averageHumidityDHT)

        http = urllib3.PoolManager()
        r = http.request('GET', link + variablesConfig.thingSpeak_WRITE_API_KEY + data)
        # print(r.status)
        if r.status == 200:
            print("Posted")
            uploadProcessScript.tempSum = 0
            uploadProcessScript.dutyCycleSum = 0
            uploadProcessScript.measurements_fan = 0
            uploadProcessScript.measurements_DHT = 0
            uploadProcessScript.humidityDHTSum = 0
            uploadProcessScript.tempDHTSum = 0
            uploadProcessScript.dhtErrCount = 0
            uploadProcessScript.lastUploadTime = time()
        else:
            print ("connection failed")
            logger.warning('FAILED to post to ThingSpeak')
            sendMail(variablesConfig.email_sendTo, 'FAILED to post to ThingSpeak: ' +
                     datetime.datetime.today().strftime(variablesConfig.dateFormat))

        # try:
        # 	f = urllib.urlopen(link + thingSpeak_WRITE_API_KEY + data)
        # 	#f.read()
        # 	#print(f)
        # 	print("Posted")
        # 	uploadProcessScript.tempSum = 0
        # 	uploadProcessScript.dutyCycleSum = 0
        # 	uploadProcessScript.measurements_fan = 0
        # 	uploadProcessScript.measurements_DHT = 0
        # 	uploadProcessScript.humidityDHTSum = 0
        # 	uploadProcessScript.tempDHTSum = 0
        # 	uploadProcessScript.dhtErrCount = 0
        # 	uploadProcessScript.lastUploadTime = time()
        # except:
        # 	print ("connection failed")
        # 	# logger.warning('FAILED to post to ThingSpeak')

        print('###################################################')
        return()

    # terminalCommand('python3 /home/pi/scripts/mailSender.py uploadThingSpeak.py Program started: ' + datetime.datetime.today().strftime(variablesConfig.dateFormat), shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    try:
        while uploadProcessFlag.value:
            runTime = time()

            while fanQueue.empty() == False:
                tempArr = fanQueue.get()
                print('tempArr: ' + str(tempArr))
                uploadProcessScript.tempSum += tempArr[0]
                uploadProcessScript.dutyCycleSum += tempArr[1]
                uploadProcessScript.measurements_fan += 1
            print('uploadProcessScript.tempSum: ' +
                  str(uploadProcessScript.tempSum))
            print('uploadProcessScript.dutyCycleSum: ' +
                  str(uploadProcessScript.dutyCycleSum))
            while DHTQueue.empty() == False:
                tempArr = DHTQueue.get()
                print('tempArr: ' + str(tempArr))
                # tempArr[2]=dhtErr
                if tempArr[2] == 1:  # it counts how many readings failed, so when you calculate average number, you subtract it from uploadProcessScript.measurements_DHT
                    uploadProcessScript.dhtErrCount += 1
                    # temperatureDHT and humidityDHT are None -> TypeError: unsupported operand type(s) for +=: 'float' and    'NoneType', so we do not add them to our sum...
                else:
                    uploadProcessScript.tempDHTSum += tempArr[0]
                    uploadProcessScript.humidityDHTSum += tempArr[1]
                uploadProcessScript.measurements_DHT += 1
            print('uploadProcessScript.tempDHTSum: ' +
                  str(uploadProcessScript.tempDHTSum))
            print('uploadProcessScript.humidityDHTSum: ' +
                  str(uploadProcessScript.humidityDHTSum))
            print('uploadProcessScript.dhtErrCount: ' +
                  str(uploadProcessScript.dhtErrCount))
            # print('DHTQueue size: ' + str(DHTQueue.qsize()))
            # if temperatureJson['dhtErr'] == True:	# it counts how many readings failed, so when you calculate average number,    you subtract it from measurements
            # 	uploadProcessScript.dhtErrCount += 1
            # 	# temperatureDHT and humidityDHT are None -> TypeError: unsupported operand type(s) for +=: 'float' and 'NoneType'
            # else:
            # 	uploadProcessScript.tempDHTSum += temperatureJson['temperatureDHT']
            # 	uploadProcessScript.humidityDHTSum += temperatureJson['humidityDHT']
            if runTime - uploadProcessScript.lastUploadTime >= variablesConfig.thingSpeak_uploadTime:
                postToThingSpeak()
            print('uploadProcess: Runned for: {0:0.4}'.format(
                time() - runTime) + 's')
            print('uploadProcess: Going to sleep for ' +
                  str(variablesConfig.thingSpeak_sleepDuration) + 's\n')
            sleep(variablesConfig.thingSpeak_sleepDuration)  # goes to sleep for
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
        print('Leaving uploadProcess')