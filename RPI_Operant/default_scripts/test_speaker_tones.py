from RPI_Operant.hardware.box import Box
import time
import random
from tabulate import tabulate
import RPi.GPIO as GPIO

import argparse
import os

RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':'test_speaker_tones', 'side':1}
USER_HARDWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/local_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/classical.yaml'

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

#box.speakers.speaker.play_tone('pellet', wait = True)

#box.speakers.speaker.play_tone('partner', wait = True)
tone_dict = box.software_config['speaker_tones']['speaker']['novel']
speaker = box.speakers.speaker

box.speakers.speaker.play_tone('partner', wait = True)
time.sleep(1)
box.speakers.speaker.play_tone('novel', wait = True)
time.sleep(1)
box.speakers.speaker.play_tone('minus', wait = True)
box.shutdown()