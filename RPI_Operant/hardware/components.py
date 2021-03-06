
import time
import sys

try:
    import RPi.GPIO as GPIO
except:
    print('RPi.GPIO not found')
    from RPI_Operant.hardware.Fake_GPIO import Fake_GPIO
    GPIO = Fake_GPIO()
import queue
import sys
from RPI_Operant.hardware.event_strings import OperantEventStrings as oes
import inspect

import os

try:
    if os.system('sudo lsof -i TCP:8888'):
        os.system('sudo pigpiod')
    import pigpio
except:
    print('pigpio not found')

try:
    from adafruit_servokit import ServoKit
    SERVO_KIT = ServoKit(channels=16)
except:
    print('adafruit_servokit not found')
    SERVO_KIT = None

def get_servo(ID, servo_type):
    '''take a servo positional ID on the adafruit board, and the servo type, and return a servo_kit obj'''

    if servo_type not in ('positional', 'continuous'):
        raise KeyError(f'servo type was passed as {servo_type}, must be either "positional" or "continuous"')

    if servo_type == 'positional':
        return SERVO_KIT.servo[ID]
    else:
        return SERVO_KIT.continuous_servo[ID] 


def thread_it(func):
        '''simple decorator to pass function to our thread distributor via a queue. 
        these 4 lines took about 4 hours of googling and trial and error.
        the returned 'future' object has some useful features, such as its own task-done monitor. '''
        
        def pass_to_thread(self, *args, **kwargs):
            bound_args = inspect.signature(func).bind(self, *args, **kwargs)
            bound_args.apply_defaults()
            bound_args_dict = bound_args.arguments

            new_kwargs = {k:v for k, v in bound_args_dict.items() if k not in ('self')}
            #print(f'submitting {func}')
            future = self.box.thread_executor.submit(func,self, **new_kwargs)
            self.box.worker_queue.put((future, func.__name__))

            if 'wait' in bound_args_dict.keys() and bound_args_dict['wait'] == True:
                name = func.__name__
                self.box.wait(future, name)
            return future
        return pass_to_thread

class Servo_Sim:
    def __init__(self):
        '''fake servokit to simulate'''
    def new_fake_servo(self, dict):
        
        if dict['servo_type'] == 'positional':
            return self.Servo(id =dict['servo'])
        else:
            return self.ContServo(id =dict['servo'])
    class Servo:
        def __init__(self, id):
            self.ID = id
            self.angle = 0
    
    class ContServo:
        def __init__(self, id):
            self.ID = id
            self.throttle = 0
        
SERVO_SIM = Servo_Sim() 

