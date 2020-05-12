# -*- coding: utf-8 -*-
 
import RPi.GPIO as GPIO
import time
import pdb
from enum import Enum

#偵測限位感測器的狀態
def ReturnSensorStatus(SensorNumber):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SensorNumber, GPIO.IN)
    #感應片間有物體會輸出1
    status = GPIO.input(SensorNumber)
    if status:
        return True
    else:
        return False
