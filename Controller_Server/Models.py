from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

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
