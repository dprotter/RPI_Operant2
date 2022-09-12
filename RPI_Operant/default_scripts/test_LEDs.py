from RPI_Operant.hardware.box import Box
import time
import random
from tabulate import tabulate
import RPi.GPIO as GPIO

import argparse
import os

RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':'cooperant_magazine', 'side':1}
USER_HARDWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/default_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/default_magazine.yaml'

box = Box()
box.setup(run_dict=RUNTIME_DICT, 
            user_hardware_config_file_path=USER_HARDWARE_CONFIG_PATH,
            user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
            start_now=True)

for output in box.outputs:
    print(f'testing output: {output.name}')
    for _ in range(4):
        output.activate()
        time.sleep(0.25)
        output.deactivate()

box.shutdown()