checkIfAlive = 5	# it checks if process are running

printFlag_main = False
printFlag_fan = False
printFlag_DHT = False
printFlag_display = False
printFlag_upload = False

thingSpeak_WRITE_API_KEY = 'YOUR API KEY FOR ThingSpeak'
thingSpeak_uploadTime = 30*60	# uploads data to ThingSpeak every 30 minutes
thingSpeak_sleepDuration = 30


fanScript_sleepDuration = 1	# every x seconds the program is going to check the temperature and according to that, set the new speed of the fan
fanScript_fanPin = 17
fanScript_desiredTemp = 45
fanScript_minFanSpeed = 30	# it is in %
fanScript_P = 100
fanScript_I = 10
fanScript_D = 50
xlsxwriter_flag = True
fanScript_I_OFF = 1	# when difference between realValue and setPoint (error) is greater then this value integral part is set to 0 (explanation in fanProcess.py file)

displayScript_sleepDuration_fanScript = True 	# if you wanna use the same value as the fanScript_sleepDuration
displayScript_sleepDuration = 2
displayScript_RST = 24	# I2C RST pin
# display configuration
displayScript_padding = 0
displayScript_linePadding = 2
displayScript_fontSize = 8


temperatureScript_DHTpin = 27
temperatureScript_measureTime = 5*60	# reads temperature and humidity every 5 minutes, other time it sleeps

runChecker_sleepDuration = 2*60