# multiPiTS - multifunction Raspberry Pi with ThingSpeak
- PID-fan-controller
- measuring room temperature and humidity
- uploading data to https://thingspeak.com/ (average CPU temperature, average dutyCycle of the fan, current temperature and humidity of the room in which the Raspberry Pi is located

# PID-fan-controller
For controlling fan of Raspberry Pi with Raspbian OS

This code is inspired by Andreas Spiess and his YouTube channel https://www.youtube.com/channel/UCu7_D0o48KbfhpEohoP7YSQ.

His two videos were the base for this code (https://youtu.be/P5o0PpfzuW8?list=PL3XBzmAj53RnezxZ_uq8YMymURnnLTqZP and https://youtu.be/oJ32CMxliCQ?list=PL3XBzmAj53RnezxZ_uq8YMymURnnLTqZP).

If you are going to use this code, change PIDs that will suit your needs.
This code is ment to start on boot and run indefinitely (to start it on boot https://www.dexterindustries.com/howto/run-a-program-on-your-raspberry-pi-at-startup/).

I know that this code if far from good soo if you have any suggestions, I would be very pleased, if you let me know.
