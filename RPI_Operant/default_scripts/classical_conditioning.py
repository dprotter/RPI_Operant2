rom pickle import FALSE
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
    
    trigger_object = box.outputs.miniscope_trigger.prepare_serial_trigger()
    
    #simplifying hardware calls
    door_partner = box.doors.partner
    door_novel = box.doors.novel
    
    
    speaker = box.speakers.speaker
    
    delay = box.get_delay()
    
    
    subox.start_and_trigger([trigger_object])