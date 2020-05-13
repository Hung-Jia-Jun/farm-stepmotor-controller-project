from flask import Flask,request
from flask import render_template
import time
import sys
import threading
import MySQLdb
import requests
import json
from flask_cors import CORS
import ftplib
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_socketio import SocketIO, emit


import base64
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

app = Flask(__name__)
CORS(app)
db = SQLAlchemy(app)

class sensor_lux(db.Model):
	DateTime = db.Column(db.String(255), primary_key=True)
	Data = db.Column(db.String(255))
	
	def __init__(self, DateTime, Data):
		self.DateTime = DateTime
		self.Data = Data

	def __repr__(self):
		return '<sensor_lux %r>' % self.content

class sensor_ec(db.Model):
	DateTime = db.Column(db.String(255), primary_key=True)
	Data = db.Column(db.String(255))

	def __init__(self, DateTime, Data):
		self.DateTime = DateTime
		self.Data = Data

	def __repr__(self):
		return '<sensor_ec %r>' % self.content

class sensor_ph(db.Model):
	DateTime = db.Column(db.String(255), primary_key=True)
	Data = db.Column(db.String(255))
  
	def __init__(self, DateTime, Data):
		self.DateTime = DateTime
		self.Data = Data

	def __repr__(self):
		return '<sensor_ph %r>' % self.content