class Lever:
    
    def __init__(self, name, lever_config_dict, box, simulated = False):
        
        
        self.config_dict = lever_config_dict
        
        self.box = box
        self.pin = self.config_dict['pin'] #int
        self.extended = self.config_dict['extended'] #int, servo angle
        self.retracted = self.config_dict['retracted'] #int, servo angle
        self.name = name #str
        self.is_extended = False #True = extended

        if simulated:
            self.servo = SERVO_SIM.new_fake_servo(self.config_dict)
        else:
            self.servo = get_servo(self.config_dict['servo'], self.config_dict['servo_type'])
        self.target_name = self.config_dict['target_name']
        self.target_type = self.config_dict['target_type']
        
        
        if 'speaker_name' in self.config_dict.keys():
            self.speaker = self.box.speakers.get_component(self.config_dict['speaker_name'])
        else:
            self.speaker = self.box.speaker
        
        switch_dict = {
            'pin':self.pin,
            'pullup_pulldown':self.config_dict['pullup_pulldown'],
        }

        self.switch = self.box.button_manager.new_button(self.name, switch_dict, self.box)
        
        #where should these defaults live so they dont take up unnecessary space? might also put pu_pd there
        self.retraction_timeout = self.config_dict['retraction_timeout'] if 'retraction_timeout' in self.config_dict.keys() else 2
        self.interpress_timeout = self.config_dict['interpress_timeout'] if 'interpress_timeout' in self.config_dict.keys() else 0.5
        
        
        
        
        #attributes for tracking during runtime
        self.total_presses = 0
        self.presses_reached = False
        self.monitoring = False
        self.stop_threads = False
        self.lever_press_queue = queue.Queue()
        self.lever_presses = 0
        
        self.wiggle = 10
    def simulate_lever_press(self):
        self.simulate_pressed()
        time.sleep(0.1)
        self.simulate_unpressed()
        
        
    def simulate_pressed(self):
        print('simulating pressed')
        self.switch.pressed = True
    
    def simulate_unpressed(self):
        print('simulating unpressed')
        self.switch.pressed = False
        
    
    def setup_target(self): 
        self.target = self.box.get_component(self.target_type, self.target_name)
        
    def current_thread_numbers(self):
        '''return the number of current threads running, based on length of futures'''
        self.clean_futures_array()
        return len(self.futures)
    
    def clean_futures_array(self):
        '''iterate over futures as clear any that are done'''
        for fut in self.futures:
            if fut.done():
                self.futures.remove(fut)
        
    
    def extend(self):
        '''extend a lever and timestamp it'''
        
        ts = self.box.timestamp_manager.new_timestamp(description = oes.lever_extended+self.name, modifiers = {'ID':self.name})
        lat = self.box.timestamp_manager.new_latency(description = oes.lever_pressed+self.name, modifiers = {'ID':self.name})
        extend_start = max(0, self.extended-self.wiggle)

        #first, extend past final value, then retract slightly to final value
        self.servo.angle = extend_start
        time.sleep(0.05)
        self.servo.angle = self.extended
        
        self.is_extended = True
        ts.submit()
        return lat
        
    @thread_it
    def retract(self):
        '''extend a lever and timestamp it'''
        #note, make a ts object and submit later after successful retraction
        ts = self.box.timestamp_manager.new_timestamp(description = oes.lever_retracted+self.name, modifiers = {'ID':self.name})
        retract_start = max(180, self.retracted + self.wiggle)
 
        #wait for the vole to get off the lever
        timeout = self.box.timing.new_timeout(self.retraction_timeout)
        while self.switch.pressed and timeout.active():
            'hanging till lever not pressed'

        #retract further than expected, then extend to final position
        self.servo.angle = retract_start
        time.sleep(0.05)
        self.servo.angle = self.retracted
        print(f'retracting {self.name}')
        self.is_extended = False
        ts.submit()
    
    @thread_it
    def watch_lever_pin(self):
        self.monitoring = True
        while self.monitoring:
            if self.switch.pressed:
                self.total_presses +=1
                self.lever_press_queue.put(('pressed'))
                self.speaker.click_on()
                timeout = self.box.timing.new_timeout(self.retraction_timeout)
                while self.switch.pressed and timeout.active():
                    '''waiting for vole to get off lever. nothing necessary within loop'''
                self.speaker.click_off()
                
                
                #wait to loop until inter-press interval is passed
                ipt_timeout = self.box.timing.new_timeout(self.interpress_timeout)
                ipt_timeout.wait()
            time.sleep(0.015)
        #iprint(f'\n:::::: done watching a pin for {self.name}:::::\n')
    
    @thread_it
    def wait_for_n_presses(self, n = 1, reset_with_new_phase = False, latency_obj = None, reset_with_new_round = True):
        'monitor lever and wait for n_presses before '
        if latency_obj:
            latency_obj.add_modifier(key = 'presses_required', value = n)
        self.watch_lever_pin()
        if reset_with_new_phase:
            print('reset with new phase')
            #get the current phase object
            phase = self.box.timing.current_phase

            #query to see if phase is still active.
            #note: if you simply used 'while self.box.current_phase.active() you could miss shutdown, i think
            while phase.active() and not self.box.finished():
                self.monitor_lever(n, latency_obj)
            self.reset_lever()
        
        #reset with new rounds waits to exit until the round has changed
        elif reset_with_new_round:
            r = self.box.timing.round
            while r == self.box.timing.round and not self.box.finished():
                self.monitor_lever(n, latency_obj)
            self.reset_lever()
        else:
            while self.monitoring and not self.box.finished():
                self.monitor_lever(n, latency_obj)
        self.monitoring = False
    
    @thread_it
    def monitor_lever(self, n, latency_obj):
        if not self.lever_press_queue.empty():
                    print(f'{self.name} was pressed')
                    while not self.lever_press_queue.empty():
                        _ = self.lever_press_queue.get()
                        self.lever_presses += 1
                        
                        if latency_obj:
                            latency_obj.add_modifier(key = 'n_presses', value = self.lever_presses)
                            latency_obj.submit()
                        else:
                            self.box.timestamp_manager.create_and_submit_new_timestamp(oes.lever_pressed+self.name ,modifiers = {'total_presses':self.total_presses, 'ID':self.name})
                            
                        if self.lever_presses >= n:
                            if latency_obj:
                                
                                latency_obj.event_descriptor = oes.presses_reached+self.name
                                latency_obj.add_modifier(key = 'n_presses', value = self.lever_presses)
                                latency_obj.submit()
                            else:
                                self.box.timestamp_manager.create_and_submit_new_timestamp(oes.presses_reached+self.name ,modifiers ={'n_press':self.lever_presses, 'ID':self.name})
                            self.presses_reached = True
                            self.monitoring = False
                        while not self.lever_press_queue.empty():
                            _ = self.lever_press_queue.get()
    def reset_lever(self):
        self.monitoring = False
        self.presses_reached = False
        self.lever_presses = 0
        
