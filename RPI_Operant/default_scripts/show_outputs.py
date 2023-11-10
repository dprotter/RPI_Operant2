from RPI_Operant.hardware.box import Box
import time
import random
from tabulate import tabulate
import RPi.GPIO as GPIO

import argparse
import os

RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':'show_outputs', 'side':1}
USER_HARDWARE_CONFIG_PATH = '/home/pi/makenzie_experiment/local_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/default_software.yaml'

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
try:
    for lever in box.levers:
        lever.extend()
except:
    pass
print(f'{len(box.button_manager.buttons)} buttons')
time.sleep(1)
def print_pin_status(bm):
    num_buttons = len(bm.buttons)

    print("\033c", end="")
    
    status = []
    for i in range(0,num_buttons,2):
        
        if i+1<num_buttons:
            b1 = bm.buttons[i]
            b2 = bm.buttons[i+1]
            status += [[b1.name, b1.pressed, b2.name, b2.pressed]]
        else:
            b1 = bm.buttons[i]
            status += [[b1.name, b1.pressed, '', '']]
    print(tabulate(status, headers = ['button', 'status', 'button', 'status']))
    time.sleep(0.05)

try:
    while True:
        print_pin_status(box.button_manager)
        time.sleep(0.05) 

except KeyboardInterrupt:
    print('\n\ncleaning up')
for lever in box.levers():
    lever.retract(wait = True)
box.shutdown()
