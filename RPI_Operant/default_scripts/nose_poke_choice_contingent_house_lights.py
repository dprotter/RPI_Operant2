from RPI_Operant.hardware.box import Box

from pathlib import Path
experiment_name = Path(__file__).stem
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':experiment_name, 'port_side':'same'}
# # For Running on the Raspberry Pi: 
USER_HARDWARE_CONFIG_PATH = '/home/pi/makenzie_experiment/local_nosepoke_hardware_house_lights.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/makenzie_experiment/makenzie_operant/setup_files/nose_poke.yaml'
 
box = Box()

def run():
    
    box.setup(run_dict=RUNTIME_DICT, 
              user_hardware_config_file_path=USER_HARDWARE_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=True, simulated = False, verbose = False)
    phase = box.timing.new_phase('setup_phase', length = 3)
    box.reset()
    
    door_1 = box.doors.door_1
    door_2 = box.doors.door_2

    box.nose_pokes.nose_port_1.deactivate_LED()
    box.nose_pokes.nose_port_2.deactivate_LED()
    
    if RUNTIME_DICT['port_side'] == 'same':
    #simplifying hardware calls
        poke_d1 = box.nose_pokes.nose_port_1
        poke_d2 = box.nose_pokes.nose_port_2
        print('poke_2 == door_2\npoke_1==door_1')
    elif RUNTIME_DICT['port_side'] == 'opposite':
        poke_d1 = box.nose_pokes.nose_port_2
        poke_d2 = box.nose_pokes.nose_port_1
        print('poke_2 == door_1\npoke_1==door_2')
    else:
        print(f'port side wasnt parsed, but was given as {RUNTIME_DICT["port_side"]}')
    
    speaker = box.speakers.speaker
    delay = box.get_delay()
    FR = box.get_software_setting(location = 'values', setting_name='FR', default = 1)
    #start beam break monitoring. calculate durations
    box.beams.door1_ir.start_getting_beam_broken_durations() 
    box.beams.door2_ir.start_getting_beam_broken_durations()
    d1_reward_phase = box.timing.new_phase('reward_phase',length = 0.05)
    d2_reward_phase = box.timing.new_phase('reward_phase',length = 0.05)
    house_light = box.house_lights.house_light
    
    phase.wait()
    total_time = box.get_software_setting(location = 'values', setting_name = 'experiment_length', default = 30*60)
    
    #wait to finish setup
    
    box.timing.new_round()

    poke_d1.begin_monitoring()
    poke_d2.begin_monitoring()

    total_time_phase = box.timing.new_phase('experiment', length = total_time)
    
    
    door_1_reward = False
    door_2_reward = False
    


    poke_d1.set_poke_target(FR)
    poke_d1.activate_LED(percent_brightness = 50)
    
    poke_d2.set_poke_target(FR)
    poke_d2.activate_LED(percent_brightness = 50)
    pokes_active_phase = box.timing.new_phase('pokes_active', length = total_time_phase.get_time_remaining())
    house_light.activate(pct = 100)
    
    while total_time_phase.active():
        
        if door_1_reward:
            if not d1_reward_phase.active():
                door_1_reward = False
                door_1.close(wait = True)
                pokes_active_phase = box.timing.new_phase('pokes_active', length = total_time_phase.get_time_remaining())
                poke_d1.set_poke_target(FR)
                poke_d2.set_poke_target(FR)
                poke_d1.activate_LED()
                poke_d2.activate_LED()
                house_light.activate(pct = 100)
        
        if door_2_reward:
            if not d2_reward_phase.active():
                door_2_reward = False
                door_2.close(wait = True)
                pokes_active_phase = box.timing.new_phase('pokes_active', length = total_time_phase.get_time_remaining())
                poke_d1.set_poke_target(FR)
                poke_d2.set_poke_target(FR)
                poke_d1.activate_LED()
                poke_d2.activate_LED()
                house_light.activate(pct = 100)
            
            
        if poke_d1.pokes_reached and not door_1_reward:
            house_light.activate(pct = 25)
            pokes_active_phase.end_phase()
            poke_d1.deactivate_LED()
            poke_d2.deactivate_LED()
            speaker.play_tone(tone_name = f'door_1_open', wait = True)
            timeout = box.timing.new_timeout(length = delay)
            timeout.wait()
            door_1.open()
            door_1_reward = True
            d1_reward_phase = box.timing.new_phase(f'reward_phase_door_1',length = box.software_config['values']['reward_length'])
            poke_d1.reset_poke_count()
            poke_d2.reset_poke_count()
        
        if poke_d2.pokes_reached and not door_2_reward:
            house_light.activate(pct = 25)
            pokes_active_phase.end_phase()
            poke_d1.deactivate_LED()
            poke_d2.deactivate_LED()
            speaker.play_tone(tone_name = f'door_2_open', wait = True)
            timeout = box.timing.new_timeout(length = delay)
            timeout.wait()
            door_2.open()
            door_2_reward = True
            d2_reward_phase = box.timing.new_phase(f'reward_phase_door_2',length = box.software_config['values']['reward_length'])
            poke_d1.reset_poke_count()
            poke_d2.reset_poke_count()
            
            
    if door_1_reward or door_2_reward:
        if door_2_reward:
            d2_reward_phase.wait()
            door_2.close()
        else:
            d1_reward_phase.wait()
            door_1.close()
        
        box.timing.new_timeout(length = 1)
    box.shutdown()

if __name__ == '__main__':
    run()
    
