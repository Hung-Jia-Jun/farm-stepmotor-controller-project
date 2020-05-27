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
from logging.handlers import RotatingFileHandler
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



#------------------------------------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:HrK8Iww7hU0izq1H@192.168.11.4:3306/sensordb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

logFile = "/home/pii/StepMotor.log"

my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=1024*1024, 
                                 backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.DEBUG)


logger = logging.getLogger('root')

logger.setLevel(logging.DEBUG)

logger.addHandler(my_handler)



class config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(255))
    width = db.Column(db.Integer)
    frequency = db.Column(db.Integer)
    count = db.Column(db.Integer)
    distance = db.Column(db.Integer)

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

    if StepMotorNumber =="B":
        #Z
        EnableBrake = True

    if sys.platform == "linux":
        Step = Controll_2MD4850.StepMotorControll(StepMotorNumber)
        status = Step.Run(Pulse_Width,
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
            "ENA" : str(ENA),
            "DIR" : str(DIR),
            "PUL" : str(PUL),
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
        #終端限位感測
        limitSensor1 = 23
        limitSensor2 = 24

        #零點感測器
        ZeroSensor1 = 0
        ZeroSensor2 = 26
        status = "None"
        #如果是正轉，碰到限位開關就要停止，只能反轉回去
        #限位開關偵測
        if Controll_input.ReturnSensorStatus(limitSensor1):
            logger.warning("X axis limit sensor trigger")
            status = "X axis limit sensor trigger"

        #限位開關偵測
        if Controll_input.ReturnSensorStatus(limitSensor2):
            logger.warning("Y axis limit sensor trigger")
            status = "Y axis limit sensor trigger"

        #如果是反轉，碰到零點開關就要停止，只能正轉出去
        #零點開關偵測
        if Controll_input.ReturnSensorStatus(ZeroSensor1):
            logger.warning("X axis zero point sensor trigger")
            status = "X axis zero point sensor trigger"

        #零點開關偵測
        if Controll_input.ReturnSensorStatus(ZeroSensor2):
            logger.warning("Y axis zero point sensor trigger")
            status = "Y axis zero point sensor trigger"

        return str(status)
    elif sys.platform == "win32":
        return "在windows環境無法顯示此數值"

#將兩顆步進馬達設定到指定的位置
def SetPoint(TargetX,TargetY):
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
            #碰到零點感測器就表示已經回0了 (Y軸)
            if "axis zero point sensor trigger" in status_B:
                MotroCurrentPostion_B.value = 0
                
            #回到原點後，略過此次任務
            return "Pass this mission"

        #碰到零點感測器就表示已經回0了
        if "axis zero point sensor trigger" in status_A:
            MotroCurrentPostion_A.value = 0



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
            #碰到零點感測器就表示已經回0了 (Y軸)
            if "axis zero point sensor trigger" in status_B:
                MotroCurrentPostion_B.value = 0

            #回到原點後，略過此次任務
            return "Pass this mission"

        #碰到零點感測器就表示已經回0了
        if "axis zero point sensor trigger" in status_B:
            MotroCurrentPostion_B.value = 0
        
        db.session.commit()

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

#呼叫Jetson Nano拍照
def TakePic():
    response = requests.get("http://192.168.11.7:8000/Pic", timeout = 30)
    logger.info("Response : " + response.text)
    return response.text

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

#啟用定時運行命令
def StartSchedule_Job():
    #依照ID排序，將所有命令取出來
    scheduleLi = schedule.query.order_by(schedule.id.asc()).all()
    for ele in scheduleLi:
        logger.info("Start Schedule Job: (" +str(ele.PositionX) + "," +str(ele.PositionY) + ")")
        SetPoint(ele.PositionX,ele.PositionY)

#立即運行剛剛設定的指令
@app.route("/runCommandList")
def runCommandList():
    StartSchedule_Job()
    return "OK"

#立即運行剛剛設定的指令
@app.route("/updateMotorJob")
#更新步進馬達的移動任務
def updateMotorJob():
    #依照ID排序
    day_schedule = schedule_day_of_time.query.order_by(schedule_day_of_time.id.asc()).all()

    #清空所有任務
    scheduler.clear()

    Plan_li = []
    for ele in day_schedule:
        if ele != None:
            schedulePlan = {
                'id' : ele.id,
                'Time' : ele.time,
            }
            #到指定時間後，運行重複運行指令
            scheduler.every().day.at(ele.time).do(StartSchedule_Job)
    print (scheduler.jobs)
    return "OK"

#每秒鐘都去確認現在是否有任務可以運行
def pendingJob():
    while True:
        logger.info("run pending")
        scheduler.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    if sys.platform == "linux":
        try:
            RS485 = Read_RS485_Sensor_Lib.RS485()
        except:
            pass
    elif sys.platform == "win32":
        pass


    db.init_app(app)
    db.create_all()
    print (__name__ , "db.create_all")
    #啟動Server後，先鎖定煞車，後放鬆馬達出力
    Controll_2MD4850.InitMotor()


    scheduler.every(15).minutes.do(ReadLUX_Job)
    scheduler.every(16).minutes.do(ReadEC_Job)
    scheduler.every(17).minutes.do(ReadPH_Job)
    # 建立一個子執行緒，去監控任務運行狀態
    t = threading.Thread(target = pendingJob)

    # 執行該子執行緒
    t.start()

    # # 建立一個子執行緒，去定時更新運行排程
    # t2 = threading.Thread(target = updateMotorJob)

    # # 執行該子執行緒
    # t2.start()
    app.run(host='0.0.0.0',port=8001)


