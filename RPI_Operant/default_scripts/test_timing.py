from RPI_Operant.hardware.box import Box
import time
import copy
import random
from tabulate import tabulate
import RPi.GPIO as GPIO

import argparse
import os

RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':'cooperant_magazine', 'side':1}
USER_HARDWARE_CONFIG_PATH = '/home/pi/anne_experiment/yaml_setup_files/laser_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/anne_experiment/yaml_setup_files/laser_software.yaml'


box = Box()
box.setup(run_dict=RUNTIME_DICT, 
            user_hardware_config_file_path=USER_HARDWARE_CONFIG_PATH,
            user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
            start_now=True)


# use time.perf_counter() to time portions of the code! 


time.sleep(1)

t1 = time.perf_counter() # start timing 
copy_box = copy.copy(box)
t2 = time.perf_counter() # stop timing
print('Time to Shallow Copy: ', t2-t1)
print('original box: ', box)
print('copied box: ', copy_box)

# get a latency object returned from any levers extend function
lever1 = box.levers.door_1
press_latency_1 = lever1.extend()
lever1.retract()

print('original latency object: ', press_latency_1)

# Make Copies of Latency Objects 
copy1_lat = copy.copy(press_latency_1)
copy2_lat = copy.copy(press_latency_1)

# Print Address and Attribute Information of the new copies! 
print('1st copy of latency: ', copy1_lat)
print('2nd copy of latency: ', copy2_lat)
print('Modifying Both Latency copies... ')
print('\n')
copy1_lat.add_modifier(key='1', value='1')
# copy2_lat.add_modifier(key='2', value='2')
print('1st copy of latency after modification: ', copy1_lat.modifiers)
print('2nd copy of latency after modification: ', copy2_lat.modifiers)

time.sleep(1)

copy1_lat.submit()
time.sleep(4)
copy2_lat.submit()

print('1st copy of latency after submitting: ', copy1_lat)
print('2nd copy of latency after submitting: ', copy2_lat)

box.shutdown()

'''

print('Latency object Copy:', copy_lat)
t1 = time.perf_counter() # start timing 
copy_lat = copy.deepcopy(box)
t2 = time.perf_counter() # stop timing
print('Time to Deep Copy: ', t2-t1)


box.shutdown()'''