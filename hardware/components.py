import time
import RPi.GPIO as GPIO
import queue
from concurrent.futures import ThreadPoolExecutor
import threading
from hardware.event_strings import OperantEventStrings as oes
import inspect

from adafruit_servokit import ServoKit
SERVO_KIT = ServoKit(channels=16)


class Lever:
    
    def __init__(self, name, lever_config_dict, box):
        
        
        self.config_dict = lever_config_dict
        
        self.box = box
        self.pin = self.config_dict['pin'] #int
        self.extended = self.config_dict['extended'] #int, servo angle
        self.retracted = self.config_dict['retracted'] #int, servo angle
        self.name = name #str
        self.servo = get_servo(self.config_dict['servo'], self.config_dict['servo_type']) #kit.servo
        self.target_name = self.config_dict['target_name']
        self.target_type = self.config_dict['target_type']
        
        switch_dict = {
            'pin':self.pin,
            'pullup_pulldown':self.config_dict['pullup_pulldown'],
        }

        self.switch = self.box.button_manager.new_button(self.name, switch_dict, self.box)
        
        #where should these defaults live so they dont take up unnecessary space? might also put pu_pd there
        self.retraction_timeout = self.config_dict['retraction_timeout'] if 'retraction_timeout' in self.config_dict.keys() else 2
        self.interpress_timeout = self.config_dict['interpress_timeout'] if 'interpress_timeout' in self.config_dict.keys() else 0.5
        
        self.setup_target()
        
        #threading        
        self.threads = ThreadPoolExecutor(max_workers = 6)
        self.futures = []
        
        #attributes for tracking during runtime
        self.total_presses = 0
        self.presses_reached = False
        self.monitoring = False
        self.stop_threads = False
        self.press_q = queue.Queue()
        
        
        self.timestamp_q = self.box.timestamp_q
        self.wiggle = 10
        
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
        
    
    def extend_lever(self):
        '''extend a lever and timestamp it'''
        
        ts = self.timestamp_q.new_timestamp(event_disciptor = f'{self.name} extended')
        
        extend_start = max(0, self.extended-self.wiggle)

        #first, extend past final value, then retract slightly to final value
        self.servo.angle = extend_start
        time.sleep(0.05)
        self.servo.angle = self.extended
        
        ts.submit()
        
        
    def retract_lever(self):
        '''extend a lever and timestamp it'''
        ts = self.timestamp_q.new_timestamp(event_disciptor = f'{self.name} extended')
        retract_start = max(180, self.retract + self.wiggle)

        #wait for the vole to get off the lever
        start = time.time()
        while not GPIO.input(self.pin) and time.time() - start < self.retraction_timeout:
            'hanging till lever not pressed'
            time.sleep(0.05)

        #retract further than expected, then extend to final position
        self.servo.angle = retract_start
        time.sleep(0.05)
        self.servo.angle = self.retracted
        
        ts.submit()
    
    
    def click_on(self):
        '''how will we implement this? will the lever have its own click? or will clicking be implemented elsewhere?'''
    
    
    def watch_lever_pin(self):
        while self.end_monitor == False:
            if self.switch.pressed:
                print(f'{self.name}pressed!')
                
                self.click_on()
                timer = self.box.timeout(self.retraction_timeout)
                while self.switch.pressed and timer.running:
                    '''waiting for vole to get off lever'''
                    time.sleep(0.025)
                self.click_off()
                self.lever_presses.put('pressed')
                time.sleep(self.inter_press_timeout)
            time.sleep(0.025)
        print(f'\n:::::: done watching a pin for {self.name}:::::\n')
    
    def wait_for_n_presses(self, presses = 1):
        'monitor lever and wait for n_presses before '
        #start new thread to track presses
            #self.monitoring = True
            
            #start thread to watch pin and note presses
                #while self.monitoring:
                    #if pressed and total < n presses:
                        #self.presses +=1
                        
                
        #if presses reached
            #self.presses_reached = True
    
    def reset_lever(self):
        self.presses_reached = False
        
