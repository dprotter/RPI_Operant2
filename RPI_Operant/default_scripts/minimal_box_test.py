from RPI_Operant.hardware.box import Box

from pathlib import Path
experiment_name = Path(__file__).stem
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':experiment_name, 'port_side':'same'}
# # For Running on the Raspberry Pi: 
USER_HARDWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/minimal_box_test_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/minimal_box_software.yaml'
 
box = Box()

def run():
    
    box.setup(run_dict=RUNTIME_DICT, 
              user_hardware_config_file_path=USER_HARDWARE_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=True, simulated = False, verbose = False)
    
    phase = box.timing.new_phase('setup_phase', length = 2)
    total_time = box.get_software_setting(location = 'values', setting_name = 'experiment_length', default = 30*60)

    box.reset()
    
    door_1 = box.linear_rail_doors.door_1
    door_2 = box.linear_rail_doors.door_2
    speaker = box.speakers.speaker
    poke_d1 = box.nose_pokes.nose_port_1
    
    phase.wait()
    
    
    poke_d1.begin_monitoring()
    
    
    total_time_phase = box.timing.new_phase('experiment', length = total_time)
        
        
    door_1_reward = False
    door_2_reward = False

    FR = 1

    poke_d1.set_poke_target(FR)
    poke_d1.activate_LED()


    pokes_active_phase = box.timing.new_phase('pokes_active', length = total_time_phase.get_time_remaining())


    while total_time_phase.active():
            
        if door_1_reward:
            if not d1_reward_phase.active():
                door_1_reward = False
                door_1.close(wait = True)
                pokes_active_phase = box.timing.new_phase('pokes_active', length = total_time_phase.get_time_remaining())
                poke_d1.set_poke_target(FR)
                poke_d1.activate_LED()

            
            
        if poke_d1.pokes_reached and not door_1_reward:

            pokes_active_phase.end_phase()
            poke_d1.deactivate_LED()
            
            # speaker.play_tone(tone_name = f'door_1_open', wait = True)
            door_1.open()
            door_1_reward = True
            d1_reward_phase = box.timing.new_phase(f'reward_phase_door_1',length = box.software_config['values']['reward_length'])
            poke_d1.reset_poke_count()
                
        if door_1_reward:
            d1_reward_phase.wait()
            door_1.close()
            box.timing.new_timeout(length = 1)
            
    box.shutdown()

if __name__ == '__main__':
    run()
