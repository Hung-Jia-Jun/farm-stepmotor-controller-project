from flask import Flask
from sqlalchemy import Column, Integer, String, ForeignKey, Date
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)

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

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:HrK8Iww7hU0izq1H@192.168.11.4:3306/sensordb'
db.init_app(app)
db.create_all()

