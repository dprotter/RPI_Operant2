from RPI_Operant.hardware.box import Box
import time
import random
from tabulate import tabulate
import RPi.GPIO as GPIO

RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':'cooperant_magazine', 'side':1}
USER_HARDWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/default_cooperant_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/cooperant_magazine.yaml'

box = Box()
box.setup(run_dict=RUNTIME_DICT, 
            user_hardware_config_file_path=USER_HARDWARE_CONFIG_PATH,
            user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
            start_now=True)

for lever in box.levers:
    lever.extend()
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
        lever.retract()
    box.shutdown()