class Button:
    
    def __init__(self, button_dict, name, box):

        #may not need this, but brings it into line with other inits
        self.box = box

        self.pin = button_dict['pin']
        self.name = name
        pullup_pulldown = button_dict['pullup_pulldown']
        
        if pullup_pulldown == 'pullup':
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.pressed_val = 0
            
        elif pullup_pulldown == 'pulldown':
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            self.pressed_val = 1
            
        else:
            raise KeyError(f'Configuration file error when instantiating Button {self.name}, must be "pullup" or "pulldown", but was passed {pullup_pulldown}')
         
        self.pressed = False
        
class ButtonManager:
    
    def __init__(self, box, simulated = False):
        
        self.box = box
        self.buttons = []
        self.running = True
        if simulated:
            self.watch_buttons_sim()
        else:
            self.watch_buttons()

    @thread_it
    def watch_buttons(self):
        while not self.box.done:
            for button in self.buttons:
                if GPIO.input(button.pin) == button.pressed_val:
                    button.pressed = True
                else:
                    button.pressed = False
            time.sleep(0.005)
    
    @thread_it
    def watch_buttons_sim(self):
        while not self.box.done:
            time.sleep(0.1)
            
    def new_button(self, name, button_dict, box = None):
        '''make a new button and add it to the button list'''
        if not box:
            box = self.box
        new_button_obj = Button(button_dict, name, box)
        self.buttons.append(new_button_obj)
        return new_button_obj
    
