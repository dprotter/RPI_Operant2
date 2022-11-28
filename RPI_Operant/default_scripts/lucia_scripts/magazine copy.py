
from RPI_Operant.hardware.box import Box
import time
import random
from pathlib import Path
experiment_name = Path(__file__).stem
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':experiment_name}
# # For Running on the Raspberry Pi: 
USER_HARDWARE_CONFIG_PATH = '/home/pi/local_rpi_files/default_hardware_fr2.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/magazine.yaml'


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
    
    if box.software_config['checks']['trigger_on_start']:
        box.start_and_trigger([trigger_object])
    
    #get LED pulses to pass to other functions
    press_led_pulse = box.outputs.event_LED.prepare_pulse(length = box.software_config['LED_pulses']['lever_press'], pulse_string = 'lever_press')
    new_round_pulse = box.outputs.round_LED.prepare_pulse(length = box.software_config['LED_pulses']['new_round'], pulse_string = 'new_round')
    retrieve_led_pulse = box.outputs.event_LED.prepare_pulse(length = box.software_config['LED_pulses']['pellet_retrieved'], pulse_string = 'pellet_retrieved')
    
    for i in range(1,box.software_config['values']['rounds']+1, 1):
        inp = input('press enter to dispense a pellet')
        dispenser.dispense()
    
    
    box.shutdown()

if __name__ == '__main__':
    run()
    
