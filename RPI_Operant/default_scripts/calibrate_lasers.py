
from RPI_Operant.hardware.box import Box
import time
import random

USER_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/laser_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/laser_software.yaml'

box = Box()    
box.setup(user_hardware_config_file_path=USER_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=True, simulated = False)


def calibrate_laser(l):

    inp =input(f'enter an "s" to skip to the next laser, or enter any key to test {l.name} \n')
    if not inp == 's':
        while not inp == 's':
            inp = input(f'enter a "1" to turn laser {l.name} ON, enter a "0" to turn laser {l.name} OFF')
            if not inp == 's':
                if int(inp) != 0 and int(inp) != 1: 
                    print(f'did not recognize the input {inp}')
                else: 
                    if int(inp) == 1: 
                        # turn on 
                        l.turn_on()
                    else: 
                        # turn off 
                        l.turn_off()


for l in box.lasers:
    calibrate_laser(l)

box.shutdown()


