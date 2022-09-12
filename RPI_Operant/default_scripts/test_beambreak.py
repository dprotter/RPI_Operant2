
from RPI_Operant.hardware.box import Box
import time
import random
from pathlib import Path
import argparse
import os

experiment_name = Path(__file__).stem
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':experiment_name}
# # For Running on the Raspberry Pi: 
USER_HARDWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/laser_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/laser_software.yaml'


parser = argparse.ArgumentParser(description='input io info')
parser.add_argument('--config_hardware_in', '-i',type = str, 
                    help = 'where is the hardware yaml file stored?',
                    action = 'store',
                    default = None)
parser.add_argument('--config_software_in', '-s',type = str, 
                    help = 'where is the software yaml file stored?',
                    action = 'store',
                    default = None)


args = parser.parse_args()

if args.config_hardware_in:
    config_hardware_file = args.config_hardware_in
else: 
    config_hardware_file = USER_HARDWARE_CONFIG_PATH


if args.config_software_in: 
    config_software_file = args.config_software_in
else:
    config_software_file = USER_SOFTWARE_CONFIG_PATH
    

if not os.path.isfile(config_hardware_file):
    print(f'-config_hardware_file not a valid csvfile. double check that filepath! see ya.')
    exit()

if not os.path.isfile(config_software_file): 
    print('-config_software_file not a valid csvfile. double check that filepath! see ya.')
    exit()    




box = Box()
box.setup(run_dict=RUNTIME_DICT, 
            user_hardware_config_file_path=config_hardware_file,
            user_software_config_file_path=config_software_file,
            start_now=True)
phase = box.timing.new_phase('testing', length = 1000)
lat_objects = []
for door in box.doors:
    
    lat_objects += [door.open(wait = True)]

for i, beam in enumerate(box.beams):
    beam.monitor_beam_break(latency_to_first_beambreak = lat_objects[i], end_with_phase=phase)


time.sleep(0.5)
for beam in box.beams:
    beam.sim_break()
    time.sleep(0.3)

try:
    while phase.active():
        ''''''
        time.sleep(0.05)

except KeyboardInterrupt:
    print('\n\ncleaning up')
    phase.finished()
    for door in box.doors:
        door.close()
    
    box.shutdown()