import RPi.GPIO as GPIO
import time
import pdb

#啟動步進馬達，在使用者輸入一個指定毫秒時
def RunStepping_MotorByInputSetNumber(TimeMinSec,DR_Type):
    #將毫秒變成脈衝次數
    TimeMinSec = int(TimeMinSec)*10
    #Set Enable
    ENA = 5

    #方向
    DIR = 6

    #脈衝
    PUL = 13

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(ENA, GPIO.OUT)
    GPIO.setup(DIR, GPIO.OUT)
    GPIO.setup(PUL, GPIO.OUT)

    #Enable = GPIO.LOW (低電壓為啟動)
    GPIO.output(ENA, GPIO.LOW)

    #DR_Type = 順時針轉為1,逆時鐘轉為0
    #正轉
    GPIO.output(DIR, int(DR_Type))

    for i in range(int(TimeMinSec)):
        GPIO.output(PUL, GPIO.LOW)
        time.sleep(0.00001)
        GPIO.output(PUL, GPIO.HIGH)
        time.sleep(0.00001)

    return 'Clear'