class Button:
    
    def __init__(self, button_dict, name, box):

        #may not need this, but brings it into line with other inits
        self.box = box

        self.pin = button_dict['pin']
        self.name = name
        pullup_pulldown = button_dict['pullup_pulldown']

        if pullup_pulldown == 'pull_up':
            self.pressed_val = 0
            GPIO.setup(self.pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        elif pullup_pulldown == 'pull_down':
            self.pressed_val = 1
            GPIO.setup(self.pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        else:
            raise KeyError(f'Configuration file error when instantiating Button {self.name}, must be "pull_up" or "pull_down", but was passed {pullup_pulldown}')
         
        self.pressed = False
        
class ButtonManager:
    
    def __init__(self, box):
        
        self.box = box
        self.buttons = []
        self.running = True
        self.wp = threading.Thread(target = self.watch_buttons, daemon = True)
        self.wp.start()
        
    
    def watch_buttons(self):
        while self.running:
            for button in self.buttons:
                if GPIO.input(button.pin) == button.pressed_val:
                    button.pressed = True
                else:
                    button.pressed = False
            time.sleep(0.005)
            
    def new_button(self, name, button_dict, box = None):
        '''make a new button and add it to the button list'''
        if not box:
            box = self.box
        new_button_obj = Button(button_dict, name, box)
        self.buttons.append(new_button_obj)
        return new_button_obj
class Door:
    
    def __init__(self, name, door_config_dict, box):
        
        self.box = box 

        self.timestamp_q = self.box.timestamp_q

        self.config_dict = door_config_dict
        self.servo = get_servo(self.config_dict['servo'], self.config_dict['servo_type']) #kit.servo
        self.stop_speed = self.config_dict['stop']
        self.close_speed = self.config_dict['close']
        self.open_speed = self.config_dict['open']
        self.open_time = self.config_dict['open_time']
        self.close_timeout = self.config_dict['close_timeout']
        self.name = name

        #real time response attributes
        
        ss_button_dict = { 
            'pin':self.config_dict['state_switch'],
            'pullup_pulldown':'pull_up'
        }
        self.state_switch = self.box.button_manager.new_button(f'{self.name}_state_switch', ss_button_dict)
        self.overridden = False


        #override buttons
        oo_button_dict = { 
            'pin':self.config_dict['override_open_pin'],
            'pullup_pulldown':'pull_up'
        }
        self.override_open_button = self.box.button_manager.new_button(f'{self.name}_override_open', oo_button_dict, self.box)


        oc_button_dict = { 
            'pin':self.config_dict['override_open_pin'],
            'pullup_pulldown':'pull_up'
        }
        self.override_close_button  = self.box.button_manager.new_button(f'{self.name}_override_close', oc_button_dict, self.box)

        
        #start the override function
        self.override(self)
    
    def is_closed(self):
        return self.state_switch.pressed
    
    def is_open(self):
        return not self.state_switch.pressed
    

    def thread_it(func):
        '''simple decorator to pass function to our thread distributor via a queue. 
        these 4 lines took about 4 hours of googling and trial and error.
        the returned 'future' object has some useful features, such as its own task-done monitor. '''
        
        def pass_to_thread(self, *args, **kwargs):
            
            bound_args = inspect.signature(func).bind(self, *args, **kwargs)
            bound_args.apply_defaults()
            bound_args_dict = bound_args.arguments

            new_kwargs = {k:v for k, v in bound_args_dict.items() if k not in ('self')}
            print(f'submitting {func}')
            future = self.box.thread_executor.submit(func,self, **new_kwargs)
            self.box.worker_queue.put((future, func.__name__))

            if 'wait' in bound_args_dict.keys() and bound_args_dict['wait'] == True:
                name = func.__name__
                self.box.wait(future, name)
            return future
        return pass_to_thread
    
    
    @thread_it
    def open(self, wait = False):
        '''open this door'''
        '''ts_start = self.timestamp_q.new_timestamp(event_disciptor = oes.open_door_start, id = self.name)
        ts_finish = self.timestamp_q.new_timestamp(event_disciptor = oes.open_door_finish, id = self.name)'''

        self.servo.throttle = self.open_speed

        start_time = time.time()
        while time.time() < (start_time + self.open_time) and not self.overridden:
            time.sleep(0.05)
        
        self.servo.throttle = self.stop_speed

        if self.state_switch.pressed:
            print(f'{self.name} door failed to open!!!')
        else:
            print(f'{self.name} opened!')

        
    @thread_it
    def close(self, wait = True):
        '''open this door'''
        '''ts_start = self.timestamp_q.new_timestamp(event_disciptor = oes.open_door_start, id = self.name)
        ts_finish = self.timestamp_q.new_timestamp(event_disciptor = oes.open_door_finish, id = self.name)'''

        self.servo.throttle = self.close_speed

        start_time = time.time()
        #this is kind of messy, mixing attributes and functions
        while time.time() < (start_time + self.close_timeout) and not self.overridden and not self.state_switch.pressed:
            time.sleep(0.05)
        
        self.servo.throttle = self.stop_speed

        if not self.state_switch.pressed:
            print(f'{self.name} door failed to close!!!')
        else:
            print(f'{self.name} closed!')

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

    def __init__(self, name, dispenser_config_dict, box):
        '''make a dispenser'''
        self.box = box
        self.timestamp_q = self.box.timestamp_q
        self.config_dict = dispenser_config_dict
        self.servo_ID = self.config_dict['servo']
        self.servo = get_servo(self.config_dict['servo'], self.config_dict['servo_type']) #kit.servo
        self.stop_speed = self.config_dict['stop']
        self.dispense_speed = self.config_dict['dispense']
        self.open_time = self.config_dict['dispense_time']
        self.name = name


class Speaker:

    def __init__(self, name, speaker_dict, box):
        self.box = box
        self.pin = speaker_dict['pin']
        self.tone_dict = speaker_dict['tone_dict']


def get_servo(ID, servo_type):
    '''take a servo positional ID on the adafruit board, and the servo type, and return a servo_kit obj'''

    if servo_type not in ('positional', 'continuous'):
        raise KeyError(f'servo type was passed as {servo_type}, must be either "positional" or "continuous"')

    if servo_type == 'positional':
        return SERVO_KIT.servo[ID]
    else:
        return SERVO_KIT.continuous_servo[ID] 

