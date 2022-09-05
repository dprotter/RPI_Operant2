
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
            phase = box.timing.new_phase(f'{box.lasers.laser1.name}, {laser1_pattern.name}', length = laser1_pattern.total_time) # iterate thru phases 

            

            # iterate both phase and laser pattern 

            while phase.active(): 
    
                laser1_pattern.trigger() # turns on laser 1, pattern i
                
                phase.end_phase()
            
        if box.doors.door_1.is_open(): 
            
            time.sleep(3)

            box.lasers.laser1.turn_on() 

            return 
            #### #### #### #### 
            #### #### #### #### 
            #### #### #### #### 

            lever_phase = box.timing.new_phase(f'lever_out', length = box.software_config['values']['lever_out_time'])
           
            
            press_latency_1 = lever_door_1.extend()
            lever_door_1.wait_for_n_presses(n=1, latency_obj = press_latency_1)
            
            press_latency_2 = lever_door_2.extend()
            lever_door_2.wait_for_n_presses(n=1, latency_obj = press_latency_2)
            

            while lever_phase.active():
                
                if lever_door_1.presses_reached:
                    
                    lever_door_1.retract()
                    lever_door_2.retract()
                    lever_phase.end_phase()
                    if RUNTIME_DICT['levers.door_1_active'] == 1:
                        pellets_dispenser_2_remaining -=1

                
                elif lever_2.presses_reached:
                    lever_1.retract()
                    lever_2.retract()
                    lever_phase.end_phase()
                    if RUNTIME_DICT['lever_2_active'] == 1:
                        speaker_1.play_tone(tone_name = 'pellet_tone')
                        dispenser_1.dispense()
                        pellets_dispenser_1_remaining -= 1
                        if RUNTIME_DICT['reward_focal_lever_2']:
                            timeout = box.timing.new_timeout(box.software_config['values']['focal_reward_lever_2_delay'])
                            timeout.wait()
                            dispenser_3.dispense()
                            pellets_dispenser_3_remaining -= 1

            if not lever_1.presses_reached and not lever_2.presses_reached:
                lever_1.retract()
                lever_2.retract()
            
            if pellets_dispenser_1_remaining == 0 or pellets_dispenser_2_remaining == 0 or pellets_dispenser_3_remaining == 0:
                phase = box.timing.new_phase(name ='refill_pellets', length = 1000)
                print('\n\nvvvvvv\none of the pellet dispensers may be empty. refill, and then press enter.\n^^^^^^^^^\n\n')
                input()
                pellets_dispenser_1_remaining = dispenser_1.config_dict['max_pellets']
                pellets_dispenser_2_remaining = dispenser_2.config_dict['max_pellets']
                phase.end_phase()
            else:
                print(f'pellets remaining| disp1: {pellets_dispenser_1_remaining} disp2:{pellets_dispenser_2_remaining}')
            phase = box.timing.new_phase(name ='ITI', length = box.timing.round_time_remaining())
            box.timing.wait_for_round_finish()
            phase.end_phase()
                   

        box.shutdown()

    except KeyboardInterrupt:
        speaker1.turn_off()
        positional_dispenser_1.stop_servo()
        lever_door_1.retract()
        lever_door_2.retract()
        box.force_shutdown()

if __name__ == '__main__':
    run()