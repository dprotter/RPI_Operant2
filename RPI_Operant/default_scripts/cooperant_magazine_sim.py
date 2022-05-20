
from RPI_Operant.hardware.box import Box
import time
import random
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':'cooperant_magazine', 'side':1}
USER_HARDWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/default_cooperant_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/cooperant_magazine.yaml'


box = Box()
    

def run():
    box.setup(run_dict=RUNTIME_DICT, 
              user_hardware_config_file_path=USER_HARDWARE_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=True, simulated = True)
    
    
    time.sleep(0.5)
    
    if RUNTIME_DICT['side'] == 1:
        lever = box.levers.lever_1
        speaker = box.speakers.speaker_1
        dispenser = box.port_dispensers.dispenser_1
    elif RUNTIME_DICT['side'] == 2:
        lever = box.levers.lever_2
        speaker = box.speakers.speaker_2
        dispenser = box.port_dispensers.dispenser_2
        
    
    
    for i in range(1,box.software_config['values']['rounds']+1, 1):
        
        
        '''vvvvvvvvvvvvv simulation test stuff vvvvvvvvvvv'''
        r1 = random.random()
        if r1 < 0.8:
            sim_press = True
            press_time = random.random()*(2)
            round_start_for_sim = time.time()
            
            
        else:
            sim_press = False
        
        r2 = random.random()
        if r2 < 0.90:
            sim_retrieve = True
        else:
            sim_retrieve = False
            
        
        box.timing.new_round(length = box.software_config['values']['round_length'])
        lever_phase = box.timing.new_phase(f'lever_out', length = box.software_config['values']['lever_out_time'])
        press_timeout = box.timing.new_timeout(length = box.software_config['values']['lever_out_to_dispense_time'])
        
        press_latency = lever.extend()
        lever.wait_for_n_presses(n=1, latency_obj = press_latency)
        
        while press_timeout.active() and lever_phase.active():
            
            if sim_press:
                if round_start_for_sim + press_time < time.time():
                    lever.simulate_lever_press()
                    time.sleep(0.05)
                    
                    
            
            if lever.presses_reached:
                
                lever.retract()
                lever_phase.end_phase()
                speaker.play_tone(tone_name = 'pellet_tone')
                dispenser.dispense()
                
                
        if not lever.presses_reached:
            speaker.play_tone(tone_name = 'pellet_tone')
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
        
        phase = box.timing.new_phase(name ='ITI', length = 1000)
        if not lever.presses_reached:
            lever.retract()
        
        while not box.timing.round_over():
            ''''''
            if sim_retrieve:
                if retrieve_start + retrieve_time < time.time():
                    dispenser.simulate_retrieved()
                    sim_retrieve = False
        
        phase.end_phase()
                    

    
    box.shutdown()

if __name__ == '__main__':
    run()