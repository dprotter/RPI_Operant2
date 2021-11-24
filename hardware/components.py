import time
import RPi.GPIO as GPIO
import queue
from concurrent.futures import ThreadPoolExecutor
import threading


class Lever:
    
    def __init__(self, lever_config_dict, lever_default_dict, box):
        
        #merge default and config file dicts, with >>> precedence to >>> config file dict
        self.config_dict = lever_default_dict.update(lever_config_dict)
        
        self.box = box
        self.pin = self.config_dict['pin'] #int
        self.extended = self.config_dict['extended'] #int, servo angle
        self.retracted = self.config_dict['retracted'] #int, servo angle
        self.name = self.config_dict['name'] #str
        self.servo = self.config_dict['servo'] #kit.servo
        self.target_name = self.config_dict['target_name']
        self.target_type = self.config_dict['target_type']
        
        self.switch = self.box.button_manager.new_button(self.pin, self.config_dict['pullup_pulldown'], self.name)
        
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
    
    def __init__(self, pin, pullup_pulldown, name):
        self.pin = pin
        self.name = name
        
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
    
    def __init__(self):
        
        self.buttons = []
        self.wp = threading.Thread(target = self.watch_buttons, daemon = True)
        self.wp.start()
        self.running = True
    
    def watch_buttons(self):
        while self.running:
            for button in self.buttons:
                if GPIO.input(button.pin) == button.pressed_val:
                    button.pressed = True
                else:
                    button.pressed = False
            time.sleep(0.005)
            
    def new_button(self, pin, pu_pd, name):
        '''make a new button and add it to the button list'''
        self.buttons.append(Button(pin, pu_pd, name))
class Door():
    
    def __init__(self, door_config_dict, door_default_dict, box):
        
        self.timestamp_q = box.timestamp_q
        
        #merge default and config file dicts, with precedence to config file dict
        self.config_dict = door_default_dict.update(door_config_dict)
        self.servo = self.config_dict['servo']
        self.stop_speed = self.config_dict['stop']
        self.close_speed = self.config_dict['close']
        self.open_speed = self.config_dict['open']
        self.open_time = self.config_dict['open_time']
        self.name = self.config_dict['name']
        self.state_switch = self.config_dict['state_switch']
        
        #override buttons
        self.override_open_button = box.button_manager.new_button(self.config_dict['override_open_pin'], 0, f'{self.name}_override_open')
        self.override_close_button = box.button_manager.new_button(self.config_dict['override_close_pin'], 0, f'{self.name}_override_close')

        
        #start the override function
        self.override(self)
    
    def is_closed(self):
        return GPIO.input(self.state_switch) == 0
    
    def is_open(self):
        return GPIO.input(self.state_switch) == 1
    
    def thread_it(func, *args, **kwargs):
        '''simple decorator to pass function to our thread distributor via a queue. 
        these 4 lines took about 4 hours of googling and trial and error.
        the returned 'future' object has some useful features, such as its own task-done monitor. '''
        def pass_to_thread(self, *args, **kwargs):
            future = self.box.thread_executor.submit(func, *args, **kwargs)
            self.box.worker_queue.put((future, func.__name__, self.round))
            return future
        return pass_to_thread
    
    
    @thread_it
    def override(self):
        while not self.box.shutdown:
            if self.override_open_button.pressed:
                self.servo.throttle = self.open_speed
                while self.override_open_button.pressed:
                    time.sleep(0.05)
                self.servo.throttle = self.stop_speed
                
                
            if self.override_close_button.pressed:
                self.servo.throttle = self.close_speed
                while self.override_close_button.pressed:
                    time.sleep(0.05)
                self.servo.throttle = self.stop_speed
            time.sleep(0.1)


class Dispenser:

    def __init__(self, dispenser_config_dict, dispenser_default_dict, box):
        '''make a dispenser'''
        self.timestamp_q = box.timestamp_q
        self.config_dict = dispenser_default_dict.update(dispenser_config_dict)
        self.servo = self.config_dict['servo']
        self.stop_speed = self.config_dict['stop']
        self.dispense_speed = self.config_dict['dispense']
        self.open_time = self.config_dict['dispense_time']
        self.name = self.config_dict['name']

        