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
USER_SOFTWARE_CONFIG_PATH = '/home/pi/RPI_Operant2/RPI_Operant/default_setup_files/door_train.yaml'


box = Box()

def run():
    
    box.setup(run_dict=RUNTIME_DICT, 
              user_hardware_config_file_path=USER_HARDWARE_CONFIG_PATH,
              user_software_config_file_path=USER_SOFTWARE_CONFIG_PATH,
              start_now=False, simulated = False)
    
    if box.software_config['trigger_on_start']:
        
        trigger_object = box.outputs.miniscope_trigger.prepare_trigger()
    
    #simplifying hardware calls
    door_1 = box.doors.door_1
    door_2 = box.doors.door_2
    lever_1 = box.levers.lever_1
    lever_2 = box.levers.lever_2
    speaker = box.speakers.speaker
    delay = box.get_delay()
    
    if box.software_config['trigger_on_start']:
        box.start_and_trigger([trigger_object])
    
    #get LED pulses to pass to other functions
    press_led_pulse = box.outputs.event_LED.prepare_pulse(length = 0.35, pulse_string = 'lever_press')
    
    lever = lever_2
    next_lever = lever_1
    
    door = door_1
    next_door = door_2
    
    tone = 'door_1_open'
    next_tone = 'door_2_open'
    
    rep = 1
    for i in range(1,box.software_config['values']['reps']*box.software_config['values']['sets']+1, 1):
        
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
            
            
            
        
        box.timing.new_round(length = box.software_config['values']['round_length'])
        
        phase = box.timing.new_phase(lever.name + 'out', box.software_config['values']['lever_out'])
        speaker.play_tone(tone_name = 'start_of_round')
        press_latency = box.levers.food.extend()
        
        #start the actual lever-out phase
        lever.wait_for_n_presses(n=1, latency_obj = press_latency, on_press_events = [press_led_pulse])
        while phase.active() and not lever.presses_reached:
            '''waiting here for something to happen'''
        
            if lever.presses_reached:
                lever.retract()
                speaker.play_tone(tone_name = tone)
                
                timeout = box.timer.new_timeout(length = delay)
                timeout.wait()
                
                phase.end_phase()
                reward_phase = box.timing.new_phase('reward_phase',length = box.software_config['reward_time'])
                
                lat = door.open()
                box.beams.door2_ir.monitor_beam_break(latency_to_first_beambreak = lat, end_with_phase=phase)

        #only dispense if not already dispensed
        if not lever.presses_reached:
            lever.retract()
       
        #if presses were reached, wait for reward phase
        if lever.presses_reached:
            reward_phase.wait()
            door.close()
        
        #if door was opened, wait until experimenter is ready to start ITI (has moved vole)
        if lever.presses_reached:
            box.buttons.ITI.wait_for_press()
            
        phase = box.timing.new_phase(name='ITI', length = box.timing.round_time_remaining())
        
        phase.wait()
        
    
    
    box.shutdown()

if __name__ == '__main__':
    run()
    







