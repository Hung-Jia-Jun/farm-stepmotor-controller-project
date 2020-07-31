export LD_LIBRARY_PATH=/opt/MVS/lib/aarch64:$LD_LIBRARY_PATH
bash set_usb_priority.sh
bash set_usbfs_memory_size.sh
python3 app.py
