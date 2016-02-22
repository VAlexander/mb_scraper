import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText

def mail(message, to):
	try:
		msg = MIMEText(message)


		me = 'root@localhost'
		msg['Subject'] = 'The contents of scraping'
		msg['From'] = me
		msg['To'] = to

		# Send the message via our own SMTP server, but don't include the
		# envelope header.
		s = smtplib.SMTP('127.0.0.1')
		s.sendmail(me, to, msg.as_string())
		s.quit()
		
		return True
	except:
		return False