class Door:
    
    def __init__(self, name, door_config_dict, box, simulated = False):
        
        self.box = box 

        self.config_dict = door_config_dict
        
        if simulated:
            self.servo = SERVO_SIM.new_fake_servo(self.config_dict)
        else:
            self.servo = get_servo(self.config_dict['servo'], self.config_dict['servo_type'])
        self.stop_speed = self.config_dict['stop']
        self.close_speed = self.config_dict['close']
        self.open_speed = self.config_dict['open']
        self.open_time = self.config_dict['open_time']
        self.close_timeout = self.config_dict['close_timeout']
        self.name = name

        #real time response attributes
        
        ss_button_dict = { 
            'pin':self.config_dict['state_switch'],
            'pullup_pulldown':'pullup'
        }
        self.state_switch = self.box.button_manager.new_button(f'{self.name}_state_switch', ss_button_dict)
        self.overridden = False


        #override buttons
        oo_button_dict = { 
            'pin':self.config_dict['override_open_pin'],
            'pullup_pulldown':'pullup'
        }
        self.override_open_button = self.box.button_manager.new_button(f'{self.name}_override_open', oo_button_dict, self.box)


        oc_button_dict = { 
            'pin':self.config_dict['override_open_pin'],
            'pullup_pulldown':'pullup'
        }
        self.override_close_button  = self.box.button_manager.new_button(f'{self.name}_override_close', oc_button_dict, self.box)

        
        #start the override function
        self.override(self)
    
    def is_closed(self):
        return self.state_switch.pressed
    
    def is_open(self):
        return not self.state_switch.pressed
    
    def simulate_open(self):
        '''use to simulate the door entering the open state'''
        self.state_switch.pressed = False
        
    def simulate_closed(self):
        '''use to simulate the door entering the closed state'''
        self.state_switch.pressed = True
    
    @thread_it
    def open(self, wait = False):
        
        self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.open_door_start+self.name, modifiers = {'ID':self.name})
        self.servo.throttle = self.open_speed

        start_time = time.time()
        while time.time() < (start_time + self.open_time) and not self.overridden:
            time.sleep(0.05)
        
        self.servo.throttle = self.stop_speed

        if self.state_switch.pressed:
            print(f'{self.name} door failed to open!!!')
            self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.open_door_failure+self.name, modifiers = {'ID':self.name})
        else:
            print(f'{self.name} opened!')
            self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.open_door_finish+self.name, modifiers = {'ID':self.name})
        
    @thread_it
    def close(self, wait = True):
        '''open this door'''
        
        self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.close_door_start+self.name, modifiers = {'ID':self.name})
        self.servo.throttle = self.close_speed

        start_time = time.time()
        
        while time.time() < (start_time + self.close_timeout) and not self.overridden and not self.state_switch.pressed:
            time.sleep(0.05)
        
        self.servo.throttle = self.stop_speed

        if self.state_switch.pressed:
            print(f'{self.name} closed!')
            self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.close_door_finish+self.name, modifiers = {'ID':self.name})
            
        else:
            print(f'{self.name} door failed to close!!!')
            self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.close_door_failure+self.name, modifiers = {'ID':self.name})

    @thread_it
    def override(self, wait = False):
        while not self.box.done:
            
            if self.override_open_button.pressed:
                
                self.servo.throttle = self.open_speed
                while self.override_open_button.pressed:
                    self.overridden = True
                    time.sleep(0.05)
                
                self.servo.throttle = self.stop_speed
                self.overridden = False
                
            if self.override_close_button.pressed:
                self.servo.throttle = self.close_speed
                while self.override_close_button.pressed:
                    self.overridden = True
                    time.sleep(0.05)
                
                self.servo.throttle = self.stop_speed
                self.overridden = False

            time.sleep(0.1)

