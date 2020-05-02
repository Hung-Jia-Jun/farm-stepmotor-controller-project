from flask import Flask,request
from flask import render_template
import time
import sys
import schedule
import MySQLdb
import json
from flask_cors import CORS
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
    
    #毫秒為單位
    TimeMinSec = request.args.get('TimeMinSec')
    if sys.platform == "linux":
        status = Controll_2MD4850.RunStepping_MotorByInputSetNumber(TimeMinSec,direction)
        return str(status)
    elif sys.platform == "win32":
        return "在windows環境無法顯示此數值"

@app.route("/ReadLUX")
def ReadLUX():
    if sys.platform == "linux":
        while True:
            try:
                time.sleep(1)
                AtomTemperature , humidity , lux , C02 , AtmosphericPressure = RS485.ReadLUX()
                RS485.Clear()
                data = {
                    "大氣溫度" : str(AtomTemperature),
                    "濕度" : str(humidity),
                    "光照" : str(lux),
                    "二氧化碳" : str(C02),
                    "大氣壓力" : str(AtmosphericPressure),
                }
                return data
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

@app.route("/ReadEC")
def ReadEC():
    if sys.platform == "linux":
        while True:
            try:
                time.sleep(1)
                temperature , EC = RS485.ReadEC()
                RS485.Clear()
                data = {
                    "水溫" : str(temperature),
                    "電導率" : str(EC),
                }
                return data
            except Exception as e:
                print (e)
    elif sys.platform == "win32":
        data = {
                "水溫" : "在windows環境無法顯示此數值",
                "電導率" :  "在windows環境無法顯示此數值",
            }
        return data

@app.route("/ReadPH")
def ReadPH():
    if sys.platform == "linux":
        while True:
            try:
                time.sleep(1)
                PH = RS485.ReadPH()
                if PH != None:
                    RS485.Clear()
                    data = {
                        "PH" : str(PH)
                    }
                    return data
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

if __name__ == "__main__":
    if sys.platform == "linux":
        RS485 = Read_RS485_Sensor_Lib.RS485()
    elif sys.platform == "win32":
        pass
    
    app.run(host='0.0.0.0',port=8001)

