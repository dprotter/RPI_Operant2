
from RPI_Operant.hardware.box import Box
import time
import random
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':'test_dispenser'}
USER_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/default_cooperant_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/cooperant_magazine.yaml'

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

def rough_calibrate(dispenser):
    d = dispenser
    name = dispenser.name
    print(f'press enter to start rotation on {name}. press enter to stop after 4 full rotations. enter "s" to skip this dispenser.')
    inp = input()
    if not inp in ('s',):
       
        pass_test = False
        while not pass_test:
            start = time.time()
            d.start_servo()
            input()
            stop_time = time.time()

            if stop_time - start < 7.5:
                print(f'servo speed too fast., slowing down')
                if d.config_dict['dispense'] > d1.config_dict['stop']:
                    d.config_dict['dispense'] -= 0.01 * (7.5 - (stop_time - start))
                    print(f'new speed {d.config_dict["dispense"]}')
                
                else:
                    d.config_dict['dispense'] += 0.01 * (7.5 - (stop_time - start))
                    print(f'new speed {d.config_dict["dispense"]}')


            elif stop_time - start > 8.5:
                print(f'servo speed too slow., speeding up')
                if d.config_dict['dispense'] > d1.config_dict['stop']:
                    d.config_dict['dispense'] += 0.01 * (7.5 - (stop_time - start))
                    print(f'new speed {d.config_dict["dispense"]}')
                
                else:
                    d.config_dict['dispense'] -= 0.01 * (7.5 - (stop_time - start))
                    print(f'new speed {d.config_dict["dispense"]}')
            else:
                d.stop_servo()
                pass_test = True
                t = (stop_time - start)/4
                print(f'calibration for {name} complete. servo speed = {d.config_dict["dispense"]}, and appx time = {t}')
                d.config_dict['full_rotation_time'] = t
            if not pass_test:
                d.stop_servo()
                print(f'press enter to start rotation on {name}. press enter to stop after 4 full rotations. enter "s" to skip this dispenser.')
                inp = input()
                if inp == 's':
                    pass_test = True
                    t = (stop_time - start)/4
                    print(f'calibration for {name} complete. servo speed = {d.config_dict["dispense"]}, and appx time = {t}')
                    d.config_dict['full_rotation_time'] = t
    
    

def fine_calibrate(dispenser):
    d = dispenser
    
    rot_time = d.config_dict['full_rotation_time']
    pass_test = False
    while not pass_test:
        input(f'please align calibration dots on {d.name}, then press enter')
        start = time.time()
        timeout = d.box.timing.new_timeout(rot_time)
        d.start_servo()
        timeout.wait()
        d.stop_servo()

        inp = float(input('how far off of the center of the dispensing hole is the dot? + for too far, - for not far enough.\n(ie +0.25 for a quart of a hole too far)\n0 to exit\n'))

        if inp == 0.0:
            pass_test = True
        else:
            rot_time_new = rot_time / ((inp+12)/12)
            pass_test = False
            print(f'old time:{rot_time}, new time: {rot_time_new}')
            rot_time = rot_time_new
            
    d.config_dict['full_rotation_time'] = rot_time
    print(f'rotation time for {d.name} is {rot_time}')
            
def test_steps(dispenser):
    d = dispenser
    name = dispenser.name
    print(f'press enter to start rotation on {name}. press enter to stop after 4 full rotations. enter "s" to skip this dispenser.')
    inp = input()
    if not inp in ('s',):
        inp = input('align calibration dots, and press enter to step through each position. enter "s" to exit')
        
        while not inp == 's':
            inp = input()
            d.next_position()

box = Box()
box.setup(run_dict=RUNTIME_DICT, 
              user_hardware_config_file_path=USER_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=True, simulated = False)

d1 = box.port_dispensers.dispenser_1
d2 = box.port_dispensers.dispenser_2

calibrate_stop(d1)
calibrate_stop(d2)

rough_calibrate(d1)
rough_calibrate(d2)

fine_calibrate(d1)
fine_calibrate(d2)

test_steps(d1)
test_steps(d2)

box.shutdown()