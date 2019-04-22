#! /usr/bin/python3

"""
USAGE: python mailSender.py toEmail@gmail.com messageSubject MESSAGE_TO_SEND
MESSAGE_TO_SEND -> message is going to be pasted in body of html code
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys
import mailConfig	# file where EMAIL_ADDRESS and EMAIL_PASSWORD are saved
import datetime
 
# With this function we send out our html email
def send_email_cmd(SUBJECT, BODY, TO, FROM):
  startDate = datetime.datetime.today().strftime(mailConfig.dateFormat)

  # Create message container - the correct MIME type is multipart/alternative here!
  MESSAGE = MIMEMultipart('alternative')
  MESSAGE['subject'] = SUBJECT
  MESSAGE['To'] = TO
  MESSAGE['From'] = FROM
  MESSAGE.preamble = """Your mail reader does not support the report format.""" 
   
  # Record the MIME type text/html.
  email_content = '<html><head></head><body>'
  email_content += BODY 
  email_content += '<br><br><p><font size="1">Mail sent: ' + startDate + '</font></p></body></html>'
  HTML_BODY = MIMEText(email_content, 'html')
 
  # Attach parts into message container.
  # According to RFC 2046, the last part of a multipart message, in this case
  # the HTML message, is best and preferred.
  MESSAGE.attach(HTML_BODY)
 
  # The actual sending of the e-mail
  server = smtplib.SMTP('smtp.gmail.com:587')
 
  # Print debugging output when testing
  if __name__ == "__main__":
    server.set_debuglevel(1)
 
  # Credentials (if needed) for sending the mail
  password = mailConfig.PASSWORD
 
  server.starttls()
  server.login(FROM, password)
  server.sendmail(FROM, [TO], MESSAGE.as_string())
  server.quit()

def send_email(TO, SUBJECT, BODY):
  send_email_cmd(SUBJECT, BODY, TO, mailConfig.FROM_EMAIL_ADDRESS)
 
# [0] is name of the file
if __name__ == "__main__":
  email_reciever = sys.argv[1]	# reciever email address
  subject = sys.argv[2]   
  i = 3
  msg = ''
  while i < len(sys.argv):
    msg += sys.argv[i] + ' '
    i += 1

  send_email_cmd(subject, msg, email_reciever, mailConfig.FROM_EMAIL_ADDRESS)
  sys.exit()