class Dispenser:

    def __init__(self, name, dispenser_config_dict, box, simulated = False):
        '''make a dispenser'''
        self.box = box
        self.config_dict = dispenser_config_dict
        self.servo_ID = self.config_dict['servo']
        if simulated:
            self.servo = SERVO_SIM.new_fake_servo(self.config_dict)
        else:
            self.servo = get_servo(self.config_dict['servo'], self.config_dict['servo_type'])
        self.name = name
        self.pellet_state = False

        sensor_dict = { 
            'pin':self.config_dict['sensor_pin'],
            'pullup_pulldown':self.config_dict['pullup_pulldown']
        }
        
        self.sensor = self.box.button_manager.new_button(f'{self.name}_sensor', sensor_dict)



    def start_servo(self):
        self.servo.throttle = self.config_dict['dispense']

    def stop_servo(self):
        self.servo.throttle =  self.config_dict['stop']

    def sensor_blocked(self):
        return self.sensor.pushed

    def simulate_dispensed(self):
        '''used in scripts to simulate a pellet being dispensed'''
        self.sensor.pressed = True
    
    def simulate_pellet_retrieved(self):
        '''used in scripts to simulate a pellet being removed from the trough'''
        self.sensor.pressed = False
    
    @thread_it
    def dispense(self):
        ''''''
        #check if pellet was retrieved or is still in trough
        if self.pellet_state:
            print('previous pellet not retrieved')
            self.box.timestamp_manager
            
        elif self.sensor_blocked:
            '''timestamp put "pellet sensor already blocked"'''
            '''wait????'''
        else:
            self.start_servo()
            read = 0
            timeout = self.box.timing.new_timeout(timeout = self.config_dict['dispense_timeout'])
            while timeout.active():
                if self.sensor.pressed:
                    read+=1
                if read > 2:
                    '''timestamp put "pellet dispensed"'''
                    self.stop_servo()
                    self.pellet_state = True
                    pellet_latency = self.box.timestamp_manager.new_latency(description = oes.pellet_retrieved, modifiers = {'ID':self.name})
                    self.monitor_pellet(pellet_latency)
                    return None
            
    
    @thread_it
    def monitor_pellet(self, pellet_latency):
        '''track when a pellet is retrieved'''
        while not self.box.finished():
            if not self.sensor_pressed:
                pellet_latency.submit()
                
