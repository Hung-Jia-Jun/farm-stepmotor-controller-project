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
from datetime import datetime,timedelta
from flask_socketio import SocketIO, emit
import base64
from os.path import dirname, abspath 
import configparser
import threading
import os
from openpyxl import load_workbook,Workbook
from flask_cors import cross_origin
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
remoteFolderPath = config.get('Setting','remoteFolderPath')
JetsonNanoIP = config.get('Setting','JetsonNanoIP')
#------------------------------------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://'+DBusername+':'+DBpassword+'@'+DatabaseIP+':3306/sensordb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
db.init_app(app)



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
	
	#因為一定要綁定一個 GPIO設定檔，所以要先創建一個空的
	GPIOCommand = GPIO(
			GPIO_Open = "",
			delayTime = 0,
			update_time = datetime.now()
		)
		
	db.session.add(GPIOCommand)
	db.session.commit()

	scheduleCommand = schedule(PositionX = int(_PositionX),
								PositionY = int(_PositionY),
								GPIO_uid = GPIOCommand.id,
								)
	 
	db.session.add(scheduleCommand)
	db.session.commit()
	return "OK"

#新增GPIO指令
@app.route("/saveGPIO")
def saveGPIO():
	#此次座標移動指令的ID
	_positionId = request.args.get('positionId')
	#新增GPIO指令
	_GPIO_Open = request.args.get('GPIO_Open')
	
	_delayTime = request.args.get('delayTime')

	positionTask = schedule.query.filter_by(id=_positionId).first()
	GPIOCommand = GPIO.query.filter_by(id = positionTask.GPIO_uid).first()
	GPIOCommand.GPIO_Open = _GPIO_Open
	GPIOCommand.delayTime = int(_delayTime)
	GPIOCommand.update_time = datetime.now()
	 
	db.session.add(GPIOCommand)
	db.session.commit()
	return "OK"

#讀取這次移動任務的GPIO指令
@app.route("/queryGPIOAndTakePic")
def queryGPIOAndTakePic():
	#從移動位置的ID去查資料表，找到關於這個移動位置所需要的GPIO詳細移動資訊
	_positionId = request.args.get('positionId')
	GPIO_schedule = schedule.query.filter_by(id=_positionId).first()
	Command = GPIO.query.filter_by(id=GPIO_schedule.GPIO_uid).first()
	GPIO_command = {
				'id':Command.id,
				'GPIO_Open' : Command.GPIO_Open,
				'delayTime':Command.delayTime,
			}
	return json.dumps(GPIO_command)
#--------------------運行排程時的GPIO設定跟此次任務是否要拍照----------------------------------------------------------------------



#--------------------定時運行排程----------------------------------------------------------------------
#更新這次排程是否要拍照的功能
@app.route("/updatePlanRunningTakePicStatus")
def updatePlanRunningTakePicStatus():
	#使用ID來刪除物件
	_id = request.args.get('id')
	_takePic = request.args.get('takePic')
	#js 過來的 true 要全小寫,python 的True要首字大寫
	if _takePic == "true":
		_takePic = True
	elif _takePic == "false":
		_takePic = False

	Command = schedule_day_of_time.query.filter_by(id=_id).first()
	#儲存是否要拍照的標記
	Command.takePic = _takePic
	db.session.commit()
	return "OK"
#新增定時運行排程
@app.route("/savePlanRunning")
def savePlanRunning():
	#座標位置 X
	Time = request.args.get('Time')
	_TakePic = request.args.get('TakePic')

	#js 過來的 true 要全小寫,python 的True要首字大寫
	if _TakePic == "true":
		_TakePic = True
	elif _TakePic == "false":
		_TakePic = False

	schedule_day_of_time_Command = schedule_day_of_time(time = Time,
														takePic = bool(_TakePic))
	 
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
				'takePic':ele.takePic,
			}
			Plan_li.append(json.dumps(schedulePlan))
	return json.dumps(Plan_li)
#--------------------定時運行排程----------------------------------------------------------------------

@app.route("/saveContinueAnywayStatus")
def saveContinueAnywayStatus():
	#儲存要不要強制執行任務的值
	_status = request.args.get('status')
	ContinueAnywayStatus = config.query.filter_by(
		config_key='continueAnyway').first()
	_status = _status.lower()
	if _status == "false":
		_status = False
	elif _status == "true":
		_status = True
	ContinueAnywayStatus.value = _status
	db.session.commit()
	return "OK"


@app.route("/queryContinueAnywayStatus")
def queryContinueAnywayStatus():
	#取得要不要強制執行任務的值
	ContinueAnywayStatus = config.query.filter_by(
		config_key='continueAnyway').first()
	_status = ContinueAnywayStatus.value
	#為了做js的 true false 轉換
	if _status == '0':
		_status = "false"
	elif _status == '1':
		_status = "true"
	return _status

#刪除定時運行指令
@app.route("/getSensorHistory")
def getSensorHistory():
	#使用ID來刪除物件
	From = request.args.get('From')
	End = request.args.get('End')

	End = (datetime.strptime(End, "%Y-%m-%d") + timedelta(1)).strftime("%Y-%m-%d")

	#去資料庫把符合日期時間的資料抓出來
	Between_lux = sensor_lux.query.filter(sensor_lux.DateTime.between(From,End))
	if Between_lux.count() > 0:
		#處理剛剛讀出來的DB歷史資料
		processHistoryData(Between_lux,"lux")

		Between_ec = sensor_ec.query.filter(sensor_ec.DateTime.between(From,End))
		#處理剛剛讀出來的DB歷史資料
		processHistoryData(Between_ec,"ec")

		Between_ph = sensor_ph.query.filter(sensor_ph.DateTime.between(From,End))
		#處理剛剛讀出來的DB歷史資料
		processHistoryData(Between_ph,"ph")
		return "OK"
	else:
		return "null"

def processHistoryData(DBInstance,filename):
	book = Workbook()
	sheet = book.active
	sheet.title = filename

	#從資料首行提取本Table中Data的所有Key當作Excel的標題首欄
	keys = json.loads(DBInstance[0].Data.replace("'", '"')).keys()

	keys_li = []
	for key in keys:
		keys_li.append(key)

	sheet.append(["時間"]+keys_li)
	for row in DBInstance:
		Values = json.loads(row.Data.replace("'", '"'))
		append_List = [row.DateTime]
		for key in keys_li:
			append_List.append(Values[key])
		sheet.append(append_List)
	
	book.save(os.path.dirname(os.path.abspath(__file__)) + '/static/'+ filename +'.xlsx')
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
	try:
		configIP = config.query.filter_by(
			config_key='JetsonIP').first()
		return configIP.value
	except:
		return JetsonNanoIP
@socketio.on('TakePic_event')
@cross_origin()
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
		last_file = sorted(ftp.nlst(remoteFolderPath))[-1]
		print (last_file)
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
