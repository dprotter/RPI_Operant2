
from RPI_Operant.hardware.box import Box
import time
import random

USER_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/default_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/default_software.yaml'

box = Box()    
box.setup(user_hardware_config_file_path=USER_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=True, simulated = True)


def calibrate_lever(lever):
    l = lever

    inp =input(f'press enter to extend lever:{l.name} or "s" to skip\n')
    if not inp == 's':
        print(f'lever extended val is {l.config_dict["extended"]}. try a new value. enter "s" to exit.\n')
        while not inp == 's':
            inp = input()
            if not inp == 's':
                try:
                    l.servo.angle = int(inp)
                except:
                    print('out of range')

    inp =input(f'press enter to retract lever:{l.name} or "s" to skip\n')
    if not inp == 's':
        print(f'lever retracted val is {l.config_dict["retracted"]}. try a new value. enter "s" to exit.\n')
        while not inp == 's':
            inp = input()
            if not inp == 's':
                try:
                    l.servo.angle = int(inp)
                except:
                    print('out of range')

for l in box.levers:
    calibrate_lever(l)

box.shutdown()


