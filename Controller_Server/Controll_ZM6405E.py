import RPi.GPIO as GPIO
import time

def Run_BrushlessDC_Motor_ByInputSetNumber(TimeMinSec,DR_Type):
    #1000毫秒 = 1秒
    TimeMinSec = int(TimeMinSec)/1000

    #DR_Type = 順時針轉為1,逆時鐘轉為0
    #這個控制器真的很奇怪，高電壓(GPIO.HIGH)才反轉
    #所以下面這段進行反相操作 輸入0 視為GPIO.HIGH
    if DR_Type=='1':
        DR_Type = 0
    else:
        DR_Type = 1

    EN = 17
    DR = 27
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(EN, GPIO.OUT)
    GPIO.setup(DR, GPIO.OUT)

    #開始轉動
    GPIO.output(DR, DR_Type)
    print('開始轉動')
    GPIO.output(EN, GPIO.HIGH)
    time.sleep(int(TimeMinSec))
    print('停止轉動')
    GPIO.output(EN, GPIO.LOW)
    return 'clear'    
