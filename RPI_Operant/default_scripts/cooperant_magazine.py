
from RPI_Operant.hardware.box import Box
import time
import random
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':'magazine'}
USER_CONFIG_PATH = None
USER_SOFTWARE_CONFIG_PATH = None

def run():
    
    box = Box(run_dict=RUNTIME_DICT, 
              user_config_file_path='/home/dprotter/Documents/Vole Projects/RPI_Operant2/RPI_Operant/default_setup_files/default_cooperant_hardware.yaml',
              user_software_config_file_path='/home/dprotter/Documents/Vole Projects/RPI_Operant2/RPI_Operant/default_setup_files/cooperant_magazine_s2.yaml',
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
        
        
        '''vvvvvvvvvvvvv simulation test stuff vvvvvvvvvvv'''
        r1 = random.random()
        if r1 < 0.75:
            sim_press = True
            press_time = random.random()(box.software_config['values']['round_length'])
            round_start_for_sim = time.time()
        else:
            sim_press = False
        
        r2 = random.random()
        if r2 < 0.90:
            sim_retrieve = True
        else:
            sim_retrieve = False
            
        
        
        box.timing.new_round(length = box.software_config['values']['round_length'])
        lever_phase = box.timing.new_phase(f'lever_out', length =4)
        press_timeout = box.timing.new_timeout(length = 2)
        
        press_latency = box.levers.door_1.extend()
        
        lever.wait_for_n_presses(n=1, latency_obj = press_latency)
        
        while press_timeout.active():
            
            if sim_press:
                if round_start_for_sim + press_time > time.time():
                    lever.simulate_press()
            
            if lever.presses_reached:
                
                lever.retract()
                lever_phase.finished()
                speaker.play_tone(tone = 'pellet_tone')
                dispenser.dispense()
                
        if not lever.presses_reached:
            speaker.play_tone(tone = 'pellet_tone')
            dispenser.dispense()
        
        if sim_retrieve:
            retrieve_time = 3 * random.random()
            retrieve_start = time.time()
        while lever_phase.active():
            ''''''
            if sim_retrieve:
                if retrieve_start + retrieve_time > time.time():
                    dispenser.simulate_retrieved()
                    sim_retrieve = False
        lever.retract()
        
        while not box.timing.round_finished():
            ''''''
            if sim_retrieve:
                if retrieve_start + retrieve_time > time.time():
                    dispenser.simulate_retrieved()
                    sim_retrieve = False
        

    
    
    
    box.shutdown()

if __name__ == '__main__':
    run()