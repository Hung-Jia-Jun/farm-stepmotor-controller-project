import RPi.GPIO as GPIO
import time
import pdb

#啟動步進馬達，在使用者輸入一個指定毫秒時
def RunStepping_MotorByInputSetNumber(Pulse_Width,Pulse_Count,PulseFrequency,DR_Type):
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

    #一秒內有工作的時候(高電平)有幾毫秒
    WorkDutyTime = ((1/100) * int(Pulse_Width))
    #PulseFrequency 每秒要產生幾個脈波
    #所以可以得知每個脈波有多久
    EachDutyTime = 1/int(PulseFrequency)
    #工作的時間有多少
    HighDutyTime = EachDutyTime * WorkDutyTime

    #扣掉工作的時間就是低電平的時間
    LowDutyTime = EachDutyTime - HighDutyTime
    #依照次數與脈衝寬度與頻率控制步進馬達
    for i in range(int(Pulse_Count)):
        GPIO.output(PUL, GPIO.HIGH)
        time.sleep(HighDutyTime)
        GPIO.output(PUL, GPIO.LOW)
        time.sleep(LowDutyTime)

    return 'OK !'