class PositionalDispenser:

    def __init__(self, name, dispenser_config_dict, box, simulated = False):
        '''make a dispenser'''
        self.box = box
        self.config_dict = dispenser_config_dict
        self.servo_ID = self.config_dict['servo']
        
        if simulated:
            self.servo = SERVO_SIM.new_fake_servo(self.config_dict)
        else:
            self.servo = get_servo(self.config_dict['servo'], self.config_dict['servo_type'])
        self.positions = self.calculate_positions()
        self.current_position_index = self.set_starting_index()
        self.current_position_angle = self.positions[self.current_position_index]
        
        self.dispense_timeout = self.config_dict['dispense_timeout']
        self.name = name
        self.pellet_state = False

        sensor_dict = { 
            'pin':self.config_dict['sensor_pin'],
            'pullup_pulldown':self.config_dict['pullup_pulldown']
        }
        
        self.sensor = self.box.button_manager.new_button(f'{self.name}_sensor', sensor_dict)
        self.overridden = False

    def calculate_positions(self):
        start = self.config_dict['start']
        n = self.config_dict['n_spots']
        return [start+i*(360/n) for i in range(n)]
    
    def get_position(self):
        '''return the current position of the servo'''
        position = 10
        return position
    
    def set_starting_index(self):
        '''calculate the index closest to the current position of the servo, and return that index'''
        cur = self.get_position()
        min_index = 0
        
        for i, pos in enumerate(self.positions):
            if abs(pos-cur) < abs(self.positions[min_index]-cur):
                min_index = i
                
        return min_index

    def next_position(self):
        angle = self.positions[self.current_position_index%len(self.positions)]
        self.servo.angle = angle
        self.current_position_angle = angle
        
    def small_step_forward(self, n = 1):
        step_size = 360/(len(self.positions)*4)
        new_angle =  self.current_position_angle + step_size * n
        self.servo.angle = new_angle
        self.current_position_angle = new_angle
        
    def small_step_backwards(self, n = 1):
        step_size = 360/(len(self.positions)*4)
        new_angle =  self.current_position_angle - step_size * n
        self.servo.angle = new_angle
        self.current_position_angle = new_angle
    
    def sensor_blocked(self):
        return self.sensor.pushed

    def simulate_dispensed(self):
        '''used in scripts to simulate a pellet being dispensed'''
        self.sensor.pressed = True
    
    def simulate_pellet_retrieved(self):
        '''used in scripts to simulate a pellet being removed from the trough'''
        self.sensor.pressed = False
    
    @thread_it
    def dispense(self):
        ''''''
        #check if pellet was retrieved or is still in trough
        if self.pellet_state:
            print('previous item not retrieved')
            self.box.timestamp_manager.create_and_submite_new_timestamp(description = oes.pellet_skip, modifiers = {'ID':self.name})
            
        elif self.sensor_blocked:
            '''timestamp put "pellet sensor already blocked"'''
            '''wait????'''
        else:
            
            read = 0
            timeout = self.box.timing.new_timeout(timeout = self.dispense_timeout)
            while timeout.active():
                self.next_position()
                timeout_2 = self.box.timing.new_timeout(timeout = 0.25)
                while timeout_2.active():
                    if self.sensor.pressed:
                        read+=1
                    if read > 2:
                        '''timestamp put "pellet dispensed"'''
                        self.servo.throttle = self.stop_speed
                        self.pellet_state = True
                        self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.pellet_dispensed, modifiers = {'ID':self.name})
                        pellet_latency = self.box.timestamp_manager.new_latency(description = oes.pellet_retrieved, modifiers = {'ID':self.name})
                        self.monitor_pellet(pellet_latency)
                        return None
                    
                
                #step back to the 1/4 position in this slot
                self.small_step_backwards(n=1)
                timeout_3 = self.box.timing.new_timeout(timeout = 0.25)
                while timeout_3.active():
                    if self.sensor.pressed:
                        read+=1
                    if read > 2:
                        '''timestamp put "pellet dispensed"'''
                        self.servo.throttle = self.stop_speed
                        self.pellet_state = True
                        self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.pellet_dispensed, modifiers = {'ID':self.name})
                        pellet_latency = self.box.timestamp_manager.new_latency(description = oes.pellet_retrieved, modifiers = {'ID':self.name})
                        self.monitor_pellet(pellet_latency)
                        return None
                
                
                #go to the 3/4 position within this slot
                self.small_step_forward(n=2)
                timeout_4 = self.box.timing.new_timeout(timeout = 0.25)
                while timeout_4.active():
                    if self.sensor.pressed:
                        read+=1
                    if read > 2:
                        '''timestamp put "pellet dispensed"'''
                        self.servo.throttle = self.stop_speed
                        self.pellet_state = True
                        self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.pellet_dispensed, modifiers = {'ID':self.name})
                        pellet_latency = self.box.timestamp_manager.new_latency(description = oes.pellet_retrieved, modifiers = {'ID':self.name})
                        self.monitor_pellet(pellet_latency)
                        return None
                #here, if not luck, we will step to the next position
        self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.pellet_failure)
            
    
    @thread_it
    def monitor_pellet(self, pellet_latency):
        '''track when a pellet is retrieved'''
        while not self.box.finished():
            if not self.sensor_pressed:
                pellet_latency.submit()     

class PortDispenser(Dispenser):

    def __init__(self, name, dispenser_config_dict, box, simulated = False):
        '''make a dispenser'''
        super().__init__(name, dispenser_config_dict, box, simulated)
        
        self.step_time = self.calculate_step_time()
        self.pellet_state = False

    def calculate_step_time(self):
        return self.config_dict['full_rotation_time'] / 12

    def update_step_time(self):
        self.step_time = self.calculate_step_time()

    def next_position(self):
        self.start_servo()
        time.sleep(self.step_time)
        self.stop_servo()
    
    def sensor_blocked(self):
        return self.sensor.pushed
    
    def simulate_retrieved(self):
        '''used in scripts to simulate a pellet being removed from the trough'''
        print('simulating pellet retrieved')
        self.sensor.pressed = True
    
    @thread_it
    def dispense(self, override_pellet_state = False):
        ''''''
        #check if pellet was retrieved or is still in trough
        
        if override_pellet_state:
            self.next_position()
            self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'{oes.pellet_dispensed}_{self.name}', modifiers = {'ID':self.name})
            latency = self.box.timestamp_manager.new_latency(description = f'{oes.pellet_retrieved}_{self.name}', modifiers = {'ID':self.name})
            self.pellet_state = True
            self.monitor_pellet(latency)
        else:
            if self.pellet_state:
                self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'{oes.pellet_not_retrieved}_{self.name}', modifiers = {'ID':self.name})
                self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'{oes.pellet_skip}_{self.name}', modifiers = {'ID':self.name})
            else:
            
                self.next_position()
                self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'{oes.pellet_dispensed}_{self.name}', modifiers = {'ID':self.name})
                latency = self.box.timestamp_manager.new_latency(description = f'{oes.pellet_retrieved}_{self.name}', modifiers = {'ID':self.name})
                self.pellet_state = True
                self.monitor_pellet(latency)
            return
    
    @thread_it
    def monitor_pellet(self, pellet_latency):
        '''track when a pellet is retrieved'''
        while not self.box.finished():
            if self.sensor.pressed:
                pellet_latency.submit()
                self.pellet_state = False  
                return       

