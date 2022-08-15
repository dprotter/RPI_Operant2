import sys
import os
  
# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.abspath(__file__))
# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)
# adding the parent directory to 
# the sys.path.
sys.path.append(parent)
print(parent)


from hardware.box import Box

import time
box=Box()
box.setup()

box.timing.new_round()

print('box complete')


def run():
    
    box.setup(simulated = True) # setting up a simulated box! 

    box.lasers.laser1.p1.trigger()

    box.shutdown() 

    return 
    
    '''time.sleep(0.5)
    for i in range(1,3, 1):
        box.timing.new_round()
        phase = box.timing.new_phase(f'test_{i}', length =30)
        press_latency = box.levers.door_1.extend()
        
        fut = box.levers.door_1.wait_for_n_presses(n=4, latency_obj = press_latency)
        while phase.active():
            if box.levers.door_1.presses_reached:
                print('wowee!')
                box.levers.door_1.retract()
                phase.finished()
                reward = box.timing.new_phase(name = 'social reward', length=2)
                box.doors.door_1.open()
                time.sleep(1)
                box.doors.door_1.simulate_open()
                
            else:
                val = random.random()
                time.sleep(1*val)
                box.levers.door_1.simulate_pressed()
                time.sleep(0.5*val)
                box.levers.door_1.simulate_unpressed()
                time.sleep(1*val)
        
        while reward.active():
            # wait 
            pass 
        
         #only setting wait = false here so that we can simulate the closing.
        box.doors.door_1.close(wait = False) 
        time.sleep(0.5)
        box.doors.door_1.simulate_closed()
        iti = box.timing.new_phase(name='ITI', length = 1)
        while iti.active():
            # wait
            pass 
    
    
    
    box.shutdown()'''

if __name__ == '__main__':
    run()