from RPI_Operant.hardware.box import Box
import time
from pathlib import Path
experiment_name = Path(__file__).stem
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':experiment_name}
# # For Running on the Raspberry Pi: 
USER_HARDWARE_CONFIG_PATH = '/home/pi/makenzie_experiment/local_nosepoke_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/makenzie_experiment/makenzie_operant/setup_files/nose_poke.yaml'
 
box = Box()

def run():
    
    box.setup(run_dict=RUNTIME_DICT, 
              user_hardware_config_file_path=USER_HARDWARE_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=True, simulated = False, verbose = False)
    phase = box.timing.new_phase('setup_phase', length = 1)
    box.reset()
    
    #simplifying hardware calls
    door_1 = box.doors.door_1
    door_2 = box.doors.door_2
    poke_1 = box.nose_pokes.nose_port_1
    poke_2 = box.nose_pokes.nose_port_2

    
    phase.wait()
    total_time = box.get_software_setting(location = 'values', setting_name = 'experiment_length', default = 30*60)
    
    #wait to finish setup
    
    box.timing.new_round()

    poke_1.begin_monitoring()
    poke_2.begin_monitoring()
    poke_1.activate_LED()
    poke_2.activate_LED()
    time.sleep(2)
    poke_1.deactivate_LED()
    poke_2.deactivate_LED()
    time.sleep(2)
    for pct in [100, 75, 50, 25, 10, 5]:
        print(pct)
        poke_1.activate_LED(percent_brightness = pct)
        poke_2.activate_LED(percent_brightness = pct)
        time.sleep(1)
    poke_1.deactivate_LED()
    poke_2.deactivate_LED()
    box.shutdown()

if __name__ == '__main__':
    run()
    
