from flask import Flask,request
from flask import render_template
import time
import sys
import schedule as scheduler
import os
import requests
import json
import ftplib
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from flask_socketio import SocketIO, emit
import base64
from os.path import dirname, abspath 
import configparser
import threading
import os
d = dirname(dirname(abspath(__file__)))
sys.path.append(d)

config = configparser.ConfigParser()

currentPath = os.path.dirname(os.path.abspath(__file__))
config.read(currentPath + '/Config.ini')
DatabaseIP = config.get('Setting','DatabaseIP')
DBusername = config.get('Setting','DBusername')
DBpassword = config.get('Setting','DBpassword')

FTP_IP = config.get('Setting','FTP')
FTPUsername = config.get('Setting','FTPUsername')
FTPPassword = config.get('Setting','FTPPassword')
#------------------------------------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://'+DBusername+':'+DBpassword+'@'+DatabaseIP+':3306/sensordb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)




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

class schedule_day_of_time(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	time = db.Column(db.String)

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
#------------------------------------------------------------------------------------------------------

#簡易版網頁
@app.route("/simple")
def simple():
	return render_template('simple.html')


@app.route("/index")
def index():
	return render_template('index.html')

#取得當前指令的列表
@app.route("/queryCommandList")
def queryCommandList():
	#依照ID排序
	scheduleLi = schedule.query.order_by(schedule.id.asc()).all()
	Command_li = []
	for ele in scheduleLi:
		if ele != None:
			scheduleCommand = {
				'id' : ele.id,
				'PositionX' : ele.PositionX,
				'PositionY' : ele.PositionY,
			}
			Command_li.append(json.dumps(scheduleCommand))
	return json.dumps(Command_li)



#刪除工作指令
@app.route("/deleteMotorCommand")
def deleteMotorCommand():
	#使用ID來刪除物件
	_id = request.args.get('id')
	
	scheduleCommand = schedule.query.filter_by(id=_id).first()
	
	#刪除指定的DB指令
	db.session.delete(scheduleCommand)
	db.session.commit()
	return "OK"


#新增工作指令
@app.route("/saveMotorCommand")
def saveMotorCommand():
	#座標位置 X
	_PositionX = request.args.get('PositionX')

	#座標位置 Y
	_PositionY = request.args.get('PositionY')

	scheduleCommand = schedule(PositionX = int(_PositionX),
								PositionY = int(_PositionY),
								)
	 
	db.session.add(scheduleCommand)
	db.session.commit()
	return "OK"

#--------------------定時運行排程----------------------------------------------------------------------
#新增定時運行排程
@app.route("/savePlanRunning")
def savePlanRunning():
	#座標位置 X
	Time = request.args.get('Time')

	#座標位置 Y
	_PositionY = request.args.get('PositionY')

	schedule_day_of_time_Command = schedule_day_of_time(time = Time)
	 
	db.session.add(schedule_day_of_time_Command)
	db.session.commit()
	return "OK"

#取得當前定時運行排程列表
@app.route("/queryPlanList")
def queryPlanList():
	#依照ID排序
	day_schedule = schedule_day_of_time.query.order_by(schedule_day_of_time.id.asc()).all()
	Plan_li = []
	for ele in day_schedule:
		if ele != None:
			schedulePlan = {
				'id' : ele.id,
				'Time' : ele.time,
			}
			Plan_li.append(json.dumps(schedulePlan))
	return json.dumps(Plan_li)

#刪除定時運行指令
@app.route("/deleteTimeCommand")
def deleteTimeCommand():
	#使用ID來刪除物件
	_id = request.args.get('id')
	
	Command = schedule_day_of_time.query.filter_by(id=_id).first()
	
	#刪除指定的DB指令
	db.session.delete(Command)
	db.session.commit()
	return "OK"

#--------------------定時運行排程----------------------------------------------------------------------


#取得現在的馬達距離比例
@app.route("/queryDistanceOfTimeProportion")
def queryDistanceOfTimeProportion():
	StepMotor_config_A = config.query.filter_by(
		config_key='StepMotor_DistanceOfTimeProportion_A').first()
	StepMotor_config_B = config.query.filter_by(
		config_key='StepMotor_DistanceOfTimeProportion_B').first()

	#距離與馬達運轉時間比例
	proportionValue = {
		"StepMotor_DistanceOfTimeProport_A": {
			"width": StepMotor_config_A.width,
			"frequency": StepMotor_config_A.frequency,
			"count": StepMotor_config_A.count,
			"distance": StepMotor_config_A.distance
		},
		"StepMotor_DistanceOfTimeProport_B": {
			"width": StepMotor_config_B.width,
			"frequency": StepMotor_config_B.frequency,
			"count": StepMotor_config_B.count,
			"distance": StepMotor_config_B.distance
		}
	}
	return proportionValue

#讀取所有Sensor數值
@app.route("/ReadLux")
def ReadLux():
	Lux = sensor_lux.query.order_by(sensor_lux.DateTime.desc()).first()
	jsonLux = json.loads(Lux.Data.replace("'",'"'))
	jsonLux['時間'] = Lux.DateTime
	return jsonLux

@app.route("/ReadPH")
def ReadPH():
	PH = sensor_ph.query.order_by(sensor_ph.DateTime.desc()).first()
	jsonPH = json.loads(PH.Data.replace("'",'"'))
	return jsonPH

@app.route("/ReadEC")
def ReadEC():
	EC = sensor_ec.query.order_by(sensor_ec.DateTime.desc()).first()
	jsonEC = json.loads(EC.Data.replace("'",'"'))
	return jsonEC

#距離與持續時間的比例尺
@app.route("/UpdateDistanceOfTimeProportion")
def UpdateDistanceOfTimeProportion():
	#設定的類別，目前設定的是哪台步進馬達
	_SettingMotorNumber = request.args.get('SettingMotorNumber')

	width = request.args.get('value[width]')
	Frequency = request.args.get('value[Frequency]')
	Count = request.args.get('value[Count]')
	distance = request.args.get('value[distance]')
	
	StepMotor_configA = config.query.filter_by(
		config_key='StepMotor_DistanceOfTimeProportion_A').first()
	StepMotor_configB = config.query.filter_by(
		config_key ='StepMotor_DistanceOfTimeProportion_B').first()

	#因為現在是雙步進馬達，所以要依照馬達類別寫入
	if _SettingMotorNumber == "A":
		StepMotor_configA.width = int(width)
		StepMotor_configA.frequency = int(Frequency)
		StepMotor_configA.count = int(Count)
		StepMotor_configA.distance = int(distance)
	elif _SettingMotorNumber == "B":
		StepMotor_configB.width = int(width)
		StepMotor_configB.frequency = int(Frequency)
		StepMotor_configB.count = int(Count)
		StepMotor_configB.distance = int(distance)
	db.session.commit()
	return "OK"

#更新Jetson的IP位置
@app.route("/UpdateJetsonIP")
def UpdateJetsonIP():
	IP = request.args.get('IP')
	configIP = config.query.filter_by(
		config_key='JetsonIP').first()

	#如果沒有Jetson 的 IP 就新增一個	
	if configIP == None:
		configIP = config(config_key = "JetsonIP",
							value = IP)
		db.session.add(configIP)
	else:
		configIP.value = IP
	db.session.commit()
	return "OK"

#更新Jetson的IP位置
@app.route("/GetJetsonIP")
def GetJetsonIP():
	configIP = config.query.filter_by(
		config_key='JetsonIP').first()
	return configIP.value

@socketio.on('TakePic_event')
def TakePic_event(msg):
	JetsonIP = GetJetsonIP()
	if msg["data"] == "Take Pic!":
		try:
			response = requests.get("http://"+ JetsonIP +":8000/Pic", timeout = 30)
			socketio.emit('server_response', {'data': "TakePic :" + response.text})
		except:
			pass
	if "Upload" in msg["data"]:
		filename = msg["data"].replace("Upload :","")
		payload = {'filename': filename}

		#叫Nano上傳
		response = requests.get("http://"+ JetsonIP +":8000/upload", timeout = 30 , params=payload)
		
		#等確定上傳後，去下載剛剛上傳的檔案，並轉成base64
		ftp = ftplib.FTP(FTP_IP)
		ftp.login(FTPUsername, FTPPassword)
		last_file = ftp.nlst("/homes/admin/MVSImage")[-1]
		bufsize=1024
		fp = open(os.getcwd()+ "/" + filename,'wb')  
		ftp.retrbinary('RETR ' + last_file, fp.write, bufsize)
		fp.close()  
		
		with open(os.getcwd()+ "/" + filename, "rb") as image_file:
			encoded_string = base64.b64encode(image_file.read())

		#刪除剛剛下載下來的圖片檔
		os.remove(os.getcwd()+ "/" + filename)
		socketio.emit('server_response', {'data': "upload Pic result :" + response.text})
		socketio.emit('ImageStream', {'data': str(encoded_string, encoding = "utf-8")})
if __name__ == "__main__":
	app.run(host='0.0.0.0',port=8000)
	socketio.run(app)
