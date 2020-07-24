# -- coding: utf-8 --
import time
import cv2
import numpy as np
import sys
from ctypes import *
import logging
if sys.platform == "linux":
	import threading
	import os
	import termios
	sys.path.append("/opt/MVS/Samples/aarch64/Python/MvImport")    
	sys.path.append("/opt/MVS/lib ")   
	print (sys.path)
	from MvCameraControl_class import *
elif sys.platform == "win32":
	import copy
	import msvcrt
	sys.path.append("C:\\Users\\Jason\\Scripts\\MVS_Camera\\Python\\MvImport")
	from MvCameraControl_class import *

import time


class MVSControll:
	def __init__(self):
		self.deviceList = MV_CC_DEVICE_INFO_LIST()
		self.tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
		
		#Enum device
		self.ret = MvCamera.MV_CC_EnumDevices(self.tlayerType, self.deviceList)
		if self.ret != 0:
			print ("enum devices fail! ret[0x%x]" % self.ret)
			sys.exit()

		if self.deviceList.nDeviceNum == 0:
			print ("find no device!")
			sys.exit()

		print ("find %d devices!" % self.deviceList.nDeviceNum)

		for i in range(0, self.deviceList.nDeviceNum):
			mvcc_dev_info = cast(self.deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
			if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
				print ("\ngige device: [%d]" % i)
				strModeName = ""
				for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
					strModeName = strModeName + chr(per)
				print ("device model name: %s" % strModeName)

				nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
				nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
				nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
				nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
				print ("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
			elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
				print ("\nu3v device: [%d]" % i)
				strModeName = ""
				for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
					if per == 0:
						break
					strModeName = strModeName + chr(per)
				print ("device model name: %s" % strModeName)

				strSerialNumber = ""
				for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
					if per == 0:
						break
					strSerialNumber = strSerialNumber + chr(per)
				print ("user serial number: %s" % strSerialNumber)

		nConnectionNum = 0#input("please input the number of the device to connect:")

		if int(nConnectionNum) >= self.deviceList.nDeviceNum:
			print ("intput error!")
			sys.exit()

		#Creat Camera Object
		self.cam = MvCamera()

		#Select device and create handle
		self.stDeviceList = cast(self.deviceList.pDeviceInfo[int(nConnectionNum)], POINTER(MV_CC_DEVICE_INFO)).contents

		self.ret = self.cam.MV_CC_CreateHandle(self.stDeviceList)
		if self.ret != 0:
			print ("create handle fail! ret[0x%x]" % self.ret)
			sys.exit()

		#Open device
		self.ret = self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
		if self.ret != 0:
			print ("open device fail! ret[0x%x]" % self.ret)
			sys.exit()

		#Set trigger mode as off
		self.ret = self.cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
		if self.ret != 0:
			print ("set trigger mode fail! ret[0x%x]" % self.ret)
			sys.exit()

		#設定自動曝光為Continuous
		self.ret = self.cam.MV_CC_SetEnumValue("ExposureAuto",2)

		#設定曝光
		self.ret = self.cam.MV_CC_SetFloatValue("ExposureTime", 150000)
		
		self.ret = self.cam.MV_CC_SetEnumValue("GainAuto",2)

		self.ret = self.cam.MV_CC_SetEnumValue("GainAuto",2)

		self.ret = self.cam.MV_CC_SetEnumValue("GammaSelector",2)
		
		self.ret = self.cam.MV_CC_SetFloatValue("Gain", 20.03)
		
		self.ret = self.cam.MV_CC_SetBoolValue("GammaEnable",True)

		self.ret = self.cam.MV_CC_SetBoolValue("SharpnessEnable",True)

		self.ret = self.cam.MV_CC_SetBoolValue("HueEnable",True)

	

		# Get payload size
		stParam =  MVCC_INTVALUE()
		memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))
		
		self.ret = self.cam.MV_CC_GetIntValue("PayloadSize", stParam)
		if self.ret != 0:
			print ("get payload size fail! ret[0x%x]" % self.ret)
			sys.exit()
		self.nPayloadSize = stParam.nCurValue

	  

		
		
	def StartGrab(self,filename):
		# Cam properties
		fps = 30
		frame_width = 3072
		frame_height = 2048
		# Define the gstreamer sink
		gst_str_rtp = "appsrc ! videoconvert ! x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! rtph264pay ! udpsink host=0.0.0.0 port=5000"

		# Create videowriter as a SHM sink
		out = cv2.VideoWriter(gst_str_rtp, 0, fps, (frame_width, frame_height), True)
		while True:
			self.ret = self.cam.MV_CC_StartGrabbing()
			if self.ret != 0:
				print ("start grabbing fail! ret[0x%x]" % self.ret)
				sys.exit()
			self.stDeviceList = MV_FRAME_OUT_INFO_EX()
			memset(byref(self.stDeviceList), 0, sizeof(self.stDeviceList))
			self.data_buf = (c_ubyte * self.nPayloadSize)()

			#Start grab image
			start_time = time.time()
			self.ret = None
			while self.ret != 0:
				self.ret = self.cam.MV_CC_GetOneFrameTimeout(byref(self.data_buf), self.nPayloadSize, self.stDeviceList, 1000)

			if self.ret == 0:
				print ("get one frame: Width[%d], Height[%d], nFrameNum[%d]"  % (self.stDeviceList.nWidth, self.stDeviceList.nHeight, self.stDeviceList.nFrameNum))

				stConvertParam = MV_SAVE_IMAGE_PARAM_EX()
				stConvertParam.nWidth = self.stDeviceList.nWidth
				stConvertParam.nHeight = self.stDeviceList.nHeight
				stConvertParam.pData = self.data_buf
				stConvertParam.nDataLen = self.stDeviceList.nFrameLen
				stConvertParam.enPixelType = self.stDeviceList.enPixelType

				# MV_Image_Undefined  = 0, 
				#   MV_Image_Bmp        = 1, //BMP
				#   MV_Image_Jpeg       = 2, //JPEG
				#   MV_Image_Png        = 3, //PNG
				#   MV_Image_Tif        = 4, //TIF

				# jpg參數
				stConvertParam.nJpgQuality   = 99  # range[50-99]
				stConvertParam.enImageType = MV_Image_Jpeg
				bmpsize = self.nPayloadSize

				stConvertParam.nBufferSize = bmpsize
				bmp_buf = (c_ubyte * bmpsize)()
				stConvertParam.pImageBuffer = bmp_buf

				self.ret = self.cam.MV_CC_SaveImageEx2(stConvertParam)
				if self.ret != 0:
					print ("save file executed failed0:! ret[0x%x]" % self.ret)
					del self.data_buf
					sys.exit()
				end_time = time.time()
				print (start_time - end_time)
			

				try:
					img_buff = (c_ubyte * stConvertParam.nImageLen)()
					if sys.platform == "linux":
						memmove(byref(img_buff), stConvertParam.pImageBuffer, stConvertParam.nImageLen)
					elif sys.platform == "win32":
						cdll.msvcrt.memcpy(byref(img_buff), stConvertParam.pImageBuffer, stConvertParam.nImageLen)

					import pdb
					pdb.set_trace()
					temp = np.asarray(stConvertParam.pData) 
					temp.reshape((960, 1280, 3)) 
					# Write to SHM
					out.write(temp)

					print (img_buff)
				except:
					return "camera Error"


			else:
				print ("get one frame fail, ret[0x%x]" % self.ret)
	def StopCamera(self):
		#Stop grab image
		self.ret = self.cam.MV_CC_StopGrabbing()
		if self.ret != 0:
			print ("stop grabbing fail! ret[0x%x]" % self.ret)
			del self.data_buf
			sys.exit()

		#Close device
		self.ret = self.cam.MV_CC_CloseDevice()
		if self.ret != 0:
			print ("close deivce fail! ret[0x%x]" % self.ret)
			del self.data_buf
			sys.exit()

		#Destroy handle
		self.ret = self.cam.MV_CC_DestroyHandle()
		if self.ret != 0:
			print ("destroy handle fail! ret[0x%x]" % self.ret)
			del self.data_buf
			sys.exit()

		del self.data_buf
if __name__ == "__main__":
	FileName=time.strftime('%Y_%m_%d_%H-%M-%S',time.localtime(time.time()))+'.jpg'
	MVSControll = MVSControll()
	print(MVSControll.StartGrab(FileName))
	MVSControll.StopCamera()
