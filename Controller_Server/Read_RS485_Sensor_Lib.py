# -*- coding:utf-8 -*-
import serial
import time
import pdb
class RS485:
	def __init__(self):
		# self.ser = serial.Serial("COM7",baudrate = 9600,bytesize = serial.EIGHTBITS,timeout=1,parity = "N",stopbits = 1) #receive data once every 0.01S 
		self.ser = serial.Serial("/dev/ttyS0",baudrate = 9600,bytesize = serial.EIGHTBITS,timeout=1,parity = "N",stopbits = 1) #receive data once every 0.01S 
	def serialRef(self):
		# self.ser.flushInput()
		return self.ser
		# self.ser.flush()
	def ReadLUX(self):
		command = bytearray([0x6E,0x03,0x00,0x00,0x00,0x05,0x8C,0x96])
		
		self.ser.write(command)
		index = 0
		line = []
		while self.ser.inWaiting() > 0:
			for c in self.ser.read(2):
				line.append(hex(c))
				index += 1
				if index == 15:
					index = 0
					#溫度
					temperature = int(''.join(line[3:5]).replace("0x",""),16)/100

					#濕度
					humidity = int(''.join(line[5:7]).replace("0x",""),16)/100

					#光照度
					lux = int(''.join(line[7:9]).replace("0x",""),16)* 10

					#二氧化碳 ppm
					C02 = int(''.join(line[9:11]).replace("0x",""),16)/100
					#大氣壓力
					AtmosphericPressure = int(''.join(line[11:13]).replace("0x",""),16)/100

					line = []

					print ("大氣溫度 : " + str(temperature))
					print ("濕度 : " + str(humidity))
					print ("光照 : " + str(lux))
					print ("二氧化碳 : " + str(C02))
					print ("大氣壓力 : " + str(AtmosphericPressure))
					#返回所有資料
					return str(temperature), str(humidity), str(lux), str(C02), str(AtmosphericPressure) 

	def Clear(self):
		while self.ser.inWaiting() > 0:
			self.ser.flushInput()
			self.ser.flushOutput()
		return "OK"
	def ReadEC(self):
		command = bytearray([0x06,0x03,0x00,0x00,0x00,0x0B,0x05,0xBA])
		
		
		self.ser.write(command)

		index = 0
		line = []
		while self.ser.inWaiting() > 0:
			for c in self.ser.read(2):
				index += 1
				if len(hex(c))==3:
					# 因為 如果是0x6 的話，要做相加會錯誤，所以要補0 0x06
					line.append(hex(c)[0:2] + "0" + hex(c)[-1])
				else:
					line.append(hex(c))
				if index == 27:
					index = 0
					#溫度
					temperature = int(''.join(line[13:15]).replace("0x",""),16)/10

					#電導率
					EC = int(''.join(line[-6:-2]).replace("0x",""),16)/100


					print ("水溫 : " + str(temperature))
					print ("電導率 : " + str(EC))
					return str(temperature) , str(EC)

	def ReadPH(self):
		command = bytearray([0x07,0x03,0x00,0x03,0x00,0x01,0x74,0x6C])
		
		self.ser.write(command)

		index = 0
		line = []
		while self.ser.inWaiting() > 0:
			for c in self.ser.read(2):
				index += 1
				if len(hex(c))==3:
					# 因為 如果是0x6 的話，要做相加會錯誤，所以要補0 0x06
					line.append(hex(c)[0:2] + "0" + hex(c)[-1])
				else:
					line.append(hex(c))
				if index == 7:
					index = 0
					#溫度
					PH = int(''.join(line[-4:-2]).replace("0x",""),16)/100

					print ("PH : " + str(PH))
					return str(PH)
	def ReadAllSensor(self):
		AtomTemperature = 0
		humidity = 0
		lux = 0
		C02 = 0
		AtmosphericPressure = 0
		temperature = 0
		EC = 0
		PH = 0
		try:
			AtomTemperature, humidity, lux, C02, AtmosphericPressure  = self.ReadLUX()
		except:
			pass
		try:
			temperature , EC = self.ReadEC()
		except:
			pass
		try:
			PH = self.ReadPH()
		except:
			pass
		return AtomTemperature , humidity , lux , C02 , AtmosphericPressure , temperature , EC , PH 


if __name__ == "__main__":
	RS485 = RS485()
	while True:
		time.sleep(1)
		# RS485.ReadLUX()
		RS485.ReadEC()
		# RS485.ReadPH()
		# RS485.Flush()
		#RS485.ReadAllSensor()