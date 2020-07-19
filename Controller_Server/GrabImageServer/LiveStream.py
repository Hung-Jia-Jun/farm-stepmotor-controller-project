import time
import datetime
import cv2

# Cam properties
fps = 30.

# Create capture
cap = cv2.VideoCapture(0)



frame_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
frame_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

# Set camera properties
cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

cap.set(cv2.CAP_PROP_FPS, int(fps))

# Define the gstreamer sink
gst_str_rtp = "appsrc ! videoconvert ! x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! rtph264pay ! udpsink host=127.0.0.1 port=5000"


# Check if cap is open
if cap.isOpened() is not True:
    print ("Cannot open camera. Exiting.")
    quit()

# Create videowriter as a SHM sink
out = cv2.VideoWriter(gst_str_rtp, 0, int(fps), (int(frame_width), int(frame_height)), True)

# Loop it
while True:
    # Get the frame
    ret, frame = cap.read()
    # Check
    if ret is True:
        # Write to SHM
        print(datetime.datetime.now(),"write")
        out.write(frame)
    else:
        print ("Camera error.")
        time.sleep(10)

cap.release()
