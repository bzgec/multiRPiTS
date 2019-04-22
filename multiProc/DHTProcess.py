from __future__ import print_function

def DHTProcessScript(DHTProcessFlag, printFlag_DHTProcess, lock_DHTFile, DHTQueue, dhtArr):
    import os
    import subprocess
    from time import sleep, time
    import sys
    import datetime
    import json
    import Adafruit_DHT
    import variablesConfig
    import logging
    import xlsxwriter

    if not os.path.isfile(variablesConfig.path_log_file_DHTProcess):
        if not os.path.isdir(variablesConfig.path_log_dir):
            os.makedirs(variablesConfig.path_log_dir)
        file = open(variablesConfig.path_log_file_DHTProcess, 'w')
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
    logger = setup_logger('defaultLogger', variablesConfig.path_log_file_DHTProcess)
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

    if printFlag_DHTProcess.value == False:
        sys.stdout = open(os.devnull, "w")  # suppress console output

    ######################################################
    # CONFIGURATION FOR DHT22
    sensor = Adafruit_DHT.DHT22
    # connected to GPIO2.

    class DHT:
        temperatureDHT = 0
        humidityDHT = 0
    ######################################################

    class xlsxData:
        workbook = xlsxwriter.Workbook('DHTProcess.xlsx')
        worksheet = workbook.add_worksheet('Sheet 1')
        row = 0
        column = 0

    def convertToFloatPoint(variable):
        variable = float(format(variable, '.1f'))
        return variable

    def getTempAndHumidity():
        # global DHT.temperatureDHT, DHT.humidityDHT
        readings = True 	# if reading fails it will change the value
        print('###################################################')
        print('Geting temperature and humidity')
        # Try to grab a sensor reading.  Use the read_retry method which will retry up
        # to 15 times to get a sensor reading (waiting 2 seconds between each retry).
        DHT.humidityDHT, DHT.temperatureDHT = Adafruit_DHT.read_retry(
            sensor, variablesConfig.temperatureScript_PIN_DHT)
        # Note that sometimes you won't get a reading and
        # the results will be null (because Linux can't
        # guarantee the timing of calls to read the sensor).
        # If this happens try again!
        if DHT.humidityDHT is not None and DHT.temperatureDHT is not None:
            DHT.humidityDHT = convertToFloatPoint(DHT.humidityDHT)
            DHT.temperatureDHT = convertToFloatPoint(DHT.temperatureDHT)
            print('Temp: ' + str(DHT.temperatureDHT) +
                  '*C, Humidity: ' + str(DHT.humidityDHT))
            # logger.info('Temperature=' + str(DHT.temperatureDHT) + ', humidity=' + str(DHT.humidityDHT))
        else:
            print('Failed to get reading. Try again!')
            logger.warning(
                'Reading temperature&humidity FAILED trying again (second time)')
            sleep(3)
            DHT.humidityDHT, DHT.temperatureDHT = Adafruit_DHT.read_retry(
                sensor, variablesConfig.temperatureScript_PIN_DHT)

        # if readings are wrong... it happened to me that humidity was 3303.0
        if DHT.humidityDHT > 100 or DHT.humidityDHT < 0 or DHT.temperatureDHT < 0:
            print(
                'DHT.humidityDHT > 100 or DHT.humidityDHT < 0 or DHT.temperatureDHT < 0 --> trying again')
            logger.warning(
                'DHT.humidityDHT > 100 or DHT.humidityDHT < 0 or DHT.temperatureDHT < o -> trying again')
            sleep(3)
            DHT.humidityDHT, DHT.temperatureDHT = Adafruit_DHT.read_retry(
                sensor, variablesConfig.temperatureScript_PIN_DHT)
            if DHT.humidityDHT is not None and DHT.temperatureDHT is not None:
                DHT.humidityDHT = convertToFloatPoint(DHT.humidityDHT)
                DHT.temperatureDHT = convertToFloatPoint(DHT.temperatureDHT)
                print('Temp: ' + str(DHT.temperatureDHT) +
                      '*C, Humidity: ' + str(DHT.humidityDHT))
                # logger.info('Temperature=' + str(DHT.temperatureDHT) + ', humidity=' + str(DHT.humidityDHT))
            else:
                print('Failed to get reading again!!!')
                logger.error(
                    'Error with DHT sensor - can not get a correct reading')
                readings = False
                date = datetime.datetime.today().strftime(variablesConfig.dateFormat)
                xlsxData.row += 1
                xlsxData.column = 0
                xlsxData.worksheet.write(xlsxData.row, xlsxData.column, date)
                xlsxData.column += 1
                xlsxData.worksheet.write(
                    xlsxData.row, xlsxData.column, 'DHT.humidityDHT > 100 or DHT.humidityDHT < 0 or DHT.temperatureDHT < o -> trying again')
                xlsxData.column += 1
                xlsxData.worksheet.write_number(
                    xlsxData.row, xlsxData.column, DHT.temperatureDHT)
                xlsxData.column += 1
                xlsxData.worksheet.write_number(
                    xlsxData.row, xlsxData.column, DHT.humidityDHT)
        print('###################################################')
        return(readings)

        # subprocess.Popen('python3 /home/pi/scripts/mailSender.py temperatureScript.py Program started: ' + datetime.datetime.today().strftime(variablesConfig.dateFormat), shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    try:
        # Create an new Excel file and add a worksheet.
        # workbook = xlsxwriter.Workbook('DHTProcess.xlsx')
        # worksheet = workbook.add_worksheet('Sheet 1')
        xlsxData.row = 1
        print('writing first row')
        xlsxData.worksheet.write(0, 0, 'time')
        xlsxData.worksheet.write(0, 1, 'Error')
        xlsxData.worksheet.write(0, 2, 'temperature')
        xlsxData.worksheet.write(0, 3, 'humidity')

        while DHTProcessFlag:
            # global DHT.temperatureDHT, DHT.humidityDHT
            runTime = time()

            if getTempAndHumidity() == False:
                dhtErr = 1
                sendString = 'ERROR DHT22: ' + datetime.datetime.today().strftime(variablesConfig.dateFormat)
                sendMail(variablesConfig.email_sendTo, sendString)

            else:
                dhtErr = 0

            jsonString = json.JSONEncoder().encode({'temperatureDHT': DHT.temperatureDHT,
                                                    'humidityDHT': DHT.humidityDHT,
                                                    'dhtErr': dhtErr
                                                    })

            DHTQueue.put([DHT.temperatureDHT, DHT.humidityDHT, dhtErr])

            dhtArr[0] = DHT.temperatureDHT
            dhtArr[1] = DHT.humidityDHT
            dhtArr[2] = dhtErr

            # file = open('/home/pi/logs/temperatureScript_DATA.log', 'w', os.O_NONBLOCK)	# os.O_NONBLOCK that two programs can read/write a file at the same time
            # file.write(jsonString)
            # file.close()

            lock_DHTFile.acquire()
            with open(variablesConfig.path_process_DHT_DATA, 'w') as file:
                file.write(jsonString)
            lock_DHTFile.release()

            print('DHTProcess: Runned for: {0:0.4}'.format(
                time() - runTime) + 's')
            print('DHTProcess: Going to sleep for ' +
                  str(variablesConfig.temperatureScript_measureTime) + 's')
            print('')
            # goes to sleep for
            sleep(variablesConfig.temperatureScript_measureTime)
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
        print('Leaving DHTProcess')
        # sys.exit(0)