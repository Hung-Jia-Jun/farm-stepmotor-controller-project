# -*- coding: UTF-8 -*-
from flask import Flask
import multiprocessing
from flask import request
import ftplib
import os
from flask import render_template, Response
from os import listdir
import time
import configparser
import pdb
import os
import logging
import GrabImageToJpg
import GrabImageToStream
import GrabImageToJpg_Pyueye_OpenCV
import subprocess
# from multiprocessing import Process, Queue
from queue import Queue
import threading
from camera_opencv import Camera as camera_cv 

app = Flask(__name__)

class Camera:
	def __init__(self):

		# #重新啟動拍照服務
		# subprocess.Popen("systemctl restart ueyeethdrc", shell=True, stdout=subprocess.PIPE).stdout.read()
		# subprocess.Popen("systemctl restart ueyeusbdrc ", shell=True, stdout=subprocess.PIPE).stdout.read()
		
		#讀取USB現在插的是IDS相機還是MVS相機
		self.subprocess = subprocess.Popen("lsusb", shell=True, stdout=subprocess.PIPE).stdout.read()
		#依照USB現在的名稱，去自動選擇拍照的機器
		if "IDS" in str(self.subprocess):
			#拍照行為的消息隊列
			self.queue = Queue() 
			#回傳拍照結果的隊列
			self.ResponseQueue = Queue() 
			Pyueye = GrabImageToJpg_Pyueye_OpenCV.Pyueye()
			#啟動IDS相機拍照的背景程序，讓它自動對焦
			Thread_Pyueye = threading.Thread(target=Pyueye.OpenCamera,args=(self.queue,self.ResponseQueue,))
			Thread_Pyueye.start()
			# Process_Pyueye = Process(target=Pyueye.OpenCamera, args=(self.queue,self.ResponseQueue,))
			# Process_Pyueye.start()
	def SaveImage(self):
		logging.basicConfig(filename="/home/jetson/MVS/Samples/aarch64/Python/Running.log", filemode="w", format="%(asctime)s %(name)s:%(levelname)s:%(message)s", datefmt="%d-%M-%Y %H:%M:%S", level=logging.DEBUG)
		config = configparser.ConfigParser()
		config.read('/home/jetson/MVS/Samples/aarch64/Python/Config.ini')
		localPictureFolderPath = config.get('Setting','localPictureFolderPath')

		self.FileName=time.strftime('%Y_%m_%d_%H-%M-%S',time.localtime(time.time()))+'.jpg'

		#拍照結果
		result = ""
		#依照USB現在的名稱，去自動選擇拍照的機器
		if "IDS" in str(self.subprocess):
			GrabImageFilePath = localPictureFolderPath + self.FileName
			#存放拍照命令到消息隊列
			self.queue.put(GrabImageFilePath)     
			result = GrabImageToJpg_Pyueye_OpenCV.GetTakePicResponse(self.ResponseQueue)
		else:
			frame = camera_cv().get_frame()
			file_open = open(localPictureFolderPath + self.FileName, 'wb+')
			try:
				file_open.write(frame, )
				logging.info("Grab Sussful " + self.FileName)
				return self.FileName
			except Exception as e:
				logging.error("GrabFail")
				return "GrabFail"
			finally:
				file_open.close()

		if self.FileName in result:
			logging.info("Grab Sussful " + self.FileName)
			return self.FileName
		else:
			logging.error("GrabFail")
			return "GrabFail"
class FTP:
	def __init__(self):
		self.config = configparser.ConfigParser()
		self.config.read('/home/jetson/MVS/Samples/aarch64/Python/Config.ini')
		self.localPictureFolderPath = self.config.get('Setting','localPictureFolderPath')
		self.FTP = self.config.get('Setting','FTP')
		self.FTPUsername = self.config.get('Setting','FTPUsername')
		self.FTPPassword = self.config.get('Setting','FTPPassword')
		self.remoteFolderPath = self.config.get('Setting','remoteFolderPath')

	def FTPupload(self,file):
		logging.basicConfig(filename="/home/jetson/MVS/Samples/aarch64/Python/Running.log", filemode="w", format="%(asctime)s %(name)s:%(levelname)s:%(message)s", datefmt="%d-%M-%Y %H:%M:%S", level=logging.DEBUG)
		try:
			ftp = ftplib.FTP(self.FTP)
		except OSError:
			logging.error("FTP server disconnect")
			return "FTP server disconnect"
		ftp.login(self.FTPUsername, self.FTPPassword)
		file_list = listdir(self.localPictureFolderPath)
		logging.warning(str(file_list))
		if file in file_list:
			fileHandle = open(self.localPictureFolderPath + file, "rb")
		else:

			logging.warning(file +" Missing")
			return file +" Missing"

		
		retry = 0
		while file not in ftp.nlst(self.remoteFolderPath):
			print ("Try Upload ftp")
			logging.debug("Try Upload ftp")
			ext = os.path.splitext(file)[1]

			try:
				ftp.storbinary("STOR " + self.remoteFolderPath + file, fileHandle , 1024)
				print ("Finsh")
				logging.debug("Finsh")
				break
			except:
				retry = retry + 1
				if retry > 10:
					fileHandle.close()
					logging.critical(file +" uploaded fail")
					return file +" uploaded fail"

		ftp.quit() 
		fileHandle.close()
		logging.info("ftp close")
		try:
			JPG_filelist = [ f for f in os.listdir(self.localPictureFolderPath) if f.endswith(".jpg") ]
			for image in JPG_filelist:
				JPG_Date = image.split(".")[0]
				Img_Time = time.strptime(JPG_Date, '%Y_%m_%d_%H-%M-%S')
				now = time.localtime(time.time())

				#刪除大於三天的檔案
				if (time.mktime(now) - time.mktime(Img_Time))/ 60/ 60/ 24 > 3:
					try:
						os.remove(self.localPictureFolderPath + image)
					except Exception as e:
						logging.error(e)
			os.remove(self.localPictureFolderPath + file)
			logging.info("file removed")
		except Exception as e:
			logging.error("file remove error", exc_info=True)

		logging.info(file +" uploaded")
		return file +" uploaded"



@app.route("/Pic")
def Pic():
	global _Camera
	result = _Camera.SaveImage()
	logging.info("Grab Status: " + result)
	return result

@app.route("/upload")
def upload():
	filename = request.args.get('filename')
	ftp = FTP()
	result = ftp.FTPupload(filename)
	logging.info("Upload to FTP status: " + result)
	return result

_Camera = None
@app.before_first_request
def StartCamera():
	global _Camera
	_Camera = Camera()
	frame = camera_cv().get_frame()
	
@app.route('/stream')
def stream():
    """Video streaming home page."""
    return render_template('stream.html')


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(camera_cv()),mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
	app.debug = True
	app.run(host='0.0.0.0', port=8000)
