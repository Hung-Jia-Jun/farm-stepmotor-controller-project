# -*- coding: utf-8 -*-
import numpy as np
import cv2

# cap = cv2.VideoCapture(
    #  'udpsrc port=5000 caps=application/x-rtp,media=(string)video,clock-rate=(int)90000,encoding-name=(string)H264,payload=(int)96!rtph264depay!decodebin!videoconvert!appsink', cv2.CAP_GSTREAMER)

# ip camera 的擷取路徑
# URL = 'rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov'
# 建立 VideoCapture 物件
ipcam = cv2.VideoCapture(
    'udpsrc port=5000 caps=application/x-rtp,media=(string)video,clock-rate=(int)90000,encoding-name=(string)H264,payload=(int)96!rtph264depay!decodebin!videoconvert!appsink', cv2.CAP_GSTREAMER)

# 使用無窮迴圈擷取影像，直到按下Esc鍵結束
while True:
    # 使用 read 方法取回影像
    stat, I = ipcam.read()

    # 加上一些影像處理...

    # imshow 和 waitkey 需搭配使用才能展示影像
    cv2.imshow('Image', I)
    if cv2.waitKey(1) == 27:
        ipcam.release()
        cv2.destroyAllWindows()
        break
