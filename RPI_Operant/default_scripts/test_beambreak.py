
from RPI_Operant.hardware.box import Box
import time
import random
from pathlib import Path
experiment_name = Path(__file__).stem
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':experiment_name}
# # For Running on the Raspberry Pi: 
USER_HARDWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/laser_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/laser_software.yaml'

parser.add_argument('--config_hardware_in', '-i',type = str, 
                    help = 'where is the hardware yaml file stored?',
                    action = 'store')
parser.add_argument('--config_software_in', '-s',type = str, 
                    help = 'where is the software yaml file stored?',
                    action = 'store')

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

lat_objects = []
for lever in box.levers:
    lat_objects += [lever.extend()]
for i, beam in enumerate(box.beams):
    beam.monitor_

try:
    while True:
        ''''''
        time.sleep(0.05)

except KeyboardInterrupt:
    print('\n\ncleaning up')
    for lever in box.levers():
        lever.retract()
    box.shutdown()