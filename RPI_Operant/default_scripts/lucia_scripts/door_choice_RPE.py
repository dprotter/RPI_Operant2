
from pickle import FALSE
from RPI_Operant.hardware.box import Box
import time
import random
from pathlib import Path
experiment_name = Path(__file__).stem
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':experiment_name}
# # For Running on the Raspberry Pi: 
USER_HARDWARE_CONFIG_PATH = '/home/pi/local_rpi_files/default_hardware_fr2.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/door_choice_RPE.yaml'


box = Box()

def run():
    
    box.setup(run_dict=RUNTIME_DICT, 
              user_hardware_config_file_path=USER_HARDWARE_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=False, simulated = False)
    
    if box.software_config['checks']['trigger_on_start']:
        
        trigger_object = box.outputs.miniscope_trigger.prepare_trigger()
    
    door_1_RPE_list = box.software_config['values']['door_1_RPE']
    door_2_RPE_list = box.software_config['values']['door_2_RPE']
    #simplifying hardware calls
    door_1 = box.doors.door_1
    door_2 = box.doors.door_2
    lever_1 = box.levers.lever_1
    lever_2 = box.levers.lever_2
    speaker = box.speakers.speaker
    delay = box.get_delay()
    
    door_1_press_count = 0
    door_2_press_count = 0
    
    if box.software_config['checks']['trigger_on_start']:
        box.start_and_trigger([trigger_object])
    box.reset()
    #get LED pulses to pass to other functions
    press_led_pulse = box.outputs.event_LED.prepare_pulse(length = box.software_config['LED_pulses']['lever_press'], pulse_string = 'lever_press')
    new_round_pulse = box.outputs.round_LED.prepare_pulse(length = box.software_config['LED_pulses']['new_round'], pulse_string = 'new_round')
    FR = box.get_software_setting(location = 'values', setting_name='FR', default = 3)
    for i in range(1,box.software_config['values']['rounds']+1, 1):

        box.timing.new_round()
        new_round_pulse()
        
        phase = box.timing.new_phase('levers_out', box.software_config['values']['lever_out'])
        
        speaker.play_tone(tone_name = 'round_start', wait = True)
        press_latency_1 = box.levers.lever_1.extend()
        press_latency_2 = box.levers.lever_2.extend(wait = True)
        
        #start the actual lever-out phase
        lever_1.wait_for_n_presses(n=FR, latency_obj = press_latency_1, on_press_events = [press_led_pulse])
        lever_2.wait_for_n_presses(n=FR, latency_obj = press_latency_2, on_press_events = [press_led_pulse])
        
        while phase.active():
        
            if lever_1.presses_reached:
                
                lever_1.retract()
                lever_2.retract()
                
                speaker.play_tone(tone_name = 'door_2_open')
                door_2_press_count +=1
                
                timeout = box.timing.new_timeout(length = delay)
                timeout.wait()
                
                phase.end_phase()
                
                if door_2_press_count in door_2_RPE_list:
                    box.timestamp_manager.create_and_submit_new_timestamp(description = 'error_trial_skipping_door', modifiers = {'ID':'door_2'})
                    box.timing.new_phase('error_trial_time', length = box.software_config['values']['error_trial_time'])
                    break
                
                reward_phase = box.timing.new_phase('reward_phase',length = box.software_config['values']['reward_time'])
                
                lat = door_2.open()
                box.beams.door2_ir.monitor_beam_break(latency_to_first_beambreak = lat, end_with_phase=reward_phase)
                
            elif lever_2.presses_reached:
                lever_1.retract()
                lever_2.retract()
                speaker.play_tone(tone_name = 'door_1_open')
                door_1_press_count +=1
                
                timeout = box.timing.new_timeout(length = delay)
                timeout.wait()
                
                phase.end_phase()
                if door_1_press_count in door_1_RPE_list:
                    box.timestamp_manager.create_and_submit_new_timestamp(description = 'error_trial_skipping_door', modifiers = {'ID':'door_1'})
                    box.timing.new_phase('error_trial_time', length = box.software_config['values']['error_trial_time'])
                    break
                reward_phase = box.timing.new_phase('reward_phase',length = box.software_config['values']['reward_time'])
                
                lat = door_1.open()
                box.beams.door1_ir.monitor_beam_break(latency_to_first_beambreak = lat, end_with_phase=reward_phase)

        if not lever_1.presses_reached and not lever_2.presses_reached:
            lever_1.retract()
            lever_2.retract()
            
        #if presses were reached, wait for reward phase
        if box.timing.current_phase.name == 'reward_phase':
            box.timing.current_phase.wait()
            if door_1.is_open():
                door_1.close()
            elif door_2.is_open():
                door_2.close()
            box.outputs.round_LED.activate()
            box.inputs.iti.wait_for_press()
            box.outputs.round_LED.deactivate()
        elif box.timing.current_phase.name == 'error_trial_time':
            box.timing.current_phase.wait()

        phase = box.timing.new_phase(name='ITI', length =box.software_config['values']['ITI_length'])
        
        phase.wait()
        
    
    
    box.shutdown()

if __name__ == '__main__':
    run()
    







