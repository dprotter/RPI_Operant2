
import sys
print(sys.path)
from RPI_Operant.hardware import fake_box as Box
import time

def run():
    box = Box()
    box.timing.start_timing()

    box.levers.door_1.extend()
    phase = box.timing.new_phase('test', length =10)
    fut = box.levers.door_1.wait_for_n_presses(n=5)
    while phase.active():
        if box.levers.door_1.presses_reached:
            print('wowee!')
            phase.finished()
        else:
            time.sleep(0.25)
            box.levers.door_1.simulate_pressed()
            box.levers.door_1.simulate_unpressed()
    box.shutdown()

if __name__ == '__main__':
    run()