from flask import Flask,request
from flask import render_template
import time
import sys
import threading
import schedule
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

	if StepMotorNumber == "A" :
		#定義要控制哪個步進馬達
		#Set Enable
		ENA = 5

		#方向
		DIR = 6

		#脈衝
		PUL = 13
	#要控制代號B的步進馬達
	else if StepMotorNumber =="B":
		#Set Enable
		ENA = 17

		#方向
		DIR = 27

		#脈衝
		PUL = 22
	if sys.platform == "linux":
		status = Controll_2MD4850.RunStepping_MotorByInputSetNumber(ENA,DIR,PUL,Pulse_Width,Pulse_Count,PulseFrequency,direction)
		return str(status)
	elif sys.platform == "win32":
		return "在windows環境無法顯示此數值"

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
		status = Controll_input.ReturnLightControllStatus()
		return str(status)
	elif sys.platform == "win32":
		return "在windows環境無法顯示此數值"


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
	