#定時運行到指定位置的資料表定義
class schedule(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	PositionX = db.Column(db.Integer)
	PositionY = db.Column(db.Integer)

class config(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	config_key = db.Column(db.String(255))
	width = db.Column(db.Integer)
	frequency = db.Column(db.Integer)
	count = db.Column(db.Integer)
	distance = db.Column(db.Integer)

@app.route("/BrushlessDC_Motor")
def BrushlessDC_Motor():
	#方向 順時針轉為1,逆時鐘轉為0
	direction = request.args.get('direction')
	
	#毫秒為單位
	TimeMinSec = request.args.get('TimeMinSec')
	if sys.platform == "linux":
		status = Controll_ZM6405E.Run_BrushlessDC_Motor_ByInputSetNumber(TimeMinSec,direction)
		return str(status)
	elif sys.platform == "win32":
		return "在windows環境無法顯示此數值"

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
	if StepMotorNumber == "A" :
		#定義要控制哪個步進馬達
		#Set Enable
		ENA = 5

		#方向
		DIR = 6

		#脈衝
		PUL = 13
	#要控制代號B的步進馬達
	elif StepMotorNumber =="B":
		#Set Enable
		ENA = 17

		#方向
		DIR = 27

		#脈衝
		PUL = 22
		
		#Z
		EnableBrake = True
	if sys.platform == "linux":
		status = Controll_2MD4850.RunStepping_MotorByInputSetNumber(ENA,
																	DIR,
																	PUL,
																	Pulse_Width,
																	Pulse_Count,
																	PulseFrequency,
																	direction,
																	EnableBrake)
		return str(status)
	elif sys.platform == "win32":
		parameterEcho = {
			"direction" : direction,
			"Pulse_Width" : Pulse_Width,
			"PulseFrequency" : PulseFrequency,
			"Pulse_Count" : Pulse_Count,
			"StepMotorNumber" : StepMotorNumber,
		}
		return parameterEcho

def ReadLUX():
	if sys.platform == "linux":
		try:
			time.sleep(5)
			AtomTemperature , humidity , lux , C02 , AtmosphericPressure = RS485.ReadLUX()
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

			db.session.add(LuxData)
			db.session.commit()
			return _Data
		except Exception as e:
			print (e)
			pass
	elif sys.platform == "win32":
		data = {
					"大氣溫度" : "在windows環境無法顯示此數值",
					"濕度" :  "在windows環境無法顯示此數值",
					"光照" :  "在windows環境無法顯示此數值",
					"二氧化碳" :  "在windows環境無法顯示此數值",
					"大氣壓力" :  "在windows環境無法顯示此數值",
				}
		return data

def ReadEC():
	if sys.platform == "linux":
		try:
			time.sleep(5)
			temperature , EC = RS485.ReadEC()
			RS485.Clear()
			_Data = {
				"水溫" : str(temperature),
				"電導率" : str(EC),
			}
		
			print (_Data)
			ECData = sensor_ec(
				DateTime = str(datetime.now()) ,
				Data = str(_Data)
			)

			db.session.add(ECData)
			db.session.commit()
			return _Data
		except Exception as e:
			print (e)
	elif sys.platform == "win32":
		data = {
				"水溫" : "在windows環境無法顯示此數值",
				"電導率" :  "在windows環境無法顯示此數值",
			}
		return data

def ReadPH():
	if sys.platform == "linux":
		try:
			time.sleep(5)
			PH = RS485.ReadPH()
			if PH != None:
				RS485.Clear()
				_Data = {
					"PH" : str(PH)
				}
				print (_Data)

				PHData = sensor_ph(
					DateTime = str(datetime.now()) ,
					Data = str(_Data)
				)

				db.session.add(PHData)
				db.session.commit()
				return _Data
		except Exception as e:
			print (e)
	elif sys.platform == "win32":
		data = {
			"PH" : "在windows環境無法顯示此數值"
		}
		return data
					
#讀取光遮斷器數值
@app.route("/LightControllerStatus")
def LightControllerStatus():
	if sys.platform == "linux":
		status = Controll_input.ReturnZeroSensor()
		return str(status)
	elif sys.platform == "win32":
		return "在windows環境無法顯示此數值"

#將兩顆步進馬達設定到0的位置
def SetZeroPoint():
	#Z軸垂直制動器煞車開關
	EnableBrake = False

	StepMotor_config_A = config.query.filter_by(
		config_key='StepMotor_DistanceOfTimeProportion_A').first()
	StepMotor_config_B = config.query.filter_by(
		config_key='StepMotor_DistanceOfTimeProportion_B').first()

	#距離與馬達運轉時間比例
	StepMotor_config_A.width
	StepMotor_config_A.frequency
	StepMotor_config_A.count
	StepMotor_config_A.distance

	StepMotor_config_B.width
	StepMotor_config_B.frequency
	StepMotor_config_B.count
	StepMotor_config_B.distance

	#步進馬達A歸零，往後走無限個單位直到碰到零點
	RunningTime_A =  parseInt(1000) /  parseInt(StepMotor_config_A.distance)

 	#持續時間 = (次數 / 頻率) * 要運行距離是參考距離的幾倍
	Duration_A = parseFloat(parseInt(StepMotor_config_A.count) / parseInt(StepMotor_config_A.frequency)) * RunningTime_A
	
	#控制X軸馬達，代號A
	#Set Enable
	ENA = 5

	#方向
	DIR = 6

	#脈衝
	PUL = 13
	if sys.platform == "linux":
		status = Controll_2MD4850.RunStepping_MotorByInputSetNumber(ENA,
																	DIR,
																	PUL,
																	Pulse_Width,
																	Pulse_Count,
																	PulseFrequency,
																	direction,
																	EnableBrake)
		return str(status)
	elif sys.platform == "win32":
		parameterEcho = {
			"direction" : direction,
			"Pulse_Width" : Pulse_Width,
			"PulseFrequency" : PulseFrequency,
			"Pulse_Count" : Pulse_Count,
			"StepMotorNumber" : StepMotorNumber,
		}
		return parameterEcho

	#控制Y軸馬達，代號B
	#Set Enable
	ENA = 17

	#方向
	DIR = 27

	#脈衝
	PUL = 22
	
	#Z
	EnableBrake = True
	if sys.platform == "linux":
		status = Controll_2MD4850.RunStepping_MotorByInputSetNumber(ENA,
																	DIR,
																	PUL,
																	Pulse_Width,
																	Pulse_Count,
																	PulseFrequency,
																	direction,
																	EnableBrake)
		return str(status)
	elif sys.platform == "win32":
		parameterEcho = {
			"direction" : direction,
			"Pulse_Width" : Pulse_Width,
			"PulseFrequency" : PulseFrequency,
			"Pulse_Count" : Pulse_Count,
			"StepMotorNumber" : StepMotorNumber,
		}
		return parameterEcho

#啟用定時運行命令
def StartSchedule_Job():  
	#現在座標的計量暫存
	NowPositionX = 0
	NowPositionY = 0

	
	#依照ID排序，將所有命令取出來
	scheduleLi = schedule.query.order_by(schedule.id.asc()).all()
	for ele in scheduleLi:
		ele.PositionX
		ele.PositionY
def ReadLUX_Job():  
	print ("Start task ReadLUX_Job")
	try:
		ReadLUX()
	except:
		pass
	print ("End task ReadLUX_Job")
	
def ReadEC_Job():  
	print ("Start task ReadEC_Job")
	try:
		ReadEC()
	except:
		pass
	print ("End task ReadEC_Job")
	
def ReadPH_Job():  
	print ("Start task ReadPH_Job")
	try:
		ReadPH()
	except:
		pass
	print ("End task ReadPH_Job")
	
	

#每秒鐘都去確認現在是否有任務可以運行
def pendingJob():
	while True:
		schedule.run_pending()
		time.sleep(1)

if __name__ == "__main__":
	import schedule
	if sys.platform == "linux":
		RS485 = Read_RS485_Sensor_Lib.RS485()
	elif sys.platform == "win32":
		pass
	
	app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:HrK8Iww7hU0izq1H@192.168.11.4:3306/sensordb'
	db.init_app(app)
	db.create_all()

	schedule.every(15).minutes.do(ReadLUX_Job)  
	schedule.every(16).minutes.do(ReadEC_Job)  
	schedule.every(17).minutes.do(ReadPH_Job)  
	# 建立一個子執行緒，去監控任務運行狀態
	t = threading.Thread(target = pendingJob)

	# 執行該子執行緒
	t.start()
	app.run(host='0.0.0.0',port=8001)
	

