from flask import Flask,request
from flask import render_template
import time
import sys
import schedule
import MySQLdb
import json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime



app = Flask(__name__)

db = SQLAlchemy(app)

class config(db.Model):
    config_key = db.Column(db.String(255), primary_key=True)
    config_value = db.Column(db.String(255))

    def __init__(self, content):
        self.content = content

    def __repr__(self):
        return '<config %r>' % self.content

class schedule(db.Model):
    DateTime = db.Column(db.String(255), primary_key=True)
    Action = db.Column(db.String(255))

    def __init__(self, DateTime, Action):
      self.DateTime = db.DateTime()
      self.Action = Action

    def __repr__(self):
        return '<schedule %r>' % self.content

db.init_app(app)
db.create_all()


@app.route("/index")
def index():
    return render_template('index.html')

#取得當前指令的列表
@app.route("/queryCommandList")
def queryCommandList():
    scheduleLi = schedule.query.all()
    Command_li = []
    for ele in scheduleLi:
        Command_li.append(ele.Action)
    return json.dumps(Command_li)


#新增工作指令
@app.route("/AddMotorCommand")
def AddMotorCommand():
    #方向 順時針轉為1,逆時鐘轉為0
    Direction = request.args.get('Direction')
    
    #座標位置
    Position = request.args.get('Position')

    #方向 順時針轉為1,逆時鐘轉為0
    Setting_type = request.args.get('Setting_type')
   
    #持續時間
    Duration = request.args.get('Duration')



    #如果是設定無刷直流馬達的距離時間關係
    if Setting_type == "BrushlessMotor":
        scheduleCommand = schedule(DateTime = str(datetime.now()) , Action='{\"Action\": \"Brushless motor\", \"Position\": \"'+str(Position)+'\",\"Direction\": \"'+str(Direction)+'\",\"Duration\": \"'+str(Duration)+'\"}')
    elif Setting_type == "StepMotor":
        scheduleCommand = schedule(DateTime = str(datetime.now()) , Action='{\"Action\": \"Step Motor\", \"Position\": \"'+str(Position)+'\",\"Direction\": \"'+str(Direction)+'\",\"Duration\": \"' + str(Duration)+'\"}')
        
    db.session.add(scheduleCommand)
    db.session.commit()
    return "OK"


#取得現在的馬達距離比例
@app.route("/queryDistanceOfTimeProportion")
def queryDistanceOfTimeProportion():
    StepMotor_config = config.query.filter_by(config_key ='StepMotor_DistanceOfTimeProportion').first()
    BrushlessMotor_config = config.query.filter_by(config_key ='BrushlessMotor_DistanceOfTimeProportion').first()
    #距離與馬達運轉時間比例
    proportionValue = '{\"BrushlessMotor_DistanceOfTimeProportion\": \"%s\",\"StepMotor_DistanceOfTimeProportion\": \"%s\"}' %(StepMotor_config.config_value,BrushlessMotor_config.config_value)
    return json.loads(proportionValue)

#距離與持續時間的比例尺
@app.route("/UpdateDistanceOfTimeProportion")
def UpdateDistanceOfTimeProportion():
    #方向 順時針轉為1,逆時鐘轉為0
    Setting_type = request.args.get('Setting_type')
    #公分 cm
    cm = request.args.get('cm')
    
    #持續時間
    duration = request.args.get('duration')
    
    #格式為 10cm:5s  全部為小寫
    value = cm + "cm:" + duration + "s"
    
    BrushlessMotor_config = config.query.filter_by(config_key ='BrushlessMotor_DistanceOfTimeProportion').first()
    StepMotor_config = config.query.filter_by(config_key ='StepMotor_DistanceOfTimeProportion').first()

    #如果是設定無刷直流馬達的距離時間關係
    if Setting_type == "BrushlessMotor":
        BrushlessMotor_config.config_value = value
    elif Setting_type == "StepMotor":
        StepMotor_config.config_value = value

    db.session.commit()
    return "OK"


if __name__ == "__main__":
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:HrK8Iww7hU0izq1H@192.168.11.4:3306/sensor_db'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:HrK8Iww7hU0izq1H@localhost:3306/sensordb'


    app.run(host='0.0.0.0',port=8000)

