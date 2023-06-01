from RPI_Operant.hardware.box import Box
import time
import random
from pathlib import Path
experiment_name = Path(__file__).stem

RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':experiment_name}
# # For Running on the Raspberry Pi: 
USER_HARDWARE_CONFIG_PATH = '/home/pi/local_rpi_files/default_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/2023_grabda/setup_files/classical_cond_software.yaml'


box = Box()

def run():
    
    box.setup(run_dict=RUNTIME_DICT, 
              user_hardware_config_file_path=USER_HARDWARE_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=True, simulated = False)
    phase = box.timing.new_phase('setup_phase', length = 5)
    

    
    #simplifying hardware calls
    door_1 = box.doors.door_1
    door_2 = box.doors.door_2

    speaker = box.speakers.speaker1
    delay = box.get_delay()
    
    box.reset()
    #get LED pulses to pass to other functions
    new_round_pulse = box.outputs.round_LED.prepare_pulse(length = box.software_config['LED_pulses']['new_round'], pulse_string = 'new_round')
    
    round_order = box.software_config['values']['door_order']
    
    phase.end_phase()
    for door in round_order:
        
        box.timing.new_round()
        new_round_pulse()
        
        #play tone and wait delay
        tone = f'{door}_tone'
        speaker.play_tone(tone_name = tone, wait = True)
        box.timing.new_timeout(length = delay).wait()
        
        if door == 'door_1':
            reward_phase = box.timing.new_phase('reward_phase',length = box.software_config['values']['reward_length']['door_1'])
            door_1.open()
            reward_phase.wait()
            door_1.close()
        elif door == 'door_2':
            reward_phase = box.timing.new_phase('reward_phase',length = box.software_config['values']['reward_length']['door_2'])
            door_2.open()
            reward_phase.wait()
            door_2.close()
        else:
            reward_phase = box.timing.new_phase('reward_phase',length = box.software_config['values']['reward_length']['minus'])
    
    
    box.shutdown()

if __name__ == '__main__':
    run()
    







