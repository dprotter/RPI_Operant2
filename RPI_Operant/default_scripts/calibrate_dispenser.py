
from RPI_Operant.hardware.box import Box
import time
import random
import argparse
import os

RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':'test_dispenser'}
USER_CONFIG_PATH = '/home/pi/Local/laser_local_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/anne_experiment/yaml_setup_files/magazine_software.yaml'
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
 
    config_hardware_file = USER_CONFIG_PATH


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

def calibrate_stop(d):
    print('testing stop speed for d1.')
    d.stop_servo()
    inp = input(f'is {d.name} stopped? (y,n)')
    val = d.config_dict['stop']
    if not inp in ['y',]:
        inp = input('press enter to change speed. if speed increases instead of decreases enter "w". when stopped enter "y"\n')
        step = 0.01
        
        while inp not in ['y',]:
            inp = input()
            if inp in ['w',]:
                if step > 0:
                    step = -0.01
                else:
                    step = 0.01
            val += step
            d.servo.throttle = val
    print(f'stop speed for {d.name} should be {round(val,3)}')

def calibrate_speed(d):
    i = ''
    while i != 's':
        i = input('set throttle value ("s" to quit)')
        if i !='s':
            d.servo.throttle = float(i)


box = Box()
box.setup(run_dict=RUNTIME_DICT, 
              user_hardware_config_file_path=config_hardware_file,
              user_software_config_file_path=config_software_file,
              start_now=True, simulated = False)

for d in box.dispensers: 
    calibrate_stop(d)
    calibrate_speed(d)
        


box.shutdown()