'''INCOMPLETE
UNTESTED'''


from pickle import FALSE
from RPI_Operant.hardware.box import Box
import time
import random
from pathlib import Path
experiment_name = Path(__file__).stem
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':experiment_name}
# # For Running on the Raspberry Pi: 
USER_HARDWARE_CONFIG_PATH = '/home/pi/local_rpi_files/default_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/autotrain.yaml'

box = Box()

def run():
    
    box.setup(run_dict=RUNTIME_DICT, 
              user_hardware_config_file_path=USER_HARDWARE_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=False, simulated = False)
    
    if box.software_config['checks']['trigger_on_start']:
        
        trigger_object = box.outputs.miniscope_trigger.prepare_trigger()
    
    #simplifying hardware calls
    lever = box.levers.food
    dispenser = box.dispensers.dispenser
    speaker = box.speakers.speaker
    
    delay = box.get_delay()
    
    if box.software_config['checks']['trigger_on_start']:
        box.start_and_trigger([trigger_object])
    
    #get LED pulses to pass to other functions
    press_led_pulse = box.outputs.event_LED.prepare_pulse(length = 0.35, pulse_string = 'lever_press_food')
    retrieve_led_pulse = box.outputs.event_LED.prepare_pulse(length = 0.7, pulse_string = 'pellet_retrieved')
    new_round_pulse = box.outputs.round_LED.prepare_pulse(length = box.software_config['LED_pulses']['new_round'], pulse_string = 'new_round')
    
    for i in range(1,box.software_config['values']['rounds']+1, 1):
        box.timing.new_round()
        new_round_pulse()

        phase = box.timing.new_phase('lever_out', box.software_config['values']['lever_out'])
        speaker.play_tone(tone_name = 'round_start', wait = True)
        
        pause = box.timing.new_timeout(length = 0.5)
        pause.wait()
        
        press_latency = box.levers.food.extend()
        
        #start the actual lever-out phase
        lever.wait_for_n_presses(n = 1, latency_obj = press_latency, on_press_events = [press_led_pulse])
        while phase.active():
            '''waiting here for something to happen'''
        
            if lever.presses_reached:
                lever.retract()
                speaker.play_tone(tone_name = 'pellet_tone')
                
                timeout = box.timing.new_timeout(length = delay)
                timeout.wait()
                
                dispenser.dispense(on_retrieval_events = [retrieve_led_pulse])  
                phase.end_phase()
        
        #only dispense if not already dispensed
        if not lever.presses_reached:
            lever.retract()
            speaker.play_tone(tone_name = 'pellet_tone')
            
            timeout = box.timing.new_timeout(length = delay)
            timeout.wait()
            
            dispenser.dispense(on_retrieval_events = [retrieve_led_pulse]) 
        
        
        phase = box.timing.new_phase(name='ITI', length = box.software_config['values']['iti_length'])
        
        phase.wait()
    
    
    box.shutdown()

if __name__ == '__main__':
    run()
    







