import time

import queue

from hardware.event_strings import OperantEventStrings as oes
import inspect






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
        
SERVO_KIT = Servo_Sim() 
        


class Lever:
    
    def __init__(self, name, lever_config_dict, box):
        
        
        self.config_dict = lever_config_dict
        
        self.box = box
        self.pin = self.config_dict['pin'] #int
        self.extended = self.config_dict['extended'] #int, servo angle
        self.retracted = self.config_dict['retracted'] #int, servo angle
        self.name = name #str
        
        self.servo = self.servo = SERVO_KIT.new_fake_servo(self.config_dict) #kit.servo
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
        
        
        #attributes for tracking during runtime
        self.total_presses = 0
        self.presses_reached = False
        self.monitoring = False
        self.stop_threads = False
        self.lever_press_queue = queue.Queue()
        self.lever_presses = 0
        
        
        self.timestamp_q = self.box.timestamp_q
        self.wiggle = 10
    
    def simulate_pressed(self):
        self.switch.pressed = True
    
    def simulate_unpressed(self):
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
        
        ts = self.box.timestamp_manager.new_timestamp(description = f'{self.name} lever extended')
        
        extend_start = max(0, self.extended-self.wiggle)

        #first, extend past final value, then retract slightly to final value
        self.servo.angle = extend_start
        time.sleep(0.05)
        self.servo.angle = self.extended
        print(f'extending {self.name}')
        
        ts.submit()
        
        
    def retract(self):
        '''extend a lever and timestamp it'''
        ts = self.box.timestamp_manager.new_timestamp(description = f'{self.name} lever retracted')
        retract_start = max(180, self.retracted + self.wiggle)

        #wait for the vole to get off the lever
        timeout = self.box.timing.new_timeout(self.retraction_timeout)
        while not GPIO.input(self.pin) and timeout.active():
            'hanging till lever not pressed'

        #retract further than expected, then extend to final position
        self.servo.angle = retract_start
        time.sleep(0.05)
        self.servo.angle = self.retracted
        print(f'retracting {self.name}')
        
        ts.submit()
    
    @thread_it
    def watch_lever_pin(self):
        while self.monitoring:
            if self.switch.pressed:
                self.total_presses +=1
                self.box.timestamp_manager.submit_new_timestamp(f'{self.name} lever pressed',modifiers = {'press_n':self.total_presses})
                self.box.speaker.click_on()
                timeout = self.box.timing.new_timeout(self.retraction_timeout)
                while self.switch.pressed and timeout.is_active():
                    '''waiting for vole to get off lever. nothing necessary within loop'''
                self.box.speaker.click_off()
                self.lever_press_queue.put(('pressed'))
                
                #wait to loop until inter-press interval is passed
                ipt_timeout = self.box.timing.new_timeout(self.interpress_timeout)
                ipt_timeout.wait()
            time.sleep(0.025)
        '''print(f'\n:::::: done watching a pin for {self.name}:::::\n')'''
    
    @thread_it
    def wait_for_n_presses(self, presses = 1, reset_with_new_phase = True):
        'monitor lever and wait for n_presses before '
        self.monitoring = True
        self.watch_lever_pin()
        if reset_with_new_phase:
            print('reset with new phase')
            #get the current phase object
            phase = self.box.timing.current_phase

            #query to see if phase is still active.
            #note: if you simply used 'while self.box.current_phase.active() you could miss shutdown, i think
            while phase.active():
                if not self.lever_press_queue.empty():
                    print(f'{self.name} was pressed')
                    while not self.lever_press_queue.empty():
                        _ = self.lever_press_queue.get()
                        self.lever_presses += 1
                        if self.lever_presses >= presses:
                            self.presses_reached = True
                            self.monitoring = False
                            return True
            print('presses not reached')
        
        else:
            while self.monitoring:
                if not self.lever_press_queue.empty():
                    while not self.lever_press_queue.empty():
                        _ = self.lever_press_queue.get()
                        self.lever_presses += 1
                        if self.lever_presses >= presses:
                            self.presses_reached = True
                            self.monitoring = False
                            return True
                time.sleep(0.05)
                
        self.monitoring = False

    def reset_lever(self):
        self.monitoring = False
        self.presses_reached = False
        
class Button:
    
    def __init__(self, button_dict, name, box):

        #may not need this, but brings it into line with other inits
        self.box = box

        self.pin = button_dict['pin']
        self.name = name
        pullup_pulldown = button_dict['pullup_pulldown']

        if pullup_pulldown == 'pullup':
            self.pressed_val = 0
            
        elif pullup_pulldown == 'pulldown':
            self.pressed_val = 1
            
        else:
            raise KeyError(f'Configuration file error when instantiating Button {self.name}, must be "pullup" or "pulldown", but was passed {pullup_pulldown}')
         
        self.pressed = False
        
