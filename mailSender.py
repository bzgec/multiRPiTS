#! /usr/bin/python3

import sys
import smtplib
import mailConfig	# file where EMAIL_ADDRESS and EMAIL_PASSWORD are saved

def send_email(subject, msg):
    try:
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(mailConfig.FROM_EMAIL_ADDRESS, mailConfig.PASSWORD)
        message = 'Subject: {}\n\n{}'.format(subject, msg)
        server.sendmail(mailConfig.FROM_EMAIL_ADDRESS, mailConfig.TO_EMAIL_ADDRESS, message)
        server.quit()
        print("Success: Email sent!")
    except:
        print("Email failed to send.")

subject = sys.argv[1]	# [0] is name of the file
i = 2
msg = ''
while i < len(sys.argv):
	msg += sys.argv[i] + ' '
	i += 1

send_email(subject, msg)
sys.exit(1)