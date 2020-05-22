# -*- coding: utf-8 -*-
 
import RPi.GPIO as GPIO
import time
import pdb
from enum import Enum

 #終端限位感測
limitSensor1 = 23
limitSensor2 = 24

#零點感測器
ZeroSensor1 = 0
ZeroSensor2 = 26

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(limitSensor1, GPIO.IN)
GPIO.setup(limitSensor2, GPIO.IN)
GPIO.setup(ZeroSensor1, GPIO.IN)
GPIO.setup(ZeroSensor2, GPIO.IN)

#偵測限位感測器的狀態
def ReturnSensorStatus(SensorNumber):
    #感應片間有物體會輸出1
    status = GPIO.input(SensorNumber)
    if status:
        return True
    else:
        return False
