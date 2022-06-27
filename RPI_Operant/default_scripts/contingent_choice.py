
from RPI_Operant.hardware.box import Box
import time
import random
import os
cwd = os.getcwd()
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':'contingent_choice', 'reward_lever':1}

USER_HARDWARE_CONFIG_PATH = os.path.join(cwd, 'RPI_Operant','default_setup_files','default_cooperant_hardware.yaml')
USER_SOFTWARE_CONFIG_PATH = os.path.join(cwd, 'RPI_Operant','default_setup_files','contingent_choice.yaml')

box = Box()
def run():
    
    box.setup(run_dict=RUNTIME_DICT, 
              user_hardware_config_file_path=USER_HARDWARE_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=True)
    time.sleep(0.5)
        
    if RUNTIME_DICT['side'] == 1:
        print('side = 1')
        lever_r = box.levers.lever_1
        lever_non_r = box.levers.lever_2
        speaker = box.speakers.speaker_1
        dispenser = box.port_dispensers.dispenser_1
    elif RUNTIME_DICT['side'] == 2:
        print('side = 2')
        lever_r = box.levers.lever_2
        lever_non_r = box.levers.lever_1
        speaker = box.speakers.speaker_2
        dispenser = box.port_dispensers.dispenser_2
    try:

        for i in range(1,box.software_config['values']['rounds']+1, 1):

            
            box.timing.new_round(length = box.software_config['values']['round_length'])
            lever_phase = box.timing.new_phase(f'lever_out', length = box.software_config['values']['lever_out_time'])
           
            
            press_latency_r = lever_r.extend()
            press_latency_non_r = lever_non_r.extend()
            lever_r.wait_for_n_presses(n=1, latency_obj = press_latency_r)
            lever_non_r.wait_for_n_presses(n=1, latency_obj = press_latency_non_r)
            
            while lever_phase.active():

                if lever_r.presses_reached:
                    
                    lever_r.retract()
                    lever_non_r.retract()
                    lever_phase.end_phase()
                    
                    #only play tone and reward if correct lever is pressed
                    speaker.play_tone(tone_name = 'pellet_tone')
                    dispenser.dispense()
                    
                if lever_non_r.presses_reached:
                    lever_r.retract()
                    lever_non_r.retract()
                    lever_phase.end_phase()
                    
            

            if not lever_r.presses_reached and not lever_non_r.presses_reached:
                lever_r.retract()
                lever_non_r.retract()
                
            phase = box.timing.new_phase(name ='ITI', length = box.timing.round_time_remaining())

            box.timing.wait_for_round_finish()
            
            phase.end_phase()

        box.shutdown()
    except KeyboardInterrupt:
        speaker.turn_off()
        dispenser.stop_servo()
        box.shutdown()

if __name__ == '__main__':
    run()