
from RPI_Operant.hardware.box import Box
import time
import random
from pathlib import Path
experiment_name = Path(__file__).stem
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':experiment_name, 'levers.door_1_active':1, 'levers.door_2_active':1, 'reward_focal_lever_1':1, 'reward_focal_lever_2':1}
# USER_HARDWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/default_cooperant_hardware.yaml'
# USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/contingent_2_lever_test.yaml'
USER_HARDWARE_CONFIG_PATH = '/Users/sarahlitz/Desktop/Projects/Donaldson Lab/RPI_Operant2/RPI_Operant/default_setup_files/default_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/Users/sarahlitz/Desktop/Projects/Donaldson Lab/RPI_Operant2/RPI_Operant/default_setup_files/default_software.yaml'

box = Box()
def run():
    
    #
    # Call to Setup Box with Hardware/Software yaml files specified! 
    #
    box.setup(run_dict=RUNTIME_DICT, 
              user_hardware_config_file_path=USER_HARDWARE_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=True, 
              simulated=True)
    time.sleep(0.5)
    
        
    if RUNTIME_DICT['levers.door_1_active'] == 1:
        print('levers.door_1 is active')
    lever_door_1 = box.levers.door_1
    speaker1 = box.speakers.speaker1
    positional_dispenser_1 = box.positional_dispensers.positional_dispenser_1
    if RUNTIME_DICT['levers.door_2_active'] == 1:
        print('levers.door_2 is active')
    lever_door_2 = box.levers.door_2
    
    if RUNTIME_DICT['levers.door_1_active'] == 0 and RUNTIME_DICT['levers.door_2_active'] == 0:
        print('\n\nvvvvvvvv\nwarning!!!! no active levers have been specified!\n^^^^^^^^^\n\n')
    
    try:
        
        for i in range(box.software_config['values']['rounds']):
            

            box.timing.new_round(length = box.software_config['values']['round_length'])

            print('New Phase, new Pattern')
            laser1_pattern = box.lasers.laser1.patterns[i]
            laser2_pattern = box.lasers.laser2.patterns[i]
            phase = box.timing.new_phase(f'{box.lasers.laser1.name}, {laser1_pattern.name}', length = laser1_pattern.total_time) # iterate thru phases 
            phase2 = box.timing.new_phase(f'{box.lasers.laser2.name}, {laser2_pattern.name}', length = laser2_pattern.total_time) 
            

            # iterate both phase and laser pattern 

            while phase.active(): 
    
                laser1_pattern.trigger() # turns on laser 1, pattern i
                laser2_pattern.trigger()
                
                phase.end_phase()
                phase2.end_phase()
            
            time.sleep(1)
            
        
        box.timing.wait_for_round_finish()
        box.shutdown()

    except KeyboardInterrupt:
        speaker1.turn_off()
        positional_dispenser_1.stop_servo()
        lever_door_1.retract()
        lever_door_2.retract()
        box.force_shutdown()

if __name__ == '__main__':
    run()