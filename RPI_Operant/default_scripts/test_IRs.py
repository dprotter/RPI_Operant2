from RPI_Operant.hardware.box import Box
import time
import random
from tabulate import tabulate
import RPi.GPIO as GPIO

import argparse
import os

RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':'show_outputs', 'side':1}
USER_HARDWARE_CONFIG_PATH ='/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/local_hardware.yaml'
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

speaker = box.speakers.speaker


beams = []

if hasattr(box, 'nose_pokes'):
    for nosepoke in box.nose_pokes:
        nosepoke.set_current_on_poke_events([speaker.click_on])
        nosepoke.begin_monitoring()

if hasattr(box, 'beams'):
    for beam in box.beams:
        tone_dict = {'type':'continuous', 
                     'tone_name':'test_ir', 
                     'hz':2000,
                     'length':0.5}
        
        #use lambda here to prep a tone to play so that arguments can be used
        beam.monitor_and_do_events(events = [lambda: speaker.play_tone_from_dictionary(tone_dict)])
time.sleep(1)


try:
    while True:
       '''''' 

except KeyboardInterrupt:
    print('\n\ncleaning up')
for lever in box.levers():
    lever.retract(wait = True)
box.shutdown()
time.sleep(1)
