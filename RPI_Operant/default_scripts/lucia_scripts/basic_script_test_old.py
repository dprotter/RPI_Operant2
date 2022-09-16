from RPI_Operant.hardware.box_old import Box
import time
box = Box(start_now = True)
box.timing.new_round()

print('box complete')

'''for door in box.doors:
    door.close(wait = True)

time.sleep(1)
for door in box.doors:
    door.open()

time.sleep(4)
for door in box.doors:
    door.close(wait = True)

while box.doors.door_1.is_open() or box.doors.door_2.is_open():
    time.sleep(0.05)'''
box.reset()
box.levers.door_1.extend()
phase = box.timing.new_phase('test', length =10)
fut = box.levers.door_1.wait_for_n_presses()
while phase.active():
    if box.levers.door_1.presses_reached:
        print('woweee you did it!')
        phase.finished()
box.shutdown()


