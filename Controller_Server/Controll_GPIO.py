import sys
if sys.platform == "linux":
	import RPi.GPIO as GPIO
import time
import os
import pdb
import logging
from logging.handlers import RotatingFileHandler
from flask_sqlalchemy import SQLAlchemy
import configparser


class Controll:
	def __init__(self):
		config = configparser.ConfigParser()

		currentPath = os.path.dirname(os.path.abspath(__file__))
		config.read(currentPath + '/Sensor_Console/Config.ini')

		#讀取GPIO mapping關係的config檔
		self.GPIO_0 = int(config.get('GPIO Mapping','GPIO_0'))
		self.GPIO_1 = int(config.get('GPIO Mapping','GPIO_1'))
		self.GPIO_2 = int(config.get('GPIO Mapping','GPIO_2'))
		self.GPIO_3 = int(config.get('GPIO Mapping','GPIO_3'))
		self.GPIO_4 = int(config.get('GPIO Mapping','GPIO_4'))
		self.GPIO_5 = int(config.get('GPIO Mapping','GPIO_5'))
		self.GPIO_6 = int(config.get('GPIO Mapping','GPIO_6'))
		self.GPIO_7 = int(config.get('GPIO Mapping','GPIO_7'))
		self.GPIO_8 = int(config.get('GPIO Mapping','GPIO_8'))

		#共八個GPIO
		self.GPIONumber = {
			"GPIO_0" :self.GPIO_0,
			"GPIO_1" :self.GPIO_1,
			"GPIO_2" :self.GPIO_2,
			"GPIO_3" :self.GPIO_3,
			"GPIO_4" :self.GPIO_4,
			"GPIO_5" :self.GPIO_5,
			"GPIO_6" :self.GPIO_6,
			"GPIO_7" :self.GPIO_7,
			"GPIO_8" :self.GPIO_8,
		}

		log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
		#在樹莓派的位置跟開發環境的不一樣
		if sys.platform == "linux":
			logFile = "/home/pii/StepMotor.log"
		else:
			logFile = currentPath + '/StepMotor.log'
		my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=1024*1024, 
										backupCount=2, encoding=None, delay=0)
		my_handler.setFormatter(log_formatter)
		my_handler.setLevel(logging.DEBUG)


		self.logger = logging.getLogger('root')

		self.logger.setLevel(logging.DEBUG)

		self.logger.addHandler(my_handler)
		if sys.platform == "linux":
			GPIO.setwarnings(False)
			GPIO.setmode(GPIO.BCM)

			#初始化8個Pin的GPIO 設定為 out
			for GPIO_key in list(self.GPIONumber.keys()):
				Pin = self.GPIONumber[GPIO_key]
				GPIO.setup(Pin, GPIO.OUT)
	#傳入List 去個別GPIO開關處理
	def OpenGPIO(self,GPIO_Pins):
		self.logger.info("Enable Pin "+ ','.join([str(Pin) for Pin in GPIO_Pins])+"  GPIO.HEIGHT")
		#先開要開GPIO	
		#依照Mapping 關係去找到要啟動的Pin
		for GPIO_Pin in GPIO_Pins:
			if GPIO_Pin == "":
				continue
			Pin = self.GPIONumber["GPIO_"+str(GPIO_Pin)]
			if sys.platform == "linux":
				GPIO.output(Pin, GPIO.HIGH)
			self.logger.info("Pin "+str(Pin)+"  GPIO.HIGH")
		
		#列出所有可被操作的GPIO,待會要做相減diff操作
		GPIO_Pins_Total = [0,1,2,3,4,5,6,7]
		#diff後取得要關閉的GPIO,所有GPIO減去現在要開啟的GPIO=預計要關閉的GPIO
		OffGPIO = list(set(GPIO_Pins_Total) - set(GPIO_Pins))
		self.logger.info("Disable Pin "+ ','.join([str(Pin) for Pin in OffGPIO])+"  GPIO.LOW")
		#再關掉要關的GPIO,用diff的方式取得
		for GPIO_key in OffGPIO:
			Pin = self.GPIONumber["GPIO_"+str(GPIO_key)]
			if sys.platform == "linux":
				GPIO.output(Pin, GPIO.LOW)
			self.logger.info("Pin "+str(Pin)+"  GPIO.LOW")
		
		#運行完成
		return "OK"
	def closeAllGPIO(self):
		#關閉所有GPIO
		for GPIO_key in list(self.GPIONumber.keys()):
			Pin = self.GPIONumber[GPIO_key]
			if sys.platform == "linux":
				GPIO.output(Pin, GPIO.LOW)
			self.logger.info("Pin "+str(Pin)+"  GPIO.LOW")
if __name__ == "__main__":
	#初始化GPIO控制器
	Controll = Controll()
	Controll.OpenGPIO([1,2,3],5)