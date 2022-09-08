
from RPI_Operant.hardware.box import Box
import time
import random
from pathlib import Path
experiment_name = Path(__file__).stem
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':experiment_name}

# # For Running on the Raspberry Pi: 
USER_HARDWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/laser_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/laser_software.yaml'


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

            # # Phase 1: Extending Levers # # 
            phase = box.timing.new_phase(f'lever_out', length = box.software_config['values']['lever_out_time'])
            
            # lever 1 
            press_latency_1 = box.levers.door_1.extend()
            box.levers.door_1.wait_for_n_presses(n = 1, latency_obj = press_latency_1)

            # lever 2 
            press_latency_2 = box.levers.door_2.extend()
            box.levers.door_2.wait_for_n_presses(n = 1, latency_obj = press_latency_2)

            lever_press_met = False 
            while phase.active(): 
                
                if box.levers.door_1.presses_reached: # lever 1 goal met

                    # retract lever 1 
                    lever_press_met = True 
                    box.levers.door_1.retract()
                    phase.end_phase() # Early exit from the Lever Out phase
                

                elif box.levers.door_2.presses_reached: # lever 2 goal met 
                
                    # retract lever 2 
                    lever_press_met = True 
                    box.levers.door_2.retract()
                    phase.end_phase() # Early exit from the Lever Out phase


            # Lever Phase Ended! If either lever is still extended, retract now. 
            if box.levers.door_1.is_extended: 
                box.levers.door_1.retract()
            if box.levers.door_2.is_extended: 
                box.levers.door_2.retract()
            
            if lever_press_met: # if True, we know that we encountered an event that caused us to exit the previous phase early. ( probs recieving enough lever presses ! )  
                phase = box.timing.new_phase(f'{box.lasers.laser1.interval_5_sec.name}', length = box.lasers.laser1.interval_5_sec.total_time) 
    
                print('a lever met its required # of presses, playing the 5 second interval laser')
                box.lasers.laser1.interval_5_sec.trigger() 

                phase.wait()
                
                phase.end_phase()

            else: 
                
                phase = box.timing.new_phase(f'{box.lasers.laser1.interval_1_sec.name}', length = box.lasers.laser1.interval_1_sec.total_time)
                
                print('lever presses was not met, playing the 1 second interval laser pattern')

                box.lasers.laser1.interval_1_sec.trigger()

                phase.wait()
                phase.end_phase()
                

            time.sleep(1)
            
        
        box.timing.wait_for_round_finish()
        box.shutdown()
 
    except KeyboardInterrupt:
        print('keyboard interrupt, shutting down')
        speaker1.turn_off()
        positional_dispenser_1.stop_servo()
        lever_door_1.retract()
        box.levers.door_1.retract()
        lever_door_2.retract()
        laser1.turn_off()
        box.force_shutdown()

if __name__ == '__main__':
    run()