# -*- coding: utf-8 -*-
import json
from email.mime.text import MIMEText
import smtplib
import configparser
import os

def Send(Message):
    currentPath = os.path.dirname(os.path.abspath(__file__))
    config = configparser.ConfigParser()
    config.read(currentPath + '/Sensor_Console/Config.ini')
    GmailUser = config.get('Setting','GmailUser')
    GmailApplicationPassword = config.get('Setting','GmailApplicationPassword')
    NotifycationEmailUser = config.get('Setting','NotifycationEmailUser')


    to = NotifycationEmailUser

    message = MIMEText(Message, 'plain', 'utf-8')
    message['Subject'] = 'System notifycation'
    message['From'] = GmailUser
    message['To'] = to

    # Set smtp
    smtp = smtplib.SMTP("smtp.gmail.com:587")
    smtp.ehlo()
    smtp.starttls()
    smtp.login(GmailUser, GmailApplicationPassword)

    # Send msil
    smtp.sendmail(message['From'], message['To'], message.as_string())
    print('Send mails:'+Message)


if __name__ == "__main__":
    SendMail("test")