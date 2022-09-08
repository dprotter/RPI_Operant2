
from RPI_Operant.hardware.box import Box
import time
import random
from pathlib import Path
experiment_name = Path(__file__).stem
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':experiment_name}
USER_CONFIG_PATH = None
USER_SOFTWARE_CONFIG_PATH = None

box = Box()

def run():
    
    box.setup(run_dict=RUNTIME_DICT, 
              user_config_file_path=USER_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=True, simulated = True)
    
    time.sleep(0.5)
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
            '''wait'''
        
         #only setting wait = false here so that we can simulate the closing.
        box.doors.door_1.close(wait = False) 
        time.sleep(0.5)
        box.doors.door_1.simulate_closed()
        iti = box.timing.new_phase(name='ITI', length = 1)
        while iti.active():
            '''wait'''
    
    
    
    box.shutdown()

if __name__ == '__main__':
    run()