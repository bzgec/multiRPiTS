from __future__ import print_function


def displayProcessScript(displayProcessFlag, printFlag_displayProcess, dhtArr, fanArr):

    import os
    import subprocess
    from time import sleep, time
    import sys
    # import datetime
    # import json

    import variablesConfig

    import Adafruit_SSD1306

    from PIL import Image
    from PIL import ImageDraw
    from PIL import ImageFont

    import logging
    if not os.path.isfile(variablesConfig.path_log_file_displayProcess):
        if not os.path.isdir(variablesConfig.path_log_dir):
            os.makedirs(variablesConfig.path_log_dir)
        file = open(variablesConfig.path_log_file_displayProcess, 'w')
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
    logger = setup_logger('defaultLogger', variablesConfig.path_log_file_displayProcess)
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

    if printFlag_displayProcess.value == False:
        sys.stdout = open(os.devnull, "w")  # suppress console output

    ######################################################
    # CONFIGURATION FOR DISPLAY
    # Raspberry Pi pin configuration:
    # RST = 24 # if is defined in variablesConfig.py
    # 128x64 display with hardware I2C:
    disp = Adafruit_SSD1306.SSD1306_128_64(rst=variablesConfig.displayScript_RST)
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
    draw.rectangle((0, 0, widthOLED, heightOLED), outline=0, fill=0)
    padding = variablesConfig.displayScript_padding
    linePadding = variablesConfig.displayScript_linePadding
    fontSize = variablesConfig.displayScript_fontSize
    x = padding
    y = padding
    font = ImageFont.load_default()
    # font = ImageFont.truetype('font1.otf', fontSize)
    # font = ImageFont.truetype('font2.ttf', fontSize)
    # font = ImageFont.truetype('font3.ttf', fontSize)

    if variablesConfig.displayScript_sleepDuration_fanScript is True:
        variablesConfig.displayScript_sleepDuration = variablesConfig.fanScript_sleepDuration

    # subprocess.Popen('python3 /home/pi/scripts/mailSender.py displayScript.py Program started: ' + datetime.datetime.today().strftime(variablesConfig.dateFormat), shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    try:
        while displayProcessFlag.value:
            runTime = time()

            # fanScript_DATA = open('/home/pi/logs/fanScript_DATA.log','r')
            # fanJson = json.loads( fanScript_DATA.read() )
            # fanScript_DATA.close()

            # temperatureScript_DATA = open('/home/pi/logs/temperatureScript_DATA.log','r', os.O_NONBLOCK)	# os.O_NONBLOCK that two programs can read/write a file at the same time
            # temperatureJson = json.loads( temperatureScript_DATA.read() )
            # temperatureScript_DATA.close()

            # lock_fanFile.acquire()
            # with open('/home/pi/logs/process_fan_DATA.txt','r') as fanScript_DATA:
            # 	fanJson = json.loads( fanScript_DATA.read() )
            # lock_fanFile.release()

            # lock_DHTFile.acquire()
            # with open('/home/pi/logs/process_DHT_DATA.txt','r') as temperatureScript_DATA:
            # 	temperatureJson = json.loads( temperatureScript_DATA.read() )
            # lock_DHTFile.release()

            disp.clear()
            draw.rectangle((0, 0, widthOLED, heightOLED), outline=0, fill=0)
            y = padding
            # draw.text((x, y),    'D:' + str(fanJson['desiredTemp']) + ', R:' + str(fanJson['cpuTemp']) + ', ' + str(fanJson['differenceInTemp']),  font=font, fill=255)
            # y += fontSize + linePadding
            # draw.text((x, y),    'p:' + str(fanJson['p']),  font=font, fill=255)
            # y += fontSize + linePadding
            # draw.text((x, y),    'i:' + str(fanJson['i']) + ', pid sum:' + str(fanJson['pidsum']),  font=font, fill=255)
            # y += fontSize + linePadding
            # draw.text((x, y),    'd:' + str(fanJson['d']) + ', delta_t:' + str(fanJson['delta_t']),  font=font, fill=255)
            # y += fontSize + linePadding

            # fanArr[] -> desiredTemp, cpuTemp, differenceInTemp, dutyCycle, p, i, d, pidsum, delta_t
            draw.text((x, y), 'D:' + str(fanArr[0]) + ', R:' + str(
                fanArr[1]) + ', ' + str(fanArr[2]), font=font, fill=255)
            y += fontSize + linePadding
            draw.text((x, y), 'p:' + str(fanArr[4]), font=font, fill=255)
            y += fontSize + linePadding
            draw.text(
                (x, y), 'i:' + str(fanArr[5]) + ', pid sum:' + str(fanArr[7]), font=font, fill=255)
            y += fontSize + linePadding
            draw.text(
                (x, y), 'd:' + str(fanArr[6]) + ', delta_t:' + str(fanArr[8]), font=font, fill=255)
            y += fontSize + linePadding

            draw.text((x, heightOLED - 2 * (fontSize + linePadding)),
                      'TEMP: ' + str(dhtArr[0]), font=font, fill=255)
            draw.text((x, heightOLED - (fontSize + linePadding)),
                      'Humidity: ' + str(dhtArr[1]), font=font, fill=255)

            disp.image(image)
            disp.display()
            print('displayProcess: Runned for: {0:0.4}'.format(
                time() - runTime) + 's')
            print('displayProcess: Going to sleep for ' +
                  str(variablesConfig.displayScript_sleepDuration) + 's\n')
            sleep(variablesConfig.displayScript_sleepDuration)  # goes to sleep for

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
        print('Leaving displayProcess')
        disp.clear()
        disp.image(image)
        disp.display()
        # sys.exit(0)