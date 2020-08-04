import os
import cv2
from base_camera import BaseCamera
import numpy as np


class Camera(BaseCamera):
	video_source = 0

	def __init__(self):
		if os.environ.get('OPENCV_CAMERA_SOURCE'):
			Camera.set_video_source(int(os.environ['OPENCV_CAMERA_SOURCE']))
		super(Camera, self).__init__()

	@staticmethod
	def set_video_source(source):
		Camera.video_source = source

	@staticmethod
	def frames():
		from GrabImageToStream import MVSControll
		# camera = cv2.VideoCapture(Camera.video_source)
		# camera = cv2.VideoCapture(0)
		MVSControll = MVSControll()
		while True:
			img_buff = MVSControll.StartStream()
			img_data = next(img_buff)
			img_data = np.fromstring(img_data, np.uint8)
			img_data = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
			yield cv2.imencode('.jpg', img_data)[1].tobytes()

		# MVSControll.StopCamera()

if __name__ == "__main__":
	from GrabImageToStream import MVSControll
	MVSControll = MVSControll()
	while True:
		img_buff = MVSControll.StartStream()
		img_data = next(img_buff)
		img_data = np.fromstring(img_data, np.uint8)
		img_data = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
		print ( cv2.imencode('.jpg', img_data)[1].tobytes() )