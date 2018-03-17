# multiRPiTS - multifunction script for Raspberry Pi with ThingSpeak
- PID-fan-controller
- measuring room temperature and humidity
- uploading data to https://thingspeak.com/channels/342779 (average CPU temperature, average fan speed, current temperature and humidity of the room in which the Raspberry Pi is located
- displaying data on OLED display (SSD1306 128x64 screen with I2C)


# PID-fan-controller
For controlling fan on Raspberry Pi.


# SSD1306 display
Follow this instructions to install everything that SSD1306 display needs to work with my code:
https://learn.adafruit.com/ssd1306-oled-displays-with-raspberry-pi-and-beaglebone-black/wiring
https://learn.adafruit.com/ssd1306-oled-displays-with-raspberry-pi-and-beaglebone-black/usage

Also enable automatic loading of I2C kernel module:
https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c


If you are going to use this code, change PIDs that will suit your needs.
This code is ment to start on boot and run indefinitely (to start it on boot https://www.dexterindustries.com/howto/run-a-program-on-your-raspberry-pi-at-startup/).


This code was initially inspired by Andreas Spiess and his YouTube channel https://www.youtube.com/channel/UCu7_D0o48KbfhpEohoP7YSQ.
His two videos were the base for this code (https://youtu.be/P5o0PpfzuW8?list=PL3XBzmAj53RnezxZ_uq8YMymURnnLTqZP and https://youtu.be/oJ32CMxliCQ?list=PL3XBzmAj53RnezxZ_uq8YMymURnnLTqZP).

I know that this code if far from good soo if you have any suggestions, I would be very pleased, if you let me know.
