import RPi.GPIO as GPIO
import time
import pdb
import Controll_input
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import configparser
import os

# logging.basicConfig(filename="/home/pii/StepMotor.log", filemode="w", format="%(asctime)s %(name)s:%(levelname)s:%(message)s", datefmt="%d-%M-%Y %H:%M:%S", level=logging.DEBUG)
currentPath = os.path.dirname(os.path.abspath(__file__))
config = configparser.ConfigParser()
config.read(currentPath + '/Sensor_Console/Config.ini')

#如果在這個設定的時間內沒有回到原點，那就發信通知
TaskerErrorResponseSecond = config.get('Setting','TaskerErrorResponseSecond')
TaskerErrorResponseSecond = int(TaskerErrorResponseSecond)
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
		self.Clockwise  = '1'

		#逆時鐘
		self.AntiClockwise  = '0'
		
GPIONumber = {
	"A":{
		"ENA" : 5,
		"DIR" : 6,
		"PUL" : 13
	},
	"B":{
		"ENA" : 17,
		"DIR" : 16,
		"PUL" : 22
	}
}
def InitMotor():
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)

	#垂直煞車制動器 (1-unlock;0-lock)
	Brake = 25
	#設定制動器的GPIO
	GPIO.setup(Brake, GPIO.OUT)

	print ("start")
	#先鎖定煞車，後放鬆馬達出力
	for motor in list(GPIONumber.keys()):
		logger.info("Start Init step motor " + str(motor) + "-----------------------")
		#垂直煞車制動器 (1-unlock;0-lock)
		GPIO.output(Brake, GPIO.LOW)
		logger.info("lock Brake = "+str(Brake)+"  GPIO.LOW")

		#初始化的時候，關閉馬達出力
		ENA = GPIONumber[motor]["ENA"]
		GPIO.setup(ENA, GPIO.OUT)
		#Enable = GPIO.LOW (低電壓為啟動,高電位為disable)
		GPIO.output(ENA, GPIO.HIGH)
		logger.info("Disable StepMotor = "+ motor +"GPIO : "+str(ENA)+"  GPIO.HIGH")


