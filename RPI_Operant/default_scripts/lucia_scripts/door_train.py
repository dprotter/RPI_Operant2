'''INCOMPLETE
UNTESTED'''


from pickle import FALSE
from RPI_Operant.hardware.box import Box
import time
import random
from pathlib import Path
experiment_name = Path(__file__).stem
RUNTIME_DICT = {'vole':000, 'day':1, 'experiment':experiment_name}
# # For Running on the Raspberry Pi: 
USER_HARDWARE_CONFIG_PATH = '/home/pi/local_rpi_files/default_hardware.yaml'
USER_SOFTWARE_CONFIG_PATH = '/home/pi/dave_miniscope_debug/setup_files/door_train.yaml'


box = Box()

def run():
    
    box.setup(run_dict=RUNTIME_DICT, 
              user_hardware_config_file_path=USER_HARDWARE_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=False, simulated = False)
    phase = box.timing.new_phase('setup_phase', length = 5)
    
    if box.software_config['checks']['trigger_on_start']:
        
        trigger_object = box.outputs.miniscope_trigger.prepare_trigger()
    
    #simplifying hardware calls
    door_1 = box.doors.door_1
    door_2 = box.doors.door_2
    lever_1 = box.levers.lever_1
    lever_2 = box.levers.lever_2
    speaker = box.speakers.speaker
    delay = box.get_delay()
    
    if box.software_config['checks']['trigger_on_start']:
        box.start_and_trigger([trigger_object])
    box.reset()
    #get LED pulses to pass to other functions
    press_led_pulse = box.outputs.event_LED.prepare_pulse(length = box.software_config['LED_pulses']['lever_press'], pulse_string = 'lever_press')
    new_round_pulse = box.outputs.round_LED.prepare_pulse(length = box.software_config['LED_pulses']['new_round'], pulse_string = 'new_round')
    
    lever = lever_2
    next_lever = lever_1
    
    door = door_1
    next_door = door_2
    
    tone = 'door_1_open'
    next_tone = 'door_2_open'
    
    rep = 1
    phase.end_phase()
    for i in range(1,box.software_config['values']['reps']*box.software_config['values']['sets']*2+1, 1):
        
        if rep > box.software_config['values']['reps']:
            rep = 1
            d = door
            l = lever
            t = tone
            
            lever = next_lever
            door = next_door
            tone = next_tone
            
            next_lever = l
            next_door = d
            next_tone = t
            
            
            
        
        box.timing.new_round()
        new_round_pulse()
        
        lever_phase = box.timing.new_phase(lever.name + '_out', 
        box.software_config['values']['lever_out'])
        speaker.play_tone(tone_name = 'round_start', wait = True)
        pause = box.timing.new_timeout(length = 0.5)
        pause.wait()
        press_latency = lever.extend()
        
        #start the actual lever-out phase
        lever.wait_for_n_presses(n = box.software_config['FR'], latency_obj = press_latency, on_press_events = [press_led_pulse])
        while lever_phase.active():
            '''waiting here for something to happen'''
        
            if lever.presses_reached:
                lever.retract()
                speaker.play_tone(tone_name = tone, wait = True)
                
                timeout = box.timing.new_timeout(length = delay)
                timeout.wait()
                
                lever_phase.end_phase()
                reward_phase = box.timing.new_phase('reward_phase',length = box.software_config['values']['reward_length'])
                
                lat = door.open()
                
                if door.name == 'door_1':
                    box.beams.door1_ir.monitor_beam_break(latency_to_first_beambreak = lat, end_with_phase=reward_phase)
                else:
                    box.beams.door2_ir.monitor_beam_break(latency_to_first_beambreak = lat, end_with_phase=reward_phase)

        #only dispense if not already dispensed
        if not lever.presses_reached:
            lever.retract()
            speaker.play_tone(tone_name = tone, wait = True)
                
            timeout = box.timing.new_timeout(length = delay)
            timeout.wait()
            
            lever_phase.end_phase()
            reward_phase = box.timing.new_phase('reward_phase',length = box.software_config['values']['reward_length'])
            
            lat = door.open()
            
            if door.name == 'door_1':
                box.beams.door1_ir.monitor_beam_break(latency_to_first_beambreak = lat, end_with_phase=reward_phase)
            else:
                box.beams.door2_ir.monitor_beam_break(latency_to_first_beambreak = lat, end_with_phase=reward_phase)
            
       
        
        reward_phase.wait()
        door.close()

        box.outputs.round_LED.activate()
        box.inputs.iti.wait_for_press()
        box.outputs.round_LED.deactivate()
        lever.reset_lever()
        
            
        phase = box.timing.new_phase(name='ITI', length = box.software_config['values']['ITI_length'])
        
        phase.wait()
        rep+=1
    
    
    box.shutdown()

if __name__ == '__main__':
    run()
    







