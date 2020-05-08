import RPi.GPIO as GPIO
import time
import pdb
#光敏電阻input pin
photocell = 26


def ReturnLightControllStatus():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(photocell, GPIO.IN)
    #感應片間有物體會輸出1
    input = GPIO.input(photocell)
    return input