class StepMotorControll:
	def __init__(self,MotorNumber):
		self.MotorNumber = MotorNumber
		self.GPIONumber = GPIONumber
		

	#使用座標來移動單顆步進馬達
	def SetPointToMove(self,nowPosition,TargetPosition,Pulse_Count,Distance):
		#算出目前座標點與目標點差距多少
		diffPosition = TargetPosition - nowPosition

		#儲存預計要移動的目標座標，等要Run的時候，就可以下判斷
		#判斷移動2分鐘後還是沒有碰到限位開關的時候要發信
		self.TargetPosition = TargetPosition

		MoveClockwise = 0
		if diffPosition > 0:
			#正轉
			MoveDirection = DR_TypeStruct().Clockwise
		else:
			#反轉
			MoveDirection = DR_TypeStruct().AntiClockwise

		#目標與基準距離的差距有多少
		MoveTime = abs(diffPosition / Distance) 

		#正反轉 and 返回到目標需要多少個脈波
		return MoveDirection , MoveTime * Pulse_Count
	#啟動步進馬達，在使用者輸入一個指定毫秒時
	def Run(self,Pulse_Width,Pulse_Count,PulseFrequency,DR_Type,EnableBrake):
		ENA = self.GPIONumber[self.MotorNumber]["ENA"]
		DIR = self.GPIONumber[self.MotorNumber]["DIR"]
		PUL = self.GPIONumber[self.MotorNumber]["PUL"]
	  
		#終端限位感測
		limitSensor1 = 8
		limitSensor2 = 9

		#零點感測器
		ZeroSensor1 = 10
		ZeroSensor2 = 11

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
		logger.info("Enable DIR = "+str(DIR)+" " + str(DR_Type))
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

		#馬達啟動時間
		startTime = None
		endTime = None
		try:
			#歸零復位模式，如果兩分鐘沒有成功復位，那就停止此次任務
			if self.TargetPosition < 0:
				startTime = datetime.now()
		except:
			pass
		#依照次數與脈衝寬度與頻率控制步進馬達
		for i in range(int(Pulse_Count)):
			# logger.debug(str(i) + ".   PUL = " + str(PUL) + str(" : GPIO.HIGH"))
			GPIO.output(PUL, GPIO.HIGH)
			time.sleep(HighDutyTime)
			# logger.debug("PUL = " + str(PUL) + str(" : GPIO.LOW"))
			GPIO.output(PUL, GPIO.LOW)
			time.sleep(LowDutyTime)
			#每50個脈波檢查一次
			if i % 5 == 0:
				print (i)
				#如果是正轉，碰到限位開關就要停止，只能反轉回去
				if DR_Type == DR_TypeStruct().Clockwise:
					if self.MotorNumber == "A":
						#限位開關偵測
						if Controll_input.ReturnSensorStatus(limitSensor1):
							logger.warning("X axis limit sensor trigger")
							return "X axis limit sensor trigger"
					if self.MotorNumber == "B":
						#限位開關偵測
						if Controll_input.ReturnSensorStatus(limitSensor2):
							logger.warning("Y axis limit sensor trigger")
							return "Y axis limit sensor trigger"

				#如果是反轉，碰到零點開關就要停止，只能正轉出去
				if DR_Type == DR_TypeStruct().AntiClockwise:
					if self.MotorNumber == "A":
						#零點開關偵測
						if Controll_input.ReturnSensorStatus(ZeroSensor1):
							logger.warning("X axis zero point sensor trigger")
							#Enable開關要關閉，不然長時間運行馬達會過熱
							logger.info("Disable ENA = "+str(ENA)+"  GPIO.HIGH")
							#Enable = GPIO.LOW (低電壓為啟動) 高電壓為ENA disable 
							GPIO.output(ENA, GPIO.HIGH)
							return "X axis zero point sensor trigger"
						else:
							try:
								#歸零復位模式，如果兩分鐘沒有成功復位，那就停止此次任務
								if self.TargetPosition < 0:
									endTime = datetime.now()
									#取時間差，當>2分鐘的時候，就發信警告
									diffTime = endTime - startTime
									if diffTime.seconds > TaskerErrorResponseSecond:
										startTime = None
										endTime = None
										logger.warning("Running X axis back to zero point task ,  but over 2 min still not trigger")
										return  "Running X axis back to zero point task ,  but over 2 min still not trigger"
							except:
								pass
					
					if self.MotorNumber == "B":
						#零點開關偵測
						if Controll_input.ReturnSensorStatus(ZeroSensor2):
							logger.warning("Y axis zero point sensor trigger")
							#鎖定垂直煞車制動器 (1-unlock;0-lock)
							GPIO.output(Brake, GPIO.LOW)

							#Enable開關要關閉，不然長時間運行馬達會過熱
							logger.info("Disable ENA = "+str(ENA)+"  GPIO.HIGH")
							#Enable = GPIO.LOW (低電壓為啟動) 高電壓為ENA disable 
							GPIO.output(ENA, GPIO.HIGH)
							
							return "Y axis zero point sensor trigger"
						else:
							try:
								#歸零復位模式，如果兩分鐘沒有成功復位，那就停止此次任務
								if self.TargetPosition < 0:
									endTime = datetime.now()
									#取時間差，當>2分鐘的時候，就發信警告
									diffTime = endTime - startTime
									if diffTime.seconds > TaskerErrorResponseSecond:
										startTime = None
										endTime = None
										logger.warning("Running Y axis back to zero point task ,  but over 2 min still not trigger")
										return  "Running Y axis back to zero point task ,  but over 2 min still not trigger"
							except:
								pass



		logger.info("Disable ENA = "+str(ENA)+"  GPIO.HIGH")
		#Enable開關要關閉
		# ，不然長時間運行馬達會過熱
		#Enable = GPIO.LOW (低電壓為啟動)
		GPIO.output(ENA, GPIO.HIGH)
		logger.info("---------------------------------------------------------")
		
		#鎖定
		#垂直煞車制動器 (1-unlock;0-lock)
		GPIO.output(Brake, GPIO.LOW)
		
		return 'OK !'

if __name__ == "__main__":
	pass