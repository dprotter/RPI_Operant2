from RPI_Operant.hardware.box import Box
import time as time
from pathlib import Path
experiment_name = Path(__file__).stem
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':experiment_name, 'port_side':'same'}
# # For Running on the Raspberry Pi: 
USER_HARDWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/serial_motor_test_setup.yaml'
# USER_SOFTWARE_CONFIG_PATH = '/home/pi/miniscope_dec_2022/setup_files/door_train.yaml'
 
box = Box()

def run():
    
    box.setup(run_dict=RUNTIME_DICT, 
              user_hardware_config_file_path=USER_HARDWARE_CONFIG_PATH,
            #   user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=True, simulated = False, verbose = False)
    phase = box.timing.new_phase('setup_phase', length = 1)
    box.reset()
    phase.wait()
    door_2 = box.linear_rail_doors.door_2

    velocity = 0
    duration = 2
    while velocity not in ['q']:
        
        velocity = input('set vactual (rpm)\n("q" to exit, "d" to reset duration (default 2))\n')
        
        if velocity in ['d', 'q']:
            if velocity == 'q':
                break
            else:
                try:
                    duration =input('set duration\n')
                    duration = float(duration)
                    continue
                except:
                    duration = 2
                    print('duration not accepted, must be int/float')
        else:
            try:
                velocity = float(velocity)
            except:
                velocity = 0
                print('velocity not accepted. must be int/float')
        door_2._open_dir_at_velocity(velocity = velocity, duration = duration, wait = True)
        door_2._disable()
    
    
    
    box.shutdown()

if __name__ == '__main__':
    run()
    

    
