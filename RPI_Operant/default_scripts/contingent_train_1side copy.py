
from RPI_Operant.hardware.box import Box
import time
import random
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':'contingent_train_1side', 'side':1}
USER_HARDWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/default_cooperant_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/cooperant_autotrain_1side.yaml'

box = Box()
def run():
    
    box.setup(run_dict=RUNTIME_DICT, 
              user_hardware_config_file_path=USER_HARDWARE_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=True)
    time.sleep(0.5)
        
    if RUNTIME_DICT['side'] == 1:
        print('side = 1')
        lever = box.levers.lever_1
        speaker = box.speakers.speaker_1
        dispenser = box.port_dispensers.dispenser_1
    elif RUNTIME_DICT['side'] == 2:
        print('side = 2')
        lever = box.levers.lever_2
        speaker = box.speakers.speaker_2
        dispenser = box.port_dispensers.dispenser_2
    try:

        for i in range(1,box.software_config['values']['rounds']+1, 1):

            
            box.timing.new_round(length = box.software_config['values']['round_length'])
            lever_phase = box.timing.new_phase(f'lever_out', length = box.software_config['values']['lever_out_time'])
           
            
            press_latency = lever.extend()
            lever.wait_for_n_presses(n=1, latency_obj = press_latency)
            
            while lever_phase.active():

                if lever.presses_reached:
                    
                    lever.retract()
                    lever_phase.end_phase()
                    speaker.play_tone(tone_name = 'pellet_tone')
                    dispenser.dispense()
                    
            

            if not lever.presses_reached:
                lever.retract()
                
            phase = box.timing.new_phase(name ='ITI', length = 1000)

            box.timing.wait_for_round_finish()
            
            phase.end_phase()
                        

        box.shutdown()
    except KeyboardInterrupt:
        speaker.turn_off()
        dispenser.stop_servo()
        box.shutdown()

if __name__ == '__main__':
    run()