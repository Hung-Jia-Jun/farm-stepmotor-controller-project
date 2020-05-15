import RPi.GPIO as GPIO
import time
import pdb
import Controll_input
import logging
from logging.handlers import RotatingFileHandler

# logging.basicConfig(filename="/home/pii/StepMotor.log", filemode="w", format="%(asctime)s %(name)s:%(levelname)s:%(message)s", datefmt="%d-%M-%Y %H:%M:%S", level=logging.DEBUG)
    

log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

logFile = "/home/pii/StepMotor.log"

my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=1024*1024, 
                                 backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.DEBUG)

logger = logging.getLogger('root')
logger.setLevel(logging.DEBUG)

logger.addHandler(my_handler)

    
class DR_TypeStruct:
    def __init__(self):
        #順時鐘
        self.Clockwise  = 1

        #逆時鐘
        self.AntiClockwise  = 0
class StepMotorControll:
    def __init__(self,MotorNumber):
        self.MotorNumber = MotorNumber
        self.GPIONumber = {
            "A":{
                "ENA" : 5,
                "DIR" : 6,
                "PUL" : 13
            },
            "B":{
                "ENA" : 17,
                "DIR" : 27,
                "PUL" : 22
            }
        }

    #使用座標來移動單顆步進馬達
    def SetPointToMove(self,nowPosition,TargetPosition,Pulse_Count,Distance):
        #算出目前座標點與目標點差距多少
        diffPosition = Position - nowPosition

        MoveClockwise = 0
        if diffPosition > 0:
            #正轉
            MoveDirection = DR_TypeStruct().Clockwise
        else:
            #反轉
            MoveDirection = DR_TypeStruct().AntiClockwise

        #目標與基準距離的差距有多少
        MoveTime = diffPosition / Distance 

        #正反轉 and 返回到目標需要多少個脈波
        return MoveDirection , MoveTime * Pulse_Count
    #啟動步進馬達，在使用者輸入一個指定毫秒時
    def Run(self,Pulse_Width,Pulse_Count,PulseFrequency,DR_Type,EnableBrake):
        ENA = self.GPIONumber[self.MotorNumber]["ENA"]
        DIR = self.GPIONumber[self.MotorNumber]["DIR"]
        PUL = self.GPIONumber[self.MotorNumber]["PUL"]
        #終端限位感測
        limitSensor1 = 23
        limitSensor2 = 24

        #零點感測器
        ZeroSensor1 = 0
        ZeroSensor2 = 26

        #垂直煞車制動器 (1-unlock;0-lock)
        Brake = 25


        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(ENA, GPIO.OUT)
        GPIO.setup(DIR, GPIO.OUT)
        GPIO.setup(PUL, GPIO.OUT)

        #設定制動器的GPIO
        GPIO.setup(Brake, GPIO.OUT)
        
        if EnableBrake == True:
            #垂直煞車制動器 (1-unlock;0-lock)
            GPIO.output(Brake, GPIO.HIGH)
        else:
            #鎖定
            #垂直煞車制動器 (1-unlock;0-lock)
            GPIO.output(Brake, GPIO.LOW)

        logger.info("Enable ENA = "+str(ENA)+"  GPIO.LOW")
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
        
        logger.info("Start Action : " + str(self.MotorNumber))
        logger.debug("Pulse_Width : " + str(Pulse_Width))
        logger.debug("Pulse_Count : " + str(Pulse_Count))
        logger.debug("PulseFrequency : " + str(PulseFrequency))
        logger.debug("DR_Type : " + str(DR_Type))
        logger.info("---------------------------------------------------------")
        logger.debug("EnableBrake : " + str(EnableBrake))
        logger.debug("Pulse_Count : " + str(Pulse_Count))
        logger.debug("HighDutyTime : " + str(HighDutyTime))
        logger.debug("LowDutyTime : " + str(LowDutyTime))
       
        
        
        
        
        #依照次數與脈衝寬度與頻率控制步進馬達
        for i in range(int(Pulse_Count)):
            logger.debug(str(i) + ".   PUL = " + str(PUL) + str(" : GPIO.HIGH"))
            GPIO.output(PUL, GPIO.HIGH)
            time.sleep(HighDutyTime)
            logger.debug("PUL = " + str(PUL) + str(" : GPIO.LOW"))
            GPIO.output(PUL, GPIO.LOW)
            time.sleep(LowDutyTime)
            
            #如果是正轉，碰到限位開關就要停止，只能反轉回去
            if DR_Type == DR_TypeStruct().Clockwise:
                #限位開關偵測
                if Controll_input.ReturnSensorStatus(limitSensor1):
                    logger.warning("X axis limit sensor trigger")
                    return "X axis limit sensor trigger"

                #限位開關偵測
                if Controll_input.ReturnSensorStatus(limitSensor2):
                    logger.warning("Y axis limit sensor trigger")
                    return "Y axis limit sensor trigger"

            #如果是反轉，碰到零點開關就要停止，只能正轉出去
            if DR_Type == DR_TypeStruct().AntiClockwise:
                #零點開關偵測
                if Controll_input.ReturnSensorStatus(ZeroSensor1):
                    logger.warning("X axis zero point sensor trigger")
                    return "X axis zero point sensor trigger"

                #零點開關偵測
                if Controll_input.ReturnSensorStatus(ZeroSensor2):
                    logger.warning("Y axis zero point sensor trigger")
                    return "Y axis zero point sensor trigger"
                



        logger.info("Disable ENA = "+str(ENA)+"  GPIO.HIGH")
        #Enable開關要關閉，不然長時間運行馬達會過熱
        #Enable = GPIO.LOW (低電壓為啟動)
        GPIO.output(ENA, GPIO.HIGH)
        logger.info("---------------------------------------------------------")
        
        #鎖定
        #垂直煞車制動器 (1-unlock;0-lock)
        GPIO.output(Brake, GPIO.LOW)

        return 'OK !'