class Speaker:
    class FakeSpeaker:
        def set_PWM_frequency(self, pin, hz):
            '''print(f'speaker set to {hz} hz')'''
        def set_PWM_dutycycle(self, pin, dc):
            '''print(f'speaker set to {dc} duty cycle')'''
            
    def __init__(self, name, speaker_dict, box, simulated = False):
        self.box = box
        self.name = name
        self.pin = speaker_dict['pin']
        
        self.tone_dict = self.box.software_config['speaker_tones'][self.name]
        self.sim = simulated
        if simulated:
            self.pi = self.FakeSpeaker()
        else:
            self.pi = pigpio.pi()
        self.click_on_train = [(tone_values['hz'], tone_values['length']) for _, tone_values in self.tone_dict['click_on'].items()]
        self.click_off_train = [(tone_values['hz'], tone_values['length']) for _, tone_values in self.tone_dict['click_off'].items()]
        self.tone_queue = queue.Queue()
        self.tone_list = []
        self.hz = 0
        self.on = False
        self.speaker_queue_handler()
    
    @thread_it
    def speaker_queue_handler(self):
        while not self.box.finished():
            if not self.tone_queue.empty():

                new_tone = self.tone_queue.get()
                #start the timer on the tone now that it has arrived. set start/stop time within tone obj
                new_tone.start()
                self.tone_list.insert(0, new_tone)
                self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.tone_start + new_tone.name, modifiers = {'ID':self.name})
            
            pop_list = []
            
            #we will visit each tone from most recent to least recent. recent tones take precedence.
            #we achieve this by breaking out of this for loop after the first tone we encounter that is not complete
            for i, tone in enumerate(self.tone_list):
                
                #prepare to remove tones that are complete
                if tone.complete():
                    pop_list.append(i)
                    
                else:
                    
                    #if speaker is not on, turn it on and set frequency to tone hz
                    if not self.on:
                        self.set_hz(int(tone.get_hz()))
                        self.set_on()
                        
                        
                        if self.sim:
                            print(f'simulated speaker playing {tone.name}')
                        break
                    #if speaker is on but current hz doesnt match most recent tone
                    elif self.hz != int(tone.get_hz()):
                        
                        self.set_hz(int(tone.get_hz()))
                        
                        if self.sim:
                            print(f'simulated speaker switching to {tone.name}')
                        break
                    else:
                        break
                
            #remove tones from tone list, starting with largest and moving backwards to prevent 
            #changes in index as tones are removed
            pop_list.reverse()
            for i in pop_list:
                
                t = self.tone_list.pop(i)
                
                self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.tone_stop + t.name, modifiers = {'ID':self.name})
                
            
            #if no tone are left, turn off speaker
            if len(self.tone_list) == 0:
                
                self.set_off()
            
            

    def turn_off(self):
        self.pi.set_PWM_dutycycle(self.pin, 0)                  
                    
    def set_hz(self, hz):
        self.pi.set_PWM_frequency(self.pin, int(hz))
        self.hz = hz


    @thread_it
    def play_tone(self, tone_name):
        '''use pigpio to play a tone, called by name from the dict imported from software config file'''
        if not tone_name in self.tone_dict.keys():
            raise KeyError(f'tone: {tone_name} was not defined in the softare dictionary')
        else:
            hz = self.tone_dict[tone_name]['hz']
            length = self.tone_dict[tone_name]['length']
            self.tone_queue.put(Tone(hz, length, tone_name))

    """def click_on(self):
        '''play through a designated train of tones.'''
        tt = ToneTrain('click_on')
        for hz, length in self.click_on_train:
            tt.add_tone(Tone(hz, length, 'click_on'))
        self.tone_queue.put(tt)
        time.sleep(tt.total_duration)
        
        
    
    def click_on_off(self):
        '''play through a designated train of tones.'''
        tt = ToneTrain('click')
        for hz, length in self.click_on_train:
            tt.add_tone(Tone(hz, length, 'click_on_off'))
        for hz, length in self.click_off_train:
            tt.add_tone(Tone(hz, length, 'click_on_off'))
        self.tone_queue.put(tt)
        time.sleep(tt.total_duration)
    
    def click_off(self):
        '''play through a designated train of tones.'''
        tt = ToneTrain('click_off')
        for hz, length in self.click_off_train:
            tt.add_tone(Tone(hz, length, 'click_off'))
        self.tone_queue.put(tt)
        time.sleep(tt.total_duration)"""

    @thread_it
    def click_on(self):
        '''play through a designated train of tones.'''
        for hz, length in self.click_on_train:
            self.set_hz(int(hz))
            self.set_on()
            time.sleep(length)
        
        
        self.set_off()

    @thread_it
    def click_off(self):
        '''play through a designated train of tones.'''
        
        for hz, length in self.click_off_train:
            self.set_hz(int(hz))
            self.set_on()
            time.sleep(length)
        
        self.set_off


    def set_on(self):
        if not self.on:
            self.on = True
            self.pi.set_PWM_dutycycle(self.pin, 255/2)

    def set_off(self):
        self.on = False
        self.pi.set_PWM_dutycycle(self.pin, 0)


class Tone:
    def __init__(self, hz, duration, name):
        
        self.duration = duration
        self.hz = hz
        self.name = name
    
    def start(self):
        self.start_time = time.time()
        self.stop_time = self.start_time + self.duration

    def get_hz(self):
        return self.hz
    
    def complete(self):
        return time.time() >= self.stop_time

class ToneTrain(Tone):
    def __init__(self, name):
        self.tone_list = []
        self.name = name
        self.position = 0
        self.total_duration = 0

    def start(self):
        self.tone_list[self.position].start()

    def add_tone(self, tone):
        self.tone_list.append(tone)
        self.total_duration += tone.duration
        
    
    def check_tone_list(self):
        
        if self.tone_list[self.position].complete():
            self.position+=1
            if self.position < len(self.tone_list):
                self.tone_list[self.position].start()
                return True
            else:
                return False

            
    def get_hz(self):
        tones_remain = self.check_tone_list()
        if tones_remain:
            return self.tone_list[self.position].get_hz()
        else:
            return 0
    
    def complete(self):
        if self.check_tone_list():
            return False
        else:
            return True

class Beam:
    
    def __init__(self, name, beam_config_dict, box):
        
        
        self.config_dict = beam_config_dict
        
        self.box = box
        self.pin = self.config_dict['pin'] #int

        self.name = name #str
        
        switch_dict = {
            'pin':self.pin,
            'pullup_pulldown':self.config_dict['pullup_pulldown'],
        }

        self.switch = self.box.button_manager.new_button(self.name, switch_dict, self.box)
        
        
class Fake_GPIO:
    def __init__(self):
        self.IN = 1
        self.OUT = 0
    
    def setup(self, pin, val):
        pass
    
    def input(self, pin):
        return 3