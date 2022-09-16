
from RPI_Operant.hardware.box import Box
import time
import random
from pathlib import Path
experiment_name = Path(__file__).stem
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':experiment_name}
USER_CONFIG_PATH = None
USER_SOFTWARE_CONFIG_PATH = None

box = Box()

def run():
    
    box.setup(run_dict=RUNTIME_DICT, 
              user_config_file_path=USER_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=False, simulated = True)
    
    #this could be
    trigger_object = box.outputs.miniscope_trigger.prepare_trigger()
    
    #simplifying hardware calls
    lever = box.levers.food
    dispenser = box.dispensers.food
    speaker = box.speakers.speaker
    #
    box.start_and_trigger([trigger_object])
    
    #get LED pulses to pass to other functions
    press_led_pulse = box.outputs.event_LED.prepare_pulse(length = 0.35, pulse_string = 'lever_press_food')
    retrieve_led_pulse = box.outputs.event_LED.prepare_pulse(length = 0.7, pulse_string = 'pellet_retrieved')
 
    for i in range(1,box.software_config['values']['rounds']+1, 1):
        box.timing.new_round(length = box.software_config['values']['round_length'])
        
        phase = box.timing.new_phase('lever_out', box.software_config['values']['lever_out'])
        press_latency = box.levers.food.extend()
        
        #start the actual lever-out phase
        lever.wait_for_n_presses(n=4, latency_obj = press_latency, on_press_events = [press_led_pulse])
        while phase.active():
            '''waiting here for something to happen'''
        
            if lever.presses_reached:
                lever.retract()
                speaker.play_tone(tone_name = 'pellet_tone')
                dispenser.dispense(on_retrieval_events = [retrieve_led_pulse])
        
        
        
        
        
        phase = box.timing.new_phase(name='ITI', length = box.timing.round_time_remaining())
        
        box.timing.wait_for_round_finish()
        phase.end_phase()
    
    
    box.shutdown()

if __name__ == '__main__':
    run()