
from RPI_Operant.hardware.box import Box
import time
import random
from pathlib import Path
experiment_name = Path(__file__).stem
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':experiment_name}

# # For Running on the Raspberry Pi: 
USER_HARDWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/laser_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/laser_software.yaml'

# # For Running Locally: 
# USER_HARDWARE_CONFIG_PATH = '/Users/sarahlitz/Desktop/Projects/Donaldson Lab/RPI_Operant2/RPI_Operant/default_setup_files/default_hardware.yaml'
# USER_SOFTWARE_CONFIG_PATH = '/Users/sarahlitz/Desktop/Projects/Donaldson Lab/RPI_Operant2/RPI_Operant/default_setup_files/default_software.yaml'

box = Box()
def run():
    
    #
    # Call to Setup Box with Hardware/Software yaml files specified! 
    #
    box.setup(run_dict=RUNTIME_DICT, 
              user_hardware_config_file_path=USER_HARDWARE_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=True, 
              simulated=False)
    time.sleep(0.5)
    
        
    try:
        
        for i in range(box.software_config['values']['rounds']):
            
            print(f'ROUND {i+1}')
            box.timing.new_round(length = box.software_config['values']['round_length'])

            phase = box.timing.new_phase(f'lever_out', length = box.software_config['values']['lever_out_time'])
            # # Notes on Laser Script Syntax # # 
            # to iterate thru every laser pattern, loop thru any laser object's pattern list ( e.g. for pattern in box.lasers.laser1.patterns )
            # to add logic for when we should trigger playing a certain pattern, we can use the phase functionality ( like while phase.active, check for a certain condition that if met will cause us to exit from the phase early and enter a new phase)
            
            lever_presses_met = False
            while phase.active(): 
                # Wait for an event here!! Add an if statement!! 
                #   use this for logic if we are waiting for some event to trigger the phase exit 
                #   e.g. if n number of lever presses is met, we open door and trigger a certain pattern on a laser! 
                lever_presses_met = True 
                if lever_presses_met: 
                    phase.end_phase() # Early exit 

            
            if lever_presses_met: # if True, we know that we encountered an event that caused us to exit the previous phase early. ( probs recieving enough lever presses ! )  
                phase = box.timing.new_phase(f'{box.lasers.laser1.interval_5_sec.name}', length = box.lasers.laser1.interval_5_sec.total_time) # iterate thru phases 
    
                box.lasers.laser1.interval_5_sec.trigger() # turns on laser 1, pattern i

                phase.wait()
                
                phase.end_phase()

            else: 

                print('lever presses was not met')
                # did not recieve enough lever presses. 
                # Any logic for how we want to react to this case goes here. 
                pass    
            
            
            time.sleep(1)
            
        
        box.timing.wait_for_round_finish()
        box.shutdown()

    except KeyboardInterrupt:
        print('keyboard interrupt, shutting down')
        speaker1.turn_off()
        positional_dispenser_1.stop_servo()
        lever_door_1.retract()
        lever_door_2.retract()
        laser1.turn_off()
        box.force_shutdown()

if __name__ == '__main__':
    run()