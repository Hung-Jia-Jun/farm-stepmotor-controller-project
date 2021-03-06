from flask import Flask,request
from flask import render_template
import time
import sys
import threading
import requests
import json
from flask_cors import CORS
import ftplib
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_socketio import SocketIO, emit
import schedule as scheduler
import base64
import logging
import configparser
from logging.handlers import RotatingFileHandler
import os
import EmailSender

#GPIO 控制
import Controll_GPIO

if sys.platform == "linux":
	#光遮斷器
	import Controll_input

	#無刷直流馬達
	import Controll_ZM6405E


	import Read_RS485_Sensor_Lib

	#步進馬達
	import Controll_2MD4850


elif sys.platform == "win32":
	pass

currentPath = os.path.dirname(os.path.abspath(__file__))
config = configparser.ConfigParser()
config.read(currentPath + '/Sensor_Console/Config.ini')
DatabaseIP = config.get('Setting','DatabaseIP')
DBusername = config.get('Setting','DBusername')
DBpassword = config.get('Setting','DBpassword')
TakePicStatus = config.get('Setting','TakePic')
JetsonNanoIP = config.get('Setting','JetsonNanoIP')

#------------------------------------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins='*')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://'+DBusername+':'+DBpassword+'@'+DatabaseIP+':3306/sensordb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

logFile = "/home/pii/StepMotor.log"

try:
	my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=500*1024*1024, 
									backupCount=5, encoding=None, delay=0)
	my_handler.setFormatter(log_formatter)
	my_handler.setLevel(logging.DEBUG)


	logger = logging.getLogger('root')

	logger.setLevel(logging.DEBUG)

	logger.addHandler(my_handler)
except:
	#windows環境
	pass


class config(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	config_key = db.Column(db.String(255))
	width = db.Column(db.Integer)
	frequency = db.Column(db.Integer)
	count = db.Column(db.Integer)
	distance = db.Column(db.Integer)
	value = db.Column(db.String(255))

class motor_position(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	number = db.Column(db.String(255))
	value = db.Column(db.Integer)

#定時運行到指定位置的資料表定義
class schedule(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	PositionX = db.Column(db.Integer)
	PositionY = db.Column(db.Integer)
	GPIO_uid = db.Column(db.Integer, db.ForeignKey('GPIO.id'), nullable=True)

class schedule_day_of_time(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	time = db.Column(db.String)
	takePic = db.Column(db.Boolean, unique=False, default=False)

class sensor_lux(db.Model):
	DateTime = db.Column(db.String(255), primary_key=True)
	Data = db.Column(db.String(255))

	def __init__(self, DateTime, Data):
		self.DateTime = DateTime
		self.Data = Data

class sensor_ec(db.Model):
	DateTime = db.Column(db.String(255), primary_key=True)
	Data = db.Column(db.String(255))

	def __init__(self, DateTime, Data):
		self.DateTime = DateTime
		self.Data = Data

class sensor_ph(db.Model):
	DateTime = db.Column(db.String(255), primary_key=True)
	Data = db.Column(db.String(255))

	def __init__(self, DateTime, Data):
		self.DateTime = DateTime
		self.Data = Data

class GPIO(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	update_time = db.Column(db.DateTime)
	GPIO_Open = db.Column(db.String(255))
	#延遲時間
	delayTime = db.Column(db.Float)
#------------------------------------------------------------------------------------------------------



@app.route("/BrushlessDC_Motor")
def BrushlessDC_Motor():
	#方向 順時針轉為1,逆時鐘轉為0
	direction = request.args.get('direction')

	#毫秒為單位
	TimeMinSec = request.args.get('TimeMinSec')
	if sys.platform == "linux":
		status = Controll_ZM6405E.Run_BrushlessDC_Motor_ByInputSetNumber(TimeMinSec,direction)
		return str(status)



@app.route("/Stepping_Motor")
def Stepping_Motor():

	#方向 順時針轉為1,逆時鐘轉為0
	direction = request.args.get('direction')

	#脈衝寬度
	Pulse_Width = request.args.get('Pulse_Width')

	#脈衝頻率
	PulseFrequency = request.args.get('PulseFrequency')

	#脈衝次數
	Pulse_Count = request.args.get('Pulse_Count')

	#步進馬達代號
	StepMotorNumber = request.args.get('StepMotorNumber')

	#Z軸垂直制動器煞車開關
	EnableBrake = False

	if StepMotorNumber =="B":
		#Z
		EnableBrake = True

	if sys.platform == "linux":
		#取得現在步進馬達的座標多少
		MotroCurrentPostion_A = motor_position.query.filter_by(number='A').first()
		MotroCurrentPostion_B = motor_position.query.filter_by(number='B').first()
		
		Step = Controll_2MD4850.StepMotorControll(StepMotorNumber)
		status = Step.Run(Pulse_Width,
							Pulse_Count,
							PulseFrequency,
							direction,
							EnableBrake)
		#碰到零點感測器就表示已經回0了 (X軸)
		if "X axis zero point sensor trigger" in status:
			MotroCurrentPostion_A.value = 0
			db.session.commit()
		#碰到零點感測器就表示已經回0了 (Y軸)
		if "Y axis zero point sensor trigger" in status:
			MotroCurrentPostion_B.value = 0
			db.session.commit()
		db.session.commit()
		return str(status)
	elif sys.platform == "win32":
		parameterEcho = {
			"direction" : direction,
			"Pulse_Width" : Pulse_Width,
			"PulseFrequency" : PulseFrequency,
			"Pulse_Count" : Pulse_Count,
			"StepMotorNumber" : StepMotorNumber,
			"ENA" : str(ENA),
			"DIR" : str(DIR),
			"PUL" : str(PUL),
		}
		return parameterEcho

def ReadLUX(checkTask=False):
	if sys.platform == "linux":
		try:
			time.sleep(5)
			AtomTemperature , humidity , lux , C02 , AtmosphericPressure = RS485.ReadLUX()
			if "Fail" in str(AtomTemperature):
				#確認Sensor存活狀態的任務
				if checkTask == True:
					EmailSender.Send("三合一感測器發生問題，未擷取到資料")
					logger.error("Sensor檢查任務 - 三合一感測器已發Mail通知")

			RS485.Clear()
			_Data = {
				"大氣溫度" : str(AtomTemperature),
				"濕度" : str(humidity),
				"光照" : str(lux),
				"二氧化碳" : str(C02),
				"大氣壓力" : str(AtmosphericPressure),
			}

			print (_Data)
			LuxData = sensor_lux(
				DateTime = str(datetime.now()) ,
				Data = str(_Data)
			)
			try:
				db.session.add(LuxData)
				db.session.commit()
			except:
				print ("DB發生問題，無法讀寫內容")
				logger.error("DB發生問題，無法讀寫內容")

			return _Data
		except:
			#確認Sensor存活狀態的任務
			if checkTask == True:
				EmailSender.Send("三合一感測器發生問題，未擷取到資料")
				logger.error("Sensor檢查任務 - 三合一感測器已發Mail通知")
			logger.error("Sensor檢查任務 - 三合一感測器發生問題，未擷取到資料")
			_Data = {
				"大氣溫度" : "0",
				"濕度" : "0",
				"光照" : "0",
				"二氧化碳" : "0",
				"大氣壓力" : "0",
			}
			return _Data

def ReadEC(checkTask=False):
	if sys.platform == "linux":
		try:
			time.sleep(5)
			temperature , EC = RS485.ReadEC()
			RS485.Clear()
			_Data = {
				"水溫" : str(temperature),
				"電導率" : str(EC),
			}

			#確認Sensor存活狀態的任務
			if checkTask == True:
				if "Fail" in str(temperature):
					EmailSender.Send("EC電導感測器發生問題，未擷取到資料")
					logger.error("Sensor檢查任務 - EC電導感測器已發Mail通知")
					logger.error("Sensor檢查任務 - EC電導感測器發生問題，未擷取到資料")
					_Data = {
						"水溫" : "0",
						"電導率" : "0",
					}
					return _Data
				else:
					return _Data

			
			print (_Data)
			ECData = sensor_ec(
				DateTime = str(datetime.now()) ,
				Data = str(_Data)
			)

			try:
				db.session.add(ECData)
				db.session.commit()
			except:
				print ("DB發生問題，無法讀寫內容")
				logger.error("DB發生問題，無法讀寫內容")
				
			return _Data
		except:
			#確認Sensor存活狀態的任務
			if checkTask == True:
				EmailSender.Send("EC電導感測器發生問題，未擷取到資料")
				logger.error("Sensor檢查任務 - EC電導感測器已發Mail通知")
			_Data = {
				"水溫" : "0",
				"電導率" : "0",
			}
			return _Data

def ReadPH(checkTask=False):
	if sys.platform == "linux":
		try:
			time.sleep(5)
			PH = RS485.ReadPH()
			if PH != None:
				RS485.Clear()
				_Data = {
					"PH" : str(PH)
				}

				#確認Sensor存活狀態的任務
				if checkTask == True:
					if "Fail" in str(PH):
						EmailSender.Send("PH感測器發生問題，未擷取到資料")
						logger.error("Sensor檢查任務 - PH感測器已發Mail通知")
						logger.error("Sensor檢查任務 - PH感測器發生問題，未擷取到資料")
						_Data = {
							"PH" : "0"
						}
						return _Data
					else:
						return _Data

				print (_Data)

				PHData = sensor_ph(
					DateTime = str(datetime.now()) ,
					Data = str(_Data)
				)

				try:
					db.session.add(PHData)
					db.session.commit()
				except:
					print ("DB發生問題，無法讀寫內容")
					logger.error("DB發生問題，無法讀寫內容")
				return _Data
		except:
			#確認Sensor存活狀態的任務
			if checkTask == True:
				EmailSender.Send("PH感測器發生問題，未擷取到資料")
				logger.error("Sensor檢查任務 - PH感測器已發Mail通知")
			print (e)
			_Data = {
				"PH" : "0"
			}
			return _Data

#讀取光遮斷器數值
@app.route("/LightControllerStatus")
def LightControllerStatus():
	if sys.platform == "linux":
		#終端限位感測
		limitSensor1 = 8
		limitSensor2 = 9

		#零點感測器
		ZeroSensor1 = 10
		ZeroSensor2 = 11
		status = {
			"limitSensor1" : False,
			"limitSensor2" : False,
			"ZeroSensor1" : False,
			"ZeroSensor2" : False,
		}
		#如果是正轉，碰到限位開關就要停止，只能反轉回去
		#限位開關偵測
		if Controll_input.ReturnSensorStatus(limitSensor1):
			logger.warning("X axis limit sensor trigger")
			status["limitSensor1"] = True
		#限位開關偵測
		if Controll_input.ReturnSensorStatus(limitSensor2):
			logger.warning("Y axis limit sensor trigger")
			status["limitSensor2"] = True
		#如果是反轉，碰到零點開關就要停止，只能正轉出去
		#零點開關偵測
		if Controll_input.ReturnSensorStatus(ZeroSensor1):
			logger.warning("X axis zero point sensor trigger")
			status["ZeroSensor1"] = True

		#零點開關偵測
		if Controll_input.ReturnSensorStatus(ZeroSensor2):
			logger.warning("Y axis zero point sensor trigger")
			status["ZeroSensor2"] = True

		return json.dumps(status)
#將兩顆步進馬達設定到指定的位置
def SetPoint(TargetX,TargetY,takePic = False):
	#讀取資料庫設定檔
	StepMotor_config_A = config.query.filter_by(
		config_key='StepMotor_DistanceOfTimeProportion_A').first()
	StepMotor_config_B = config.query.filter_by(
		config_key='StepMotor_DistanceOfTimeProportion_B').first()


	Step_A = Controll_2MD4850.StepMotorControll("A")
	Step_B = Controll_2MD4850.StepMotorControll("B")

	#取得現在步進馬達的座標多少
	MotroCurrentPostion_A = motor_position.query.filter_by(number='A').first()
	MotroCurrentPostion_B = motor_position.query.filter_by(number='B').first()
	if MotroCurrentPostion_A.value < 0 and TargetX > 0:
		MotroCurrentPostion_A.value = 0
		db.session.commit()
	if MotroCurrentPostion_B.value < 0 and TargetY > 0:
		MotroCurrentPostion_B.value = 0
		db.session.commit()
	#算出與目標點差距有幾個脈波
	Direction_X , Pulse_X_Count = Step_A.SetPointToMove(nowPosition = MotroCurrentPostion_A.value,
														TargetPosition = TargetX,
														Pulse_Count = StepMotor_config_A.count,
														Distance = StepMotor_config_A.distance,
														)

	Direction_Y , Pulse_Y_Count = Step_B.SetPointToMove(nowPosition = MotroCurrentPostion_B.value,
														TargetPosition = TargetY,
														Pulse_Count = StepMotor_config_B.count,
														Distance = StepMotor_config_B.distance,
														)

	MotroCurrentPostion_A.value = TargetX
	MotroCurrentPostion_B.value = TargetY
	

	#如果碰到0點歸零開關就會停止
	if sys.platform == "linux":
		#Z軸垂直制動器煞車開關
		_EnableBrake = False
		status_A = Step_A.Run(  Pulse_Width = StepMotor_config_A.width,
								Pulse_Count = Pulse_X_Count,
								PulseFrequency = StepMotor_config_A.frequency,
								DR_Type = Direction_X,
								EnableBrake = _EnableBrake)
		#正常操作下，不應該碰到限位開關，如果碰到了，就要回到原點
		if "limit sensor trigger" in status_A:
			#X,Y軸都要回原點
			status_A = Step_A.Run(  Pulse_Width = StepMotor_config_A.width,
									Pulse_Count = 99999,
									PulseFrequency = StepMotor_config_A.frequency,
									DR_Type = '0',
									EnableBrake = _EnableBrake)
			status_B = Step_B.Run(  Pulse_Width = StepMotor_config_B.width,
									Pulse_Count = 99999,
									PulseFrequency = StepMotor_config_B.frequency,
									DR_Type = '0',
									EnableBrake = _EnableBrake)

			#碰到零點感測器就表示已經回0了 (X軸)
			if "axis zero point sensor trigger" in status_A:
				MotroCurrentPostion_A.value = 0
				db.session.commit()
			#碰到零點感測器就表示已經回0了 (Y軸)
			if "axis zero point sensor trigger" in status_B:
				MotroCurrentPostion_B.value = 0
				db.session.commit()
			#回到原點後，略過此次任務
			return "Pass this mission"

		#碰到零點感測器就表示已經回0了
		if "axis zero point sensor trigger" in status_A:
			MotroCurrentPostion_A.value = 0
			db.session.commit()

		#在倒退運行的時候，連續運行2分鐘，但都沒碰到限位開關
		#那就發mail通知
		if "Running X axis back to zero point task ,  but over 2 min still not trigger" in status_A:
			EmailSender.Send("歸零任務發生問題，請檢查X軸馬達位置")
			#但因為現在機器以為A馬達在-999的位置，這樣下次嘗試歸零的時候就無法進入判斷回圈
			#所以就先設定0吧
			MotroCurrentPostion_A.value = 0
			db.session.commit()
			#回到原點這件事發生錯誤
			return "An error occurred when returning to the origin"

		#-------------------------步進馬達 B ----------------------------------
		#Z軸要放開煞車
		_EnableBrake = True
		status_B = Step_B.Run(  Pulse_Width = StepMotor_config_B.width,
								Pulse_Count = Pulse_Y_Count,
								PulseFrequency = StepMotor_config_B.frequency,
								DR_Type = Direction_Y,
								EnableBrake = _EnableBrake)
		#正常操作下，不應該碰到限位開關，如果碰到了，就要回到原點
		if "limit sensor trigger" in status_B:
			#X,Y軸都要回原點
			status_A = Step_A.Run(  Pulse_Width = StepMotor_config_A.width,
									Pulse_Count = 99999,
									PulseFrequency = StepMotor_config_A.frequency,
									DR_Type = '0',
									EnableBrake = _EnableBrake)
			status_B = Step_B.Run(  Pulse_Width = StepMotor_config_B.width,
									Pulse_Count = 99999,
									PulseFrequency = StepMotor_config_B.frequency,
									DR_Type = '0',
									EnableBrake = _EnableBrake)

			#碰到零點感測器就表示已經回0了 (X軸)
			if "axis zero point sensor trigger" in status_A:
				MotroCurrentPostion_A.value = 0
				db.session.commit()
			#碰到零點感測器就表示已經回0了 (Y軸)
			if "axis zero point sensor trigger" in status_B:
				MotroCurrentPostion_B.value = 0
				db.session.commit()

			#回到原點後，略過此次任務
			return "Pass this mission"

		#碰到零點感測器就表示已經回0了
		if "axis zero point sensor trigger" in status_B:
			MotroCurrentPostion_B.value = 0
			db.session.commit()

		#在倒退運行的時候，連續運行2分鐘，但都沒碰到限位開關
		#那就發mail通知
		if "Running Y axis back to zero point task ,  but over 2 min still not trigger" in status_B:
			print("歸零任務發生問題，請檢查Y軸馬達位置")
			EmailSender.Send("歸零任務發生問題，請檢查Y軸馬達位置")
			#但因為現在機器以為B馬達在-999的位置，這樣下次嘗試歸零的時候就無法進入判斷回圈
			#所以就先設定0吧
			MotroCurrentPostion_B.value = 0
			db.session.commit()
			return "An error occurred when returning to the origin"

		db.session.commit()

		#回原點歸零的那個任務不拍照
		if int(TargetX) > 0 and int(TargetY) > 0:
			time.sleep(6)
			logger.info("TakePic mode : " + TakePicStatus)
			#Global 的拍照任務，當Global的拍照任務都設定為Disable
			#那不管哪個Schedule都要略過
			#所以只有Global 與每個Schedule任務都為 True的時候才會拍照
			if TakePicStatus == "Enable":
				if takePic == True:
					#到達定點後拍照
					TakePic()
		return str(status_A + status_B)

	elif sys.platform == "win32":
		parameterEcho = {
			"direction" : direction,
			"Pulse_Width" : Pulse_Width,
			"PulseFrequency" : PulseFrequency,
			"Pulse_Count" : Pulse_Count,
			"StepMotorNumber" : StepMotorNumber,
		}
		return parameterEcho

#啟動資料庫記錄的GPIO
def ActiveGPIO(PinOpenLi):
	#GPIO 控制
	Controll = Controll_GPIO.Controll()
	#啟動GPIO,並且一段時間後停止
	Controll.OpenGPIO(PinOpenLi)
	return "OK"

#啟動資料庫記錄的GPIO
@app.route("/ActiveGPIOByRequests")
def ActiveGPIOByRequests():
	PinOpenLi = request.args.get('PinOpenLi')
	PinOpenLi = PinOpenLi.split(",")
	#GPIO 控制
	Controll = Controll_GPIO.Controll()
	#啟動GPIO,並且一段時間後停止
	Controll.OpenGPIO(PinOpenLi)
	return "OK"

def GetJetsonIP():
	try:
		configIP = config.query.filter_by(
			config_key='JetsonIP').first()
		return configIP.value
	except:
		return JetsonNanoIP
#呼叫Jetson Nano拍照
def TakePic():
	JetsonIP = GetJetsonIP()
	response = requests.get("http://" + JetsonIP + ":8000/Pic", timeout = 30)
	
	filename = response.text
	payload = {'filename': filename}
	#叫Nano上傳
	uploadResponse = requests.get("http://" + JetsonIP + ":8000/upload", timeout = 30 , params=payload)
	logger.info("Schedule take picture result : " + uploadResponse.text)
	return response.text,uploadResponse.text

def ReadLUX_Job():
	print ("Start task ReadLUX_Job")
	logger.info("Start task ReadLUX_Job")
	try:
		ReadLUX()
	except:
		logger.error("Error read job")
		pass
	print ("End task ReadLUX_Job")
	logger.info("End task ReadLUX_Job")

def ReadEC_Job():
	print ("Start task ReadEC_Job")
	logger.info("Start task ReadEC_Job")
	try:
		ReadEC()
	except:
		logger.error("Error read job")
		pass
	print ("End task ReadEC_Job")
	logger.info("End task ReadEC_Job")

def ReadPH_Job():
	print ("Start task ReadPH_Job")
	logger.info("Start task ReadPH_Job")
	try:
		ReadPH()
	except:
		logger.error("Error read job")
		pass
	print ("End task ReadPH_Job")
	logger.info("End task ReadPH_Job")

#啟用定時運行命令
def StartSchedule_Job(takePic):
	try:
		#依照ID排序，將所有命令取出來
		scheduleLi = schedule.query.order_by(schedule.id.asc()).all()
		for ele in scheduleLi:
			logger.info("Start Schedule Job: (" +str(ele.PositionX) + "," +str(ele.PositionY) + ")" + "takePic : " + str(takePic))
			#找到這次要開啟的GPIO列表
			GPIOCommand = GPIO.query.filter_by(id = ele.GPIO_uid).first()
			
			#切分準備要開啟的GPIO列表
			GPIO_OpenLi =  GPIOCommand.GPIO_Open.split(",")
			ActiveGPIO(GPIO_OpenLi)

			#延遲一段時間後才開始移動
			time.sleep(GPIOCommand.delayTime)

			
			#GPIO運行結束後，才會進行移動任務
			#並且依照此次是否要拍照的任務決定要不要拍照
			result = SetPoint(ele.PositionX,ele.PositionY,takePic = takePic)
			#當偵測到回原點這件事情發生錯誤
			#就略過之後所有的任務
			if result == "An error occurred when returning to the origin":
				isContinueAnyway = config.query.filter_by(config_key='continueAnyway').first().value
				
				#不要強制執行的話為 0
				#這樣這個任務就會停下來了
				if isContinueAnyway == '0':
					#關閉所有GPIO，防止出錯了還在灑水
					ActiveGPIO([])
					return "An error occurred when returning to the origin"
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)
#立即運行剛剛設定的指令
@app.route("/runCommandList")
def runCommandList():
	StartSchedule_Job(takePic = False)
	return "OK"

#立即運行剛剛設定的指令
@app.route("/forceRestart")
#更新步進馬達的移動任務
def forceRestart():
	os.popen("sudo -S %s"%('systemctl restart Controller_Server'), 'w').write('888')
	return 'OK'
#立即運行剛剛設定的指令
@app.route("/updateMotorJob")
#更新步進馬達的移動任務
def updateMotorJob():
	nowTime = datetime.now().strftime("%H:%M")
	logger.info("任務排程檢查時間 : " + nowTime)
	print ("任務排程檢查時間 : " + nowTime)
	#每日健康檢查2次
	if nowTime == '08:05':
		logger.info("Sensor檢查任務 - 啟動")
		sensorChecker()
		databaseChecker()
		print ("Sensor檢查任務 - 結束")
		logger.info("Sensor檢查任務 - 結束")
	if nowTime == '15:05':
		logger.info("Sensor檢查任務 - 啟動")
		sensorChecker()
		databaseChecker()
		print ("Sensor檢查任務 - 結束")
		logger.info("Sensor檢查任務 - 結束")

	try:

		#依照ID排序
		day_schedule = schedule_day_of_time.query.order_by(schedule_day_of_time.id.asc()).all()

		Plan_li = []
		for ele in day_schedule:
			if ele != None:
				#到指定時間後，運行重複運行指令
				if nowTime == ele.time:
					StartSchedule_Job(takePic = ele.takePic)
		return "OK"
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)
		print ("DB錯誤，無法運行馬達排程任務")
		logger.error("DB錯誤，無法運行馬達排程任務")
		return "OK"
			

def databaseChecker():
	try:
		day_schedule = schedule_day_of_time.query.order_by(schedule_day_of_time.id.asc()).all()
	except:
		print ("DB發生問題，無法讀寫內容")
		logger.error("DB發生問題，無法讀寫內容")
		EmailSender.Send("DB發生問題，無法讀寫內容")
		logger.info("DB檢查任務 - 已發DB錯誤的Mail通知")
def sensorChecker():
	try:
		ReadLUX(checkTask=True)
		ReadEC(checkTask=True)
		ReadPH(checkTask=True)
	except:
		print ("Sensor檢查任務 - 有部分Sensor失敗")
		logger.error("Sensor檢查任務 - 有部分Sensor失敗")

#每分鐘都去確認現在是否有"移動"任務可以運行
def pendingJob():
	while True:
		logger.info("run pending")
		scheduler.run_pending()
		updateMotorJob()
		logger.info("end pending search")
		time.sleep(60)

if __name__ == "__main__":
	if sys.platform == "linux":
		try:
			RS485 = Read_RS485_Sensor_Lib.RS485()
		except:
			logger.info("RS485 reader dongle error")
			pass
	elif sys.platform == "win32":
		pass

	db.init_app(app)
	try:
		db.create_all()
	except:
		print ("DB發生問題，無法讀寫內容")
		logger.error("DB發生問題，無法讀寫內容")
		EmailSender.Send("DB發生問題，無法讀寫內容")
		
	#檢查Sensor
	sensorChecker()

	print (__name__ , "db.create_all")
	#啟動Server後，先鎖定煞車，後放鬆馬達出力
	Controll_2MD4850.InitMotor()


	# 建立一個子執行緒，去監控任務運行狀態
	t = threading.Thread(target = pendingJob)

	# 執行該子執行緒
	t.start()


	scheduler.every(15).minutes.do(ReadLUX_Job)
	scheduler.every(16).minutes.do(ReadEC_Job)
	scheduler.every(17).minutes.do(ReadPH_Job)
	
	ReadLUX_Job()
	ReadEC_Job()
	ReadPH_Job()
	
	app.run(host='0.0.0.0',port=8001)