class ButtonManager:
    
    def __init__(self, box):
        
        self.box = box
        self.buttons = []
        self.running = True
        '''self.wp = threading.Thread(target = self.watch_buttons, daemon = True)
        self.wp.start()'''
        self.watch_buttons()

    @thread_it
    def watch_buttons(self):
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
    
    def __init__(self, name, door_config_dict, box):
        
        self.box = box 

        self.config_dict = door_config_dict
        
        self.servo = SERVO_KIT.new_fake_servo(self.config_dict) #kit.servo
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
        self.state_switch.pressed = True
        
    def simulate_closed(self):
        '''use to simulate the door entering the closed state'''
        self.state_switch.pressed = False
    
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
        self.config_dict = dispenser_config_dict
        self.servo_ID = self.config_dict['servo']
        self.servo = self.servo = SERVO_KIT.new_fake_servo(self.config_dict) #kit.servo
        self.stop_speed = self.config_dict['stop']
        self.dispense_speed = self.config_dict['dispense']
        self.dispense_timeout = self.config_dict['dispense_timeout']
        self.name = name
        self.pellet_state = False

        sensor_dict = { 
            'pin':self.config_dict['sensor_pin'],
            'pullup_pulldown':self.config_dict['pullup_pulldown']
        }
        
        self.sensor = self.box.button_manager.new_button(f'{self.name}_sensor', sensor_dict)
        self.overridden = False



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
            self.servo.throttle = self.dispense_speed
            read = 0
            timeout = self.box.timing.new_timeout(timeout = self.dispense_timeout)
            while timeout.active():
                if self.sensor.pressed:
                    read+=1
                if read > 2:
                    '''timestamp put "pellet dispensed"'''
                    self.servo.throttle = self.stop_speed
                    self.pellet_state = True
                    pellet_latency = self.timestamp_q.new_latency(description = 'pellet_retrieved')
                    self.monitor_pellet(pellet_latency)
                    return None
            
    
    @thread_it
    def monitor_pellet(self, pellet_latency):
        '''track when a pellet is retrieved'''
        while not self.box.finished():
            if not self.sensor_pressed:
                pellet_latency.submit()
                
                
                

class Speaker:
    class FakeSpeaker:
        def set_PWM_frequency(pin, hz):
            print(f'speaker set to {hz} hz')
        def set_PWM_dutycycle(pin, dc):
            print(f'speaker set to {dc} duty cycle')
            
    def __init__(self, name, speaker_dict, box):
        self.box = box
        self.name = name
        self.pin = speaker_dict['pin']
        self.tone_dict = self.box.software_config['speaker_tones']
        self.pi = self.FakeSpeaker()
        self.click_on_train = [(tone_values['hz'], tone_values['length']) for _, tone_values in self.tone_dict['click_on'].items()]
        self.click_off_train = [(tone_values['hz'], tone_values['length']) for _, tone_values in self.tone_dict['click_off'].items()]
    @thread_it
    def play_tone(self, tone_name):
        '''use pigpio to play a tone, called by name from the dict imported from software config file'''
        if not tone_name in self.tone_dict.keys():
            raise KeyError(f'tone: {tone_name} was not defined in the softare dictionary')
        else:
            hz = self.tone_dict[tone_name]['hz']
            length = self.tone_dict[tone_name]['length']

            self.pi.set_PWM_frequency(self.pin, int(hz))
            self.pi.set_PWM_dutycycle(self.pin, 255/2)
            time.sleep(length)
            self.pi.set_PWM_dutycycle(self.pin, 0)

    @thread_it
    def click_on(self):
        '''play through a designated train of tones.'''
        for hz, length in self.click_on_train:
            self.pi.set_PWM_frequency(self.pin, int(hz))
            self.pi.set_PWM_dutycycle(self.pin, 255/2)
            time.sleep(length)
        
        self.pi.set_PWM_dutycycle(self.pin, 0)

    @thread_it
    def click_off(self):
        '''play through a designated train of tones.'''
        for hz, length in self.click_off_train:
            self.pi.set_PWM_frequency(self.pin, int(hz))
            self.pi.set_PWM_dutycycle(self.pin, 255/2)
            time.sleep(length)
        
        self.pi.set_PWM_dutycycle(self.pin, 0)

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
        
        
