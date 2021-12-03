from hardware.box import Box
import time

box = Box()
print('box complete')
box.doors.door_1.close()
box.doors.door_1.open()
time.sleep(3)
box.doors.door_1.close()
box.shutdown()