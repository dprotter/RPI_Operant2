
from RPI_Operant.hardware.box import Box
import time
import random
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':'magazine'}
USER_CONFIG_PATH = None
USER_SOFTWARE_CONFIG_PATH = None

def run():
    
    box = Box(run_dict=RUNTIME_DICT, 
              user_config_file_path=USER_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=True, simulated = True)
    
    time.sleep(0.5)
    
    if box.software_config['values']['location'] == 1:
        lever = box.levers.lever_1
        speaker = box.speakers.speaker_1
        dispenser = box.dispensers.port_dispenser_1
    elif box.software_config['values']['location'] == 2:
        lever = box.levers.lever_2
        speaker = box.speakers.speaker_2
        dispenser = box.dispensers.port_dispenser_2
        
    
    
    for i in range(1,box.software_config['values']['rounds']+1, 1):
        box.timing.new_round(length = box.software_config['values']['round_length'])
        lever_phase = box.timing.new_phase(f'lever_out', length =4)
        press_timeout = box.timing.new_timeout(length = 2)
        
        press_latency = box.levers.door_1.extend()
        
        lever.wait_for_n_presses(n=1, latency_obj = press_latency)
        
        while press_timeout.active():
            if lever.presses_reached:
                print('wowee! pressed.')
                lever.retract()
                lever_phase.finished()
                speaker.play_tone(tone = 'pellet_tone')
                dispenser.dispense()
                
        if not lever.presses_reached:
            speaker.play_tone(tone = 'pellet_tone')
            dispenser.dispense()
        
        while lever_phase.active():
            ''''''
            
        lever.retract()
        
        while not box.timing.round_finished():
            ''''''
        
        

    
    
    
    box.shutdown()

if __name__ == '__main__':
    run()