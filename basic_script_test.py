from hardware.box import Box
import time

box = Box()
print('box complete')

for door in box.doors:
    
    print(f'\n{door}')
    door.close(wait = True)

time.sleep(1)
for door in box.doors:
    door.open()

time.sleep(4)
for door in box.doors:
    door.close()

while box.doors.door_1.is_open() or box.doors.door_2.is_open():
    print(f'door_1: {box.doors.door_1.is_open()} door_2:{box.doors.door_2.is_open()} ')
    time.sleep(0.05)

box.shutdown()