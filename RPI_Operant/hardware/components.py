
import time
import sys
from concurrent.futures import ThreadPoolExecutor
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    print('RPi.GPIO not found')
    from .Fake_GPIO import Fake_GPIO
    GPIO = Fake_GPIO()
import queue
import sys
from .event_strings import OperantEventStrings as oes
import inspect
import copy
import serial as ser

try: 
    from adafruit_servokit import ServoKit
    SERVO_KIT = ServoKit(channels=16)
except Exception as e:
    print(e)
    print('servokit not found')
    SERVO_KIT = None



def get_servo(ID, servo_type):
    '''take a servo positional ID on the adafruit board, and the servo type, and return a servo_kit obj'''
    ACCEPTABLE_TYPES = ('positional', 'continuous', 'output')
    if servo_type not in ACCEPTABLE_TYPES:
        raise KeyError(f'servo type was passed as {servo_type}, must be in:\n{ACCEPTABLE_TYPES}')

    if servo_type == 'positional':
        return SERVO_KIT.servo[ID]
    elif servo_type == 'continuous':
        return SERVO_KIT.continuous_servo[ID] 
    else:
        return SERVO_KIT.channel[ID]



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
        self.control_loc = False
        self.control_queue = queue.Queue()
        self.angular_position = None
        
        if simulated:
            self.servo = SERVO_SIM.new_fake_servo(self.config_dict)
        else:
            self.servo = get_servo(self.config_dict['servo'], self.config_dict['servo_type'])
        self.target_name = self.config_dict['target_name']
        self.target_type = self.config_dict['target_type']
        
        self.attatch_speaker()
        
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
        self.pause_monitoring = False
        self.stop_threads = False
        self.lever_press_queue = queue.Queue()
        self.lever_presses = 0
        
        self.wiggle = 5
        self.step_size = 10
    
    @thread_it
    def _raise_test_error(self, wait = True):
        '''use this to test errors are recorded properly'''
        raise Exception('this error is a test for logging.')
    
    @thread_it
    def attatch_speaker(self):
        success = False 
        timeout = self.box.timing.new_timeout(length = 2)
        while not success and timeout.active():
            if 'speaker_name' in self.config_dict.keys():
                self.speaker = self.box.speakers.get_component(self.config_dict['speaker_name'])
                success = True
            else:
                try: 
                    self.speaker = self.box.speaker
                    success = True
                except AttributeError as e: 
                    pass
    
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

    @thread_it
    def _execute_move(self, wait = False):
        if not self.control_queue.empty():

            self.control_loc = True
            while self.control_loc and not self.box.finished():
                
                #get the destination and all incoming timestamp objects
                destination, init_ts, finish_ts, interrupt_ts  = self.control_queue.get()
                #print(f'lever {self.name} moving to destination {destination}')
                if not self.angular_position:
                    self.angular_position = abs(self.retracted - self.extended) / 2
                    
                steps = int((self.angular_position - destination)/self.step_size)
                
                #where is the lever
                loc = self.angular_position
                interrupt = False
                
                #determine step direction
                if steps<0:
                    steps = abs(steps)
                    step = self.step_size
                else:
                    step = -self.step_size
                
                #submit start of move timestamp
                init_ts.submit()
                
                for _ in range(steps):
                    #step slowly
                    loc+=step
                    try:
                        self.servo.angle = loc
                    except:
                        print(f'{self.name} tried moving past allowable range. target:{loc}')
                    self.angular_position = loc
                    
                    #exit this loop if a new command is found
                    if not self.control_queue.empty():
                        interrupt_ts.submit()
                        interrupt = True
                        print('move interrupted!!!')
                        break
                    time.sleep(0.02)
                
                if not interrupt:
                    self.servo.angle = destination
                    self.angular_position = destination
                    self.control_loc = False
                    
            finish_ts.submit()
            
            if destination == self.extended:
                self.is_extended = True
            else:
                self.is_extended = False
            
            time.sleep(0.25)
            self.disable()
                
  
    def extend(self, wait = False):
        '''extend a lever and timestamp it
        returns a latency object that may be used to get the latency from lever-out to a second event'''
        destination = self.extended
        start_ts = self.box.timestamp_manager.new_timestamp(description = oes.start_lever_extend + self.name, modifiers = {'ID':self.name}, 
                                                print_to_screen = False)
        
        finish_ts = self.box.timestamp_manager.new_timestamp(description = oes.lever_extended+self.name, 
                                                        modifiers = {'ID':self.name})
        
        interrupt_ts = self.box.timestamp_manager.new_timestamp(description = oes.extend_interrupt+self.name, 
                                                        modifiers = {'ID':self.name})
        self.control_queue.put((destination, start_ts, finish_ts, interrupt_ts))
        self._execute_move(wait = wait)
            
        return self.box.timestamp_manager.new_latency(event_1 = oes.lever_extended+self.name, 
                                                        modifiers = {'ID':self.name})
    
    def retract(self, wait = False):
        '''retract a lever and timestamp it
        returns a latency object that may be used to get the latency from lever-out to a second event'''
        destination = self.retracted
        start_ts = self.box.timestamp_manager.new_timestamp(description = oes.start_lever_retract + self.name, modifiers = {'ID':self.name}, 
                                                print_to_screen = False)
        
        finish_ts = self.box.timestamp_manager.new_timestamp(description = oes.lever_retracted+self.name, 
                                                        modifiers = {'ID':self.name})
        
        interrupt_ts = self.box.timestamp_manager.new_timestamp(description = oes.retract_interrupt+self.name, 
                                                        modifiers = {'ID':self.name})
        self.control_queue.put((destination,start_ts, finish_ts, interrupt_ts))
        self._execute_move(wait = wait) 
        return self.box.timestamp_manager.new_latency(event_1 = oes.lever_retracted+self.name, 
                                                        modifiers = {'ID':self.name})

    def disable(self):
        self.servo._pwm_out.duty_cycle = 0
        

    @thread_it
    def watch_lever_pin(self):
        self.monitoring = True
        
        while self.monitoring:
            if not self.pause_monitoring:
                if self.switch.pressed:
                    self.total_presses +=1
                    self.lever_press_queue.put(('pressed'))
                    if self.box.get_software_setting('checks', 
                                                    'click_on',
                                                    default = True): 
                        self.speaker.click_on()
                    timeout = self.box.timing.new_timeout(self.retraction_timeout)
                    while self.switch.pressed and timeout.active() and self.monitoring:
                        '''waiting for vole to get off lever. nothing necessary within loop'''
                    
                    if self.box.get_software_setting('checks', 
                                                    'click_off',
                                                    default = False): 
                        self.speaker.click_off()
                    
                    
                    #wait to loop until inter-press interval is passed
                    ipt_timeout = self.box.timing.new_timeout(self.interpress_timeout)
                    ipt_timeout.wait()
            time.sleep(0.015)
        #iprint(f'\n:::::: done watching a pin for {self.name}:::::\n')
    
    
    @thread_it
    def wait_for_n_presses(self, n = 1, reset_with_new_phase = False, 
                           latency_obj = None, 
                           reset_with_new_round = True,
                           on_press_events = None,inter_press_retraction = False):
        'monitor lever and wait for n_presses before'
        if self.presses_reached:
            print('trying to launch wait_for_n_presses, but presses already reached')
            while self.presses_reached and not self.box.finished():
                '''wait for lever to reset'''
            print('lever successfully reset, launching wait for n presses')
        if latency_obj:
            latency_obj.add_modifier(key = 'presses_required', value = n)
        self.watch_lever_pin()
        if reset_with_new_phase:
            print('reset with new phase')
            #get the current phase object
            phase = self.box.timing.current_phase

            #query to see if phase is still active.
            #note: if you simply used 'while self.box.current_phase.active() you could miss shutdown, i think
            self.monitor_lever(n, latency_obj, on_press_events=on_press_events, inter_press_retraction=inter_press_retraction)
            while phase.active() and not self.box.finished():
                '''wait'''

            self.reset_lever()
            
        #reset with new rounds waits to exit until the round has changed
        elif reset_with_new_round:
            r = self.box.timing.round
            self.monitor_lever(n, latency_obj, on_press_events=on_press_events, inter_press_retraction=inter_press_retraction)
            while r == self.box.timing.round and not self.box.finished():
                '''wait'''
            self.reset_lever()
            print('resetting')
            
        else:
            self.monitor_lever(n, latency_obj, on_press_events=on_press_events, inter_press_retraction=inter_press_retraction)
            while self.monitoring and not self.box.finished():
                '''wait'''
        
        self.monitoring = False
    @thread_it
    def inter_press_retraction_func(self):
        start = time.time()
        
        self.pause_monitoring = True
        self.retract()
        
        self.box.timing.new_timeout(length = self.config_dict['inter_press_retraction_interval']).wait()
        self.extend()
        self.pause_monitoring = False
        
    @thread_it
    def monitor_lever(self, n, latency_obj, on_press_events = None, inter_press_retraction = False):
        if latency_obj:
            latency_obj.event_2 = oes.lever_pressed+self.name
            latency_obj.reformat_event_descriptor()
        while self.monitoring:
            if not self.lever_press_queue.empty():
                        
                        while not self.lever_press_queue.empty() and self.monitoring:
                            _ = self.lever_press_queue.get()
                            self.lever_presses += 1
                            print(f'\n{self.name} was pressed (press {self.lever_presses} of {n} required)\n')
                            if inter_press_retraction and self.lever_presses < n:
                                self.inter_press_retraction_func()

                            #if there are on-press events, run them. they cannot take arguments at this time.
                            if on_press_events:
                                for event in on_press_events:
                                    event()
                                    
                            if latency_obj:
                                self.box.timestamp_manager.create_and_submit_new_timestamp(oes.lever_pressed+self.name, 
                                                                                            modifiers = {'total_presses':self.total_presses, 'ID':self.name})
                                local_latency = copy.copy(latency_obj)
                                local_latency.add_modifier(key = 'n_presses', value = self.lever_presses)
                                local_latency.submit()
                                
                            else:
                                self.box.timestamp_manager.create_and_submit_new_timestamp(oes.lever_pressed+self.name, 
                                                                                            modifiers = {'total_presses':self.total_presses, 'ID':self.name})
                            
                            if self.lever_presses >= n:
                                if latency_obj:
                                    local_latency = copy.copy(latency_obj)
                                    local_latency.event_descriptor = oes.presses_reached+self.name
                                    local_latency.add_modifier(key = 'n_presses', value = self.lever_presses)
                                    local_latency.submit()
                                else:
                                    self.box.timestamp_manager.create_and_submit_new_timestamp(oes.presses_reached+self.name, 
                                                                                                modifiers ={'n_press':self.lever_presses, 'ID':self.name})
                                self.presses_reached = True
                                self.monitoring = False
                            while not self.lever_press_queue.empty():
                                _ = self.lever_press_queue.get()
            time.sleep(0.005)
        
    def reset_lever(self):

        while self.is_extended:
            '''waiting for lever to be retracted before resetting'''
        self.monitoring = False
        self.pause_monitoring = False
        self.presses_reached = False
        self.lever_presses = 0


class NosePoke:
    
    def __init__(self, name, poke_config_dict, box, simulated = False):
        
        
        self.config_dict = poke_config_dict
        
        self.box = box
        self.pin = self.config_dict['pin'] #int

        self.name = name #str
        self.is_active = False #True = extended


        
        self.attatch_speaker()
        
        switch_dict = {
            'pin':self.pin,
            'pullup_pulldown':self.config_dict['pullup_pulldown'],
        }

        self.switch = self.box.button_manager.new_button(self.name, switch_dict, self.box)
        
        #where should these defaults live so they dont take up unnecessary space? might also put pu_pd there
        self.interpoke_timeout = self.config_dict['interpoke_timeout'] if 'interpoke_timeout' in self.config_dict.keys() else 0.25
        
        
        #attributes for tracking during runtime
        self.total_pokes = 0
        self.pokes_reached = False
        self.monitoring = False
        self.pause_monitoring = False
        self.stop_threads = False
        self.poke_queue = queue.Queue()
        self.pokes = 0
        if 'LED' in self.config_dict:
            self.LED = Output(name = f"{self.name}_port_LED",
                              output_config_dict = self.config_dict['LED'],
                              box = self.box,
                              simulated = simulated)
        self.current_latency_obj = None
        self.current_target_pokes = None
        self.current_on_poke_events = None

    
    @thread_it
    def _raise_test_error(self, wait = True):
        '''use this to test errors are recorded properly'''
        raise Exception('this error is a test for logging.')
    
    @thread_it
    def attatch_speaker(self):
        success = False 
        timeout = self.box.timing.new_timeout(length = 2)
        while not success and timeout.active():
            if 'speaker_name' in self.config_dict.keys():
                self.speaker = self.box.speakers.get_component(self.config_dict['speaker_name'])
                success = True
            else:
                try: 
                    self.speaker = self.box.speaker
                    success = True
                except AttributeError as e: 
                    pass
    
    def simulate_nose_poke(self):
        self.simulate_pressed()
        time.sleep(0.1)
        self.simulate_unpressed()
        
        
    def simulate_pressed(self):
        print('simulating pressed')
        self.switch.pressed = True
    
    def simulate_unpressed(self):
        print('simulating unpressed')
        self.switch.pressed = False
        

    def activate_LED(self, percent_brightness = 100, wait = False):
        '''activates a ports LED and timestamp it
        returns a latency object that may be used to get the latency from lever-out to a second event'''
        
       
        try:
            self.LED.activate
        except:
            print(f'{self.name} does not have an attached LED, but tried to activate one')
        else:
            self.LED.activate(percent_brightness)
        self.box.timestamp_manager.create_and_submit_new_timestamp(f'{self.name}_port_LED_active')
        return self.box.timestamp_manager.new_latency(event_1 = oes.nose_poke_active+self.name, 
                                                      modifiers = {'ID':self.name})
        
    
    def deactivate_LED(self, wait = False):
        '''inactivate a port and timestamp it
        returns a latency object that may be used to get the latency from lever-out to a second event'''
        try:
            self.LED
        except:
            print(f'{self.name} does not have an attached LED, but tried to deactivate one')
        else:
            self.LED.deactivate()
        self.box.timestamp_manager.create_and_submit_new_timestamp(f'{self.name}_port_LED_deactivate')
        return self.box.timestamp_manager.new_latency(event_1 = oes.nose_poke_inactive+self.name, 
                                                        modifiers = {'ID':self.name})

    
    @thread_it
    def wait_for_n_pokes(self, n = 1, reset_with_new_phase = False, 
                           latency_obj = None, 
                           reset_with_new_round = True,
                           on_poke_events = None, inter_poke_inactivation = False, end_monitoring_on_completion = True):
        'monitor lever and wait for n_presses before'
        if self.pokes_reached:
            print('trying to launch wait_for_n_pokes, but pokes already reached')
            while self.pokes_reached and not self.box.finished():
                '''wait for port to reset'''
            print('port successfully reset, launching wait for n pokes')
        if latency_obj:
            latency_obj.add_modifier(key = 'pokes_required', value = n)
        
        
        self._watch_port()
        if reset_with_new_phase:
            print('reset with new phase')
            #get the current phase object
            phase = self.box.timing.current_phase

            #query to see if phase is still active.
            #note: if you simply used 'while self.box.current_phase.active() you could miss shutdown, i think
            self._monitor_port_for_n_pokes(n, latency_obj, on_press_events=on_poke_events, inter_poke_inactivation=inter_poke_inactivation)
            while phase.active() and not self.box.finished():
                '''wait'''

            self.reset_port()
            
        #reset with new rounds waits to exit until the round has changed
        elif reset_with_new_round:
            r = self.box.timing.round
            self._monitor_port_for_n_pokes(n, latency_obj, on_poke_events=on_poke_events, inter_poke_inactivation=inter_poke_inactivation)
            while r == self.box.timing.round and not self.box.finished():
                '''wait'''
            self.reset_port()
            print('resetting')
            
        else:
            self._monitor_port_for_n_pokes(n, latency_obj, on_poke_events=on_poke_events, inter_poke_inactivation=inter_poke_inactivation)
            while self.monitoring and not self.box.finished():
                '''wait'''
        
        if end_monitoring_on_completion:
            self.monitoring = False
    
    @thread_it
    def inter_poke_inactivation_func(self):
        
        self.pause_monitoring = True
        self.deactivate_LED()
        
        self.box.timing.new_timeout(length = self.config_dict['inter_poke_inactiation_interval']).wait()
        self.activate_LED()
        self.pause_monitoring = False
        
    @thread_it
    def _monitor_port_for_n_pokes(self, n, latency_obj, on_poke_events = None, inter_poke_inactivation = False):
        if latency_obj:
            latency_obj.event_2 = oes.poke+self.name
            latency_obj.reformat_event_descriptor()
        while self.monitoring:
            if not self.poke_queue.empty():
                        
                        while not self.poke_queue.empty() and self.monitoring:
                            _ = self.poke_queue.get()
                            self.pokes += 1
                            print(f'\n{self.name} was poked (poke {self.pokes} of {n} required)\n')
                            if inter_poke_inactivation and self.pokes < n:
                                self.inter_poke_inactivation_func()

                            #if there are on-press events, run them. they cannot take arguments at this time.
                            if on_poke_events:
                                for event in on_poke_events:
                                    event()
                                    
                            if latency_obj:
                                self.box.timestamp_manager.create_and_submit_new_timestamp(oes.poke+self.name, 
                                                                                            modifiers = {'total_pokes':self.total_pokes, 'ID':self.name})
                                local_latency = copy.copy(latency_obj)
                                local_latency.add_modifier(key = 'n_pokes', value = self.pokes)
                                local_latency.submit()
                                
                            else:
                                self.box.timestamp_manager.create_and_submit_new_timestamp(oes.poke+self.name, 
                                                                                            modifiers = {'total_pokes':self.total_pokes, 'ID':self.name})
                            
                            if self.pokes >= n:
                                if latency_obj:
                                    local_latency = copy.copy(latency_obj)
                                    local_latency.event_descriptor = oes.pokes_reached+self.name
                                    local_latency.add_modifier(key = 'n_pokes', value = self.pokes)
                                    local_latency.submit()
                                else:
                                    self.box.timestamp_manager.create_and_submit_new_timestamp(oes.pokes_reached+self.name, 
                                                                                                modifiers ={'n_pokes':self.pokes, 'ID':self.name})
                                self.pokes_reached = True
                                self.monitoring = False
                            while not self.poke_queue.empty():
                                _ = self.poke_queue.get()
            time.sleep(0.005)
    
    @thread_it
    def set_poke_target(self, n = 1, reset_with_new_phase = False, 
                           latency_object = None, 
                           reset_with_new_round = False,
                           on_poke_events = None):
        'monitor lever and wait for n_presses before'
        self.is_active = True
        if self.pokes_reached:
            print('trying to launch wait_for_n_pokes, but pokes already reached')
            while self.pokes_reached and not self.box.finished():
                '''wait for port to reset'''
            print('port successfully reset, launching wait for n pokes')
        if latency_object:
            latency_object.add_modifier(key = 'pokes_required', value = n)
            self.current_latency_obj = latency_object
            
        if on_poke_events:
            self.current_on_poke_events = on_poke_events
        
        self.current_target_pokes = n
        
        if reset_with_new_phase:
            #get the current phase object
            phase = self.box.timing.current_phase

            #query to see if phase is still active.
            #note: if you simply used 'while self.box.current_phase.active() you could miss shutdown, i think
            
            while phase.active() and not self.box.finished():
                '''wait'''

            self.reset_poke_count()
            
        #reset with new rounds waits to exit until the round has changed
        elif reset_with_new_round:
            r = self.box.timing.round
            while r == self.box.timing.round and not self.box.finished():
                '''wait'''
            self.reset_poke_count()

            
        else:
            while self.current_target_pokes > 0 and not self.pokes_reached and not self.box.finished():
                '''wait'''
        self.is_active = False
    
    @thread_it
    def begin_monitoring(self):
        '''activating monitoring'''
        self._watch_port()
        time.sleep(0.25)
        while self.monitoring and not self.box.finished():
            
            
            if not self.poke_queue.empty():
                _ = self.poke_queue.get()
                self.pokes += 1
                if self.current_latency_obj:
                    #not ideal to keep reformating this event, but not costly
                    self.current_latency_obj.event_2 = oes.poke+self.name
                    self.current_latency_obj.reformat_event_descriptor()
                    
                    self.box.timestamp_manager.create_and_submit_new_timestamp(oes.poke+self.name, 
                                                                                modifiers = {'total_pokes':self.total_pokes, 'ID':self.name})
                    #make a local latency object that is a copy for this particular nose poke. 
                    local_latency = copy.copy(self.current_latency_obj)
                    local_latency.add_modifier(key = 'n_pokes', value = self.pokes)
                    local_latency.submit()
                    
                else:
                    #if no latency object, just use a simply timestamp
                    self.box.timestamp_manager.create_and_submit_new_timestamp(oes.poke+self.name, 
                                                                          modifiers = {'total_pokes':self.total_pokes, 'ID':self.name})
                #check for current on_poke_events to run
                if self.current_on_poke_events:
                        for event in self.current_on_poke_events:
                            event()
                        
                #check if we have reached the threshold
                if self.current_target_pokes > 0 and self.pokes >= self.current_target_pokes:
                    print(f'{self.name} poked {self.pokes} of {self.current_target_pokes}')
                    if self.current_latency_obj:
                        #make a local latency object that is a copy for this particular nose poke. 
                        local_latency = copy.copy(self.current_latency_obj)
                        local_latency.event_descriptor = oes.pokes_reached+self.name
                        local_latency.add_modifier(key = 'n_pokes', value = self.pokes)
                        local_latency.submit()
                    else:
                        self.box.timestamp_manager.create_and_submit_new_timestamp(oes.pokes_reached+self.name, 
                                                                                    modifiers ={'n_pokes':self.pokes, 'ID':self.name})
                    self.pokes_reached = True
                    self.n_pokes_reached_reset()
        print('exiting monitoring')
    def wait_for_reset(self):
        if self.pokes_reached:
            timeout = self.box.timing.new_timeout(length = 2)
            while self.pokes_reached and timeout.active:
                ''''''
            if self.pokes_reached:
                print('uhoh! failed to reset pokes within 2 seconds')
            
    @thread_it
    def _watch_port(self):
        print(f'watching port {self.name}')
        run_click_off = False
        if not self.monitoring:
            self.monitoring = True
            
            while self.monitoring:
                if not self.pause_monitoring:
                    if self.switch.pressed:
                        
                        self.total_pokes +=1
                        self.poke_queue.put(('poked'))
                        if self.box.get_software_setting('checks', 
                                                        'click_on',
                                                        default = True) and self.is_active:
                             
                            self.speaker.click_on()
                            run_click_off = True
                        while self.switch.pressed and self.monitoring:
                            '''waiting for vole to get off lever. nothing necessary within loop'''
                        
                        if self.box.get_software_setting('checks', 
                                                        'click_off',
                                                        default = False) and self.is_active: 
                            if run_click_off:
                                self.speaker.click_off()
                                run_click_off = False
                        
                        
                        #wait to loop until inter-press interval is passed
                        ipt_timeout = self.box.timing.new_timeout(self.interpoke_timeout)
                        ipt_timeout.wait()
                time.sleep(0.015)
            print(f'\n:::::: done watching a pin for {self.name}:::::\n')
            
    def reset_poke_count(self):
        self.pokes_reached = False
        self.pokes = 0
        self.current_target_pokes = 0
        self.is_active = False
        
    def n_pokes_reached_reset(self):
        
        self.current_target_pokes = 0
        #fall back to simple timestamps outside of latencies and targets
        self.current_latency_obj = None
        self.current_on_poke_events = None 
        self.is_active = False
        
    def reset_port(self):

        self.monitoring = False
        self.pause_monitoring = False
        self.pokes_reached = False
        self.pokes = 0
        self.is_active = False

class Button:
    
    def __init__(self, button_dict, name, box, simulated = False):

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

    def simulate_pressed(self):
        self.pressed = True
    
    def simulate_unpressed(self):
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
            
    def new_button(self, name, button_dict, box = None, simulated = False):
        '''make a new button and add it to the button list'''
        if not box:
            print(self)
            new_button_obj = Button(button_dict, name, self.box)
        else:
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
        self.state_switch = self.box.button_manager.new_button(f'{self.name}_state_switch', 
                                                               ss_button_dict)
        self.overridden = False


        #override buttons
        oo_button_dict = { 
            'pin':self.config_dict['override_open_pin'],
            'pullup_pulldown':'pullup'
        }
        self.override_open_button = self.box.button_manager.new_button(f'{self.name}_override_open', 
                                                                        oo_button_dict, self.box)


        oc_button_dict = { 
            'pin':self.config_dict['override_close_pin'],
            'pullup_pulldown':'pullup'
        }
        self.override_close_button  = self.box.button_manager.new_button(f'{self.name}_override_close', 
                                                                        oc_button_dict, self.box)

        
        #start the override function
        self.override(self)
    
    def disable(self):
        self.servo._pwm_out.duty_cycle = 0
    
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
    

    def open(self, wait = False):
        '''open this door. 
        wait = boolean --> should the box wait to move on to the next line of code until this event is complete?
        
        returns latency object'''
        self._open(wait = wait)       
        return self.box.timestamp_manager.new_latency(event_1 = f'{self.name}_open', modifiers = {'ID':self.name})

            
    
    @thread_it
    def _open(self, wait):
        self.servo.throttle = self.open_speed
        
        self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.open_door_start+self.name, 
                                                                   modifiers = {'ID':self.name})
        if 'serial_send' in self.box.software_config['checks'].keys():
            if self.box.software_config['checks']['serial_send'][self.name]:
                self.box.serial_sender.send_data(f'{self.name} open start')
            
        start_time = time.time()
        while time.time() < (start_time + self.open_time) and not self.overridden:
            time.sleep(0.05)
        
        self.disable()

        if self.state_switch.pressed:
            print(f'{self.name} door failed to open!!!')
            self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.open_door_failure+self.name, 
                                                                        modifiers = {'ID':self.name})
        else:
            print(f'{self.name} opened!')
            self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.open_door_finish+self.name, 
                                                                        modifiers = {'ID':self.name})

    @thread_it
    def close(self, wait = True):
        '''open this door'''
        
        self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.close_door_start+self.name,
                                                                     modifiers = {'ID':self.name})
        if 'serial_send' in self.box.software_config['checks'].keys():
            if self.box.software_config['checks']['serial_send'][self.name]:
                self.box.serial_sender.send_data(f'{self.name} close start')
            
        self.servo.throttle = self.close_speed

        start_time = time.time()
        
        #keep trying to close
        while time.time() < (start_time + self.close_timeout) and not self.state_switch.pressed:
            #once the override has been triggered, keep trying to close. 
            if self.overridden:
                while time.time() < (start_time + self.close_timeout) and self.overridden:
                    time.sleep(0.05)
                time.sleep(0.75)
                self.servo.throttle = self.close_speed
            else:
                time.sleep(0.05)
                
            
            
        #self.servo.throttle = self.stop_speed
        self.disable()
        if self.state_switch.pressed:
            print(f'{self.name} closed!')
            self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.close_door_finish+self.name, 
                                                                        modifiers = {'ID':self.name})
            if 'serial_send' in self.box.software_config['checks'].keys():
                if self.box.software_config['checks']['serial_send'][self.name]:
                    self.box.serial_sender.send_data(f'{self.name} close finish')
            
        else:
            print(f'{self.name} door failed to close!!!')
            self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.close_door_failure+self.name, 
                                                                        modifiers = {'ID':self.name})

    @thread_it
    def override(self, wait = False):
        while not self.box.done:
            
            if self.override_open_button.pressed:
                
                self.servo.throttle = self.open_speed
                self.overridden = True
                #print(f'{self.name} overriden open -> speed to {self.servo.throttle} -> aiming for {self.open_speed}')
                while self.override_open_button.pressed:
                    time.sleep(0.01)
                #print(f'{self.name} overriden open over')
                self.disable()
                self.overridden = False
                
            if self.override_close_button.pressed:
                self.servo.throttle = self.close_speed
                self.overridden = True
                #print(f'{self.name} overriden close')
                while self.override_close_button.pressed:
                    time.sleep(0.01)
                #print(f'{self.name} overriden close over')
                self.disable()
                self.overridden = False

            time.sleep(0.025)

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

        sensor_dict = { 
            'pin':self.config_dict['sensor_pin'],
            'pullup_pulldown':self.config_dict['pullup_pulldown']
        }
        
        self.sensor = self.box.button_manager.new_button(f'{self.name}_sensor', sensor_dict)

    
    def pellet_state(self): 
        return self.sensor.pressed 

    def start_servo(self):
        self.servo.throttle = self.config_dict['dispense']

    def stop_servo(self):
        self.servo._pwm_out.duty_cycle = 0

    def sensor_blocked(self):
        return self.sensor.pushed

    def simulate_dispensed(self):
        '''used in scripts to simulate a pellet being dispensed'''
        self.sensor.pressed = True
    
    def simulate_pellet_retrieved(self):
        '''used in scripts to simulate a pellet being removed from the trough'''
        self.sensor.pressed = False
    
    @thread_it
    def dispense(self, on_retrieval_events = None):
        ''''''

        #check if pellet was retrieved or is still in trough
        if self.pellet_state():
            self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'{oes.pellet_not_retrieved}_{self.name}', modifiers = {'ID':self.name})
            self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'{oes.pellet_skip}_{self.name}', modifiers = {'ID':self.name})            
        
        else:
            self.start_servo()
            read = 0
            timeout = self.box.timing.new_timeout(length = self.config_dict['dispense_timeout'])
            while timeout.active():
                if self.pellet_state():
                    read+=1
                if read > 2:
                    '''timestamp put "pellet dispensed"'''
                    self.stop_servo()
                    self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'{oes.pellet_dispensed}_{self.name}', modifiers = {'ID':self.name})
                    pellet_latency = self.box.timestamp_manager.new_latency(description = oes.pellet_retrieved, 
                                                                            modifiers = {'ID':self.name})
                    self.monitor_pellet(pellet_latency, on_retrieval_events = on_retrieval_events)
                    return None
            
            self.stop_servo()
            timeout = self.box.timing.new_timeout(length = 1)
            while timeout.active():
                if self.pellet_state():
                    self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'{oes.pellet_dispensed}_{self.name}', modifiers = {'ID':self.name})
                    pellet_latency = self.box.timestamp_manager.new_latency(description = oes.pellet_retrieved, 
                                                                            modifiers = {'ID':self.name})
                    self.monitor_pellet(pellet_latency, on_retrieval_events = on_retrieval_events)
                    return None
                    
            if not self.pellet_state():
                self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'{oes.pellet_failure}_{self.name}', modifiers = {'ID':self.name})
                return None
    @thread_it
    def monitor_pellet(self, pellet_latency, on_retrieval_events = None):
        '''track when a pellet is retrieved'''
        local_latency = copy.copy(pellet_latency)
        
        # no pellet in trough
        if not self.pellet_state(): # no pellet in trough, no need to loop 
            return 

        # pellet is in trough, monitor for pellet retrieval
        while not self.box.finished(): 
            if not self.pellet_state(): # stops looping as soon as pellet is gone from trough
                local_latency.submit()
                if on_retrieval_events:
                    for event in on_retrieval_events:
                        event()
                return 
                
                

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

    def disable(self):
        self.servo._pwm_out.duty_cycle = 0
    
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
        return self.sensor.pressed

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
            self.box.timestamp_manager.create_and_submite_new_timestamp(description = oes.pellet_skip, 
                                                                        modifiers = {'ID':self.name})
            
        elif self.sensor_blocked():
            '''timestamp put "pellet sensor already blocked"'''
            '''wait????'''
            print('sensor blocked', self.sensor_blocked)
        else:
            
            read = 0
            timeout = self.box.timing.new_timeout(length = self.dispense_timeout)
            while timeout.active():
                self.next_position()
                timeout_2 = self.box.timing.new_timeout(length = 0.25)
                while timeout_2.active():
                    if self.sensor.pressed:
                        read+=1
                    if read > 2:
                        '''timestamp put "pellet dispensed"'''
                        self.disable()
                        self.pellet_state = True
                        self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.pellet_dispensed, 
                                                                                    modifiers = {'ID':self.name})
                        pellet_latency = self.box.timestamp_manager.new_latency(description = oes.pellet_retrieved, 
                                                                                    modifiers = {'ID':self.name})
                        self.monitor_pellet(pellet_latency)
                        return None
                    
                
                #step back to the 1/4 position in this slot
                self.small_step_backwards(n=1)
                timeout_3 = self.box.timing.new_timeout(length = 0.25)
                while timeout_3.active():
                    if self.sensor.pressed:
                        read+=1
                    if read > 2:
                        '''timestamp put "pellet dispensed"'''
                        self.disable()
                        self.pellet_state = True
                        self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.pellet_dispensed, 
                                                                                modifiers = {'ID':self.name})
                        pellet_latency = self.box.timestamp_manager.new_latency(description = oes.pellet_retrieved, 
                                                                                modifiers = {'ID':self.name})
                        self.monitor_pellet(pellet_latency)
                        return None
                
                
                #go to the 3/4 position within this slot
                self.small_step_forward(n=2)
                timeout_4 = self.box.timing.new_timeout(length = 0.25)
                while timeout_4.active():
                    if self.sensor.pressed:
                        read+=1
                    if read > 2:
                        '''timestamp put "pellet dispensed"'''
                        self.disable()
                        self.pellet_state = True
                        self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.pellet_dispensed, 
                                                                                    modifiers = {'ID':self.name})
                        pellet_latency = self.box.timestamp_manager.new_latency(description = oes.pellet_retrieved, 
                                                                                    modifiers = {'ID':self.name})
                        self.monitor_pellet(pellet_latency)
                        return None
                #here, if not luck, we will step to the next position
        self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.pellet_failure)
            
    def stop(self): 
        print(f'STOPPING {self.name}')
        self.disable()

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
            self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'{oes.pellet_dispensed}_{self.name}', 
                                                                        modifiers = {'ID':self.name})
            latency = self.box.timestamp_manager.new_latency(description = f'{oes.pellet_retrieved}_{self.name}', 
                                                                        modifiers = {'ID':self.name})
            self.pellet_state = True
            self.monitor_pellet(latency)
        else:
            if self.pellet_state:
                self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'{oes.pellet_not_retrieved}_{self.name}', 
                                                                            modifiers = {'ID':self.name})
                self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'{oes.pellet_skip}_{self.name}', 
                                                                            modifiers = {'ID':self.name})
            else:
            
                self.next_position()
                self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'{oes.pellet_dispensed}_{self.name}', 
                                                                            modifiers = {'ID':self.name})
                latency = self.box.timestamp_manager.new_latency(description = f'{oes.pellet_retrieved}_{self.name}', 
                                                                            modifiers = {'ID':self.name})
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
class Output:
    
    '''
    '''
    
    
    def __init__(self, name, output_config_dict, box, simulated = False):
        '''make an output'''
        self.box = box
        self.config_dict = output_config_dict
        self.active = False
        self.name = name
        
        if self.config_dict['type'] == 'GPIO':
            
            self.pin = self.config_dict['pin']
            
            GPIO.setup(self.pin, GPIO.OUT)
            self.output_on = self.set_active_GPIO
            self.output_off = self.set_inactive_GPIO
                

        elif self.config_dict['type'] == 'HAT':

            self.channel = SERVO_KIT._pca.channels[self.config_dict['channel']]
            self.output_on = self.set_active_HAT
            self.output_off = self.set_inactive_HAT
            
        else:
            raise Exception(f'incorrect output type passed: {self.config_dict["type"]}\n must be "HAT" or "GPIO"')
    
    ################################################
    ############## HAT ###############
    def set_active_HAT(self, percent):
        self.active = True
        self.channel.duty_cycle = self.hat_PWM_hex_from_percent(percent)
        
    def set_inactive_HAT(self):
        self.active = False
        self.channel.duty_cycle = 0
                
        
    ############## GPIO ###############    
    def set_active_GPIO(self, percent):
        self.box.pi.set_PWM_dutycycle(self.pin, self.GPIO_PWM_8bit_from_percent(percent))
        self.active = True
        
    def set_inactive_GPIO(self):
        self.box.pi.set_PWM_dutycycle(self.pin, 0)
        self.active = False
    ################################################    
         
        
    def activate(self, percent_duty_cycle = 100):
        '''when activating take a percent brightness from 1 to 100'''

        self.output_on(percent_duty_cycle)
        self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'output_activated', 
                                                                    modifiers = {'ID':self.name,'duty_cycle':percent_duty_cycle}, 
                                                                    print_to_screen = False)
    
    def hat_PWM_hex_from_percent(self, percent = 100, int_bit = 16, max_value = None):
        vals = {16:65535, 12: 4095, 8: 255}
        if max_value:
            max_value = max_value
        else:
            try:
                max_val = vals[int(int_bit)]
            except:
                print(f'expected a int_bit value of 8, 12, or 16, but received: {int_bit}. you may also pass a max_value for your PWM generator directly as max_value')
        integer = int(percent * max_val / 100)
        return integer
    
    def GPIO_PWM_8bit_from_percent(self, percent = 100):
        return int(255 * percent / 100)
         
    def deactivate(self):
        
        self.output_off()
        self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'output_deactivated', 
                                                                    modifiers = {'ID':self.name}, 
                                                                    print_to_screen = False)
    
    @thread_it
    def pulse_output(self, length = 1, pulse_string = None):
        '''pulse an output pin. relies on time.sleep, so not super accurate for short pulses.
        length = time in s to pulse (float, int)
        pulse_string = string to be timestamped in the output file'''
        timestamp_str = pulse_string if pulse_string else f'output_puslse_start_len_{length}'
        self.box.timestamp_manager.create_and_submit_new_timestamp(description = timestamp_str, 
                                                                   modifiers = {'ID':self.name})
        
        self.activate()
        time.sleep(length)
        self.deactivate()
    
    @thread_it
    def trigger(self, length = 0.1, pulse_string = None):
        if pulse_string:
            self.box.timestamp_manager.create_and_submit_new_timestamp(description = pulse_string, 
                                                                   modifiers = {'ID':self.name})
        else:
            self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'trigger', 
                                                                   modifiers = {'ID':self.name})
        self.switch_active()
        time.sleep(length)
        self.switch_inactive()
        return None
    
    def shutdown(self):
        if self.active:
            self.deactivate()
            print(f'deactivating {self.name}')
    
    def trigger_hold_high(self, pulse_string):
        if pulse_string:
            self.box.timestamp_manager.create_and_submit_new_timestamp(description = pulse_string, 
                                                                   modifiers = {'ID':self.name})
        else:
            self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'trigger', 
                                                                   modifiers = {'ID':self.name})
        self.switch_active()
        return self
    
    def prepare_pulse(self, length, pulse_string = None):
        'create a premade pulse object that can be passed to on-press-event lists'
        return lambda: self.pulse_output(length, pulse_string)  
   
    def prepare_trigger(self, length = 0, pulse_string = None):
        'create a premade trigger object that can be passed to on-press-event lists'
        if length == 0:
            return lambda: self.trigger_hold_high(pulse_string)
        return lambda: self.trigger(length, pulse_string)

    
    
class Laser: 

    def __init__(self, name, speaker_dict, box, simulated = False): 

        self.box = box 
        self.name = name 
        self.pin = speaker_dict['pin'] 
        if not simulated:
            
            ##################3here is where I need to come in and change how this output is handled###################333 
            self.gpio = GPIO 
            GPIO.setup(self.pin, GPIO.OUT) # Connecting to Pi ! 
        else: 
            print(f'Simulating {self.name} pi connection')
            self.gpio = self.SimulatedGPIO()
        self.on = False # current on/off state of the Laser
        self.patterns = self._setup_laser_patterns() # creates Cycle objects and sets as attributes for all the patterns defined in the yaml file so we can reference them by name. Also returns a list of all of the string names of the patterns to allow us to iterate thru all the patterns if desired.  

    class SimulatedGPIO: 
        def output(self, pin_num, zero_or_one):
            '''print(f'laser{self.name} set to {zero_or_one}')'''

    class Cycle: 
        def __init__(self, name, high_time, low_time, repeat, laser_object): 
            self.name = name 
            self.high_time = high_time # seconds Laser is set to HIGH
            self.low_time = low_time # seconds Laser is set to LOW
            self.repeat = repeat # number of times we repeat this HIGH/LOW cycle 
            self.laser_object = laser_object
            self.box = laser_object.box

            self.total_time = (high_time + low_time)*repeat

        @thread_it
        def trigger(self): 
            '''turn the laser on/off according to the cycle attributes'''
            for i in range(self.repeat): 
                latency_obj = self.laser_object.turn_on() # submits a normal timestampt and creates the latency timestamp for submition at a later time
                time.sleep(self.high_time)
                self.laser_object.turn_off(latency_obj = latency_obj) # submits a normal timestamp and submits the latency timestamp 
                time.sleep(self.low_time)
            
            return 
        
    def _setup_laser_patterns(self): 
        ''' Instantiates Cycle Objects and sets them as attributes for the Laser so we can easily turn the laser on/off to match a certain pattern/cycle '''
        pattern_list = [] # empty list 
        if 'laser_patterns' in self.box.software_config.keys(): 
            for (pattern_name, pattern) in self.box.software_config['laser_patterns'].items(): 
                # create a Cycle instance for each Pattern, and add an attribute for the pattern that points to the cycle instance  
                newCycle = self.Cycle(pattern_name, pattern['on_seconds'], pattern['off_seconds'], pattern['repeat'], self)
                setattr(self, pattern_name, newCycle ) 
                pattern_list.append(newCycle)
        return pattern_list
    
    def turn_on(self): 
        ''' turns laser on '''
        print(f'{self.name} On')
        latency_obj = self.box.timestamp_manager.new_latency(description = oes.laser_on_latency, modifiers = {'ID':self.name})
        self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.laser_on+self.name, modifiers = {'ID':self.name})
        self.on = True 
        self.gpio.output(self.pin, GPIO.HIGH) # sets to 3.3V
        return latency_obj

    
    def turn_off(self, latency_obj = None): 
        ''' turns laser off '''
        print(f'{self.name} Off')
        self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.laser_off+self.name, modifiers = {'ID':self.name})        
        self.on = False
        self.gpio.output(self.pin, GPIO.LOW) # sets to 0.0V
        if latency_obj is not None: 
            latency_obj.submit() # sets time of the latency from when we turned the laser on until right when we turn the laser off 
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
            self.pi = self.box.pi
        if 'click_on' in self.tone_dict:
            self.click_on_train = [(tone_values['hz'], tone_values['length']) for _, tone_values in self.tone_dict['click_on'].items()]
        if 'click_off' in self.tone_dict:
            self.click_off_train = [(tone_values['hz'], tone_values['length']) for _, tone_values in self.tone_dict['click_off'].items()]
        self.tone_queue = queue.Queue()
        self.tone_list = []
        self.hz = 0
        self.on = False
        self.handler_running = False
    
    
    @thread_it
    def speaker_queue_handler(self):
        self.handler_running = True
        while not self.box.finished():
            if not self.tone_queue.empty():

                new_tone = self.tone_queue.get()
                #start the timer on the tone now that it has arrived. set start/stop time within tone obj
                new_tone.start()
                self.tone_list.insert(0, new_tone)
                self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.tone_start + new_tone.name, modifiers = {'ID':self.name})
                if 'serial_send' in self.box.software_config['checks'].keys():
                    if self.box.software_config['checks']['serial_send'][self.name]:
                        self.box.serial_sender.send_data(f'{self.name} {new_tone.name} start')
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
                self.handler_running = False
                self.set_off()
                break
 
    def turn_off(self):
        self.pi.set_PWM_dutycycle(self.pin, 0)                  
                    
    def set_hz(self, hz):

        self.pi.set_PWM_frequency(self.pin, int(hz))
        self.hz = hz


    @thread_it
    def play_tone(self, tone_name, wait = False):
        '''use pigpio to play a tone, called by name from the dict imported from software config file'''
        if not tone_name in self.tone_dict.keys():
            raise KeyError(f'tone: {tone_name} was not defined in the softare dictionary')
        elif 'type' in self.tone_dict[tone_name]:
            if self.tone_dict[tone_name]['type'] == 'structured':
                self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.tone_start + tone_name, modifiers = {'ID':self.name})
                if 'serial_send' in self.box.software_config['checks'].keys():
                    if self.box.software_config['checks']['serial_send'][self.name]:
                        self.box.serial_sender.send_data(f'{self.name} {tone_name} start')
                Structured_Tone(self.tone_dict[tone_name], self).play()
                
                self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.tone_stop + tone_name, modifiers = {'ID':self.name})
                length = 0
            elif self.tone_dict[tone_name]['type'] == 'tone_train':
                self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.tone_start + tone_name, modifiers = {'ID':self.name})
                if 'serial_send' in self.box.software_config['checks'].keys():
                    if self.box.software_config['checks']['serial_send'][self.name]:
                        self.box.serial_sender.send_data(f'{self.name} {tone_name} start')
                ToneTrain(self.tone_dict[tone_name], self).play()
                
                self.box.timestamp_manager.create_and_submit_new_timestamp(description = oes.tone_stop + tone_name, modifiers = {'ID':self.name})
                length = 0
            elif self.tone_dict[tone_name]['type'] == 'continuous':
                hz = self.tone_dict[tone_name]['hz']
                length = self.tone_dict[tone_name]['length']
                self.tone_queue.put(Tone(hz, length, tone_name))
                if not self.handler_running:
                    self.speaker_queue_handler()
            else:
                hz = self.tone_dict[tone_name]['hz']
                length = self.tone_dict[tone_name]['length']
                self.tone_queue.put(Tone(hz, length, tone_name))
                if not self.handler_running:
                    self.speaker_queue_handler()
        else:
            hz = self.tone_dict[tone_name]['hz']
            length = self.tone_dict[tone_name]['length']
            self.tone_queue.put(Tone(hz, length, tone_name))
            if not self.handler_running:
                    self.speaker_queue_handler()
        
        #not my favorite way to handle this as it is not directly tied to the behavior of the speaker, but it is close
        #perhaps, integrate a .done() into Tone objs so that it can be queried. 
        time.sleep(length)


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
        
        self.set_off()


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
    
class Structured_Tone:
    def __init__(self, tone_dict, speaker_instance):
        self.tone_dict = tone_dict
        self.speaker = speaker_instance
    
    def play(self):
        '''leaving off "thread_it" intentionally as this will be called from
        a threaded function. that also means that the parent function will
        wait on this play function until it finishes. good to keep in mind.'''
        on = self.tone_dict['on_time'] / 1000
        off = self.tone_dict['off_time'] / 1000
        self.speaker.set_hz(self.tone_dict['hz'])
        length = self.speaker.box.timing.new_timeout(self.tone_dict['length'])
        while length.active():
            self.speaker.set_on()
            precise_sleeper(on)
            self.speaker.set_off()
            precise_sleeper(off)
            
class ToneTrain:
    class ToneGenerator(object):
        def __init__(self, tone_train):
            self.tt = tone_train
            self.tone_list = self.make_tone_list(self.tt['tones'])
            self.length = len(self.tone_list)
            self.position = 0

        def make_tone_list(self, tone_dict):
            out_list = []
            for tone in sorted(tone_dict.keys()):
                out_list+=[(tone_dict[tone]['hz'], tone_dict[tone]['on_time']/1000, tone_dict[tone]['off_time']/1000)]
            return out_list
        
        def __iter__(self):
            return self

        def __next__(self):
            return self.next()
        
        def next(self):
            
            current, self.position = self.tone_list[self.position%self.length], self.position + 1
            return current


    def __init__(self, tone_dict, speaker_instance):
        self.tone_dict = tone_dict
        self.speaker = speaker_instance
        self.tone_generator = self.ToneGenerator(self.tone_dict)
    



    def play(self):
        '''leaving off "thread_it" intentionally as this will be called from
        a threaded function. that also means that the parent function will
        wait on this play function until it finishes. good to keep in mind.'''
        length = self.speaker.box.timing.new_timeout(self.tone_dict['length'])
        while length.active():
            hz, t_on, t_off = next(self.tone_generator)
            self.speaker.set_hz(hz)
            self.speaker.set_on()
            precise_sleeper(t_on)
            self.speaker.set_off()
            precise_sleeper(t_off)

class Input:
            
    def __init__(self, name, input_config_dict, box, simulated = False):
    
        self.config_dict = input_config_dict
        
        self.box = box
        self.pin = self.config_dict['pin'] #int
        self.name = name #str
        
        switch_dict = {
                        'pin':self.pin,
                        'pullup_pulldown':self.config_dict['pullup_pulldown'],
                    }

        self.switch = self.box.button_manager.new_button(self.name, switch_dict, self.box)
        
        
    def wait_for_press(self):
        print(f'button {self.name} is waiting to be pressed')
        while not self.switch.pressed:
            time.sleep(0.05)
    
    def is_pressed(self):
        return self.switch.pressed
    
class Beam:
    
    def __init__(self, name, beam_config_dict, box, simulated = False):
        
        
        self.config_dict = beam_config_dict
        
        self.box = box
        self.pin = self.config_dict['pin'] #int

        self.name = name #str
        
        switch_dict = {
            'pin':self.pin,
            'pullup_pulldown':self.config_dict['pullup_pulldown'],
        }

        self.switch = self.box.button_manager.new_button(self.name, switch_dict, self.box)
        self.monitor = False

        self.total_beam_breaks = 0
        self.counting = False # set to True while the count_beam_breaks function is running
        self.get_durations = False # set to True when we want to be creating duration objects to represent if vole is in or out of the Interaction Zone


    def shutdown_protocol(self):
        '''how to get this object to shutdown when the box is finished'''
        self.monitor = False
        self.get_durations = False 
        self.counting = False 

    
    @thread_it
    def sim_break(self):
        self.switch.simulate_pressed()
        time.sleep(0.7)
        self.switch.simulate_unpressed()


    ''' Interaction Zone Functions for Anne '''
    def start_getting_beam_broken_durations(self): 
        self.get_durations = True 
        self.get_beam_broken_durations(reset_on_call=True)
    def stop_getting_beam_broken_durations(self): 
        self.get_durations = False 
    
    @thread_it 
    def get_beam_broken_durations(self, reset_on_call=False): 

        '''VERSION 2 of getting durations. This one assumes that a vole is large enough that when it is in the interaction zone, the ir beam is broken the entire time.'''
        self._begin_monitoring() # sets monitoring to true 

        if reset_on_call: 
            self.total_beam_breaks = 0

        while self.monitor and self.get_durations and not self.box.finished(): 

            if self.switch.pressed: 
                self.total_beam_breaks += 1 

                print(f'total beam breaks: {self.total_beam_breaks} ')

                # create duration object 
                duration = self.box.timestamp_manager.new_duration(description = oes.inside_interaction_zone+self.name, modifiers={'ID':self.name}, event_1=f'entered_interaction_zone_{self.name}')

                while self.monitor and self.switch.pressed and not self.box.finished(): 
                    '''wait for state change/unpress to occur'''
                
                if not self.switch.pressed: 
                    duration.event_2 = f'exited_interaction_zone_{self.name}'
                    duration.submit()
                else: 
                    # monitoring stopped 
                    duration.event_2 = f'stopped monitoring while vole still in interaction zone_{self.name}'
                    duration.submit()
    
    ''' Interaction Zone Monitoring, Version 2: Assumes vole is small enough that it will run completely passed the ir beam, so requires some extra work to become aware of where the vole is positioned.'''
    @property 
    def inInteractionZone(self): 
        # using the total number of beam breaks that have been recorded, returns True/False to represent if a vole is in the interaction zone or not 
        if self.total_beam_breaks%2 != 0:  return True 
        else:  return False 
    
    @thread_it
    def get_interaction_zone_durations( self, door_object = None ): 
        '''
            if a door_object gets passed in, then we adjust behavior when the door is open vs. closed. When the door is closed, 
            we assume that every beam break is entering the interaction zone and every beam unbroken is the vole leaving, because there is not enough room for the vole to get passed the ir beam.
        '''

        if self.counting is False: 
            print('At time of get_interaction_zone_durations() call, was not already counting the beam breaks. As a result, cannot tell if vole is starting out in the interaction zone or not. Calling count_beam_breaks() now.')
            self.count_beam_breaks() # should already have been counting beam breaks by now, but if we weren't, start now. 
            self._begin_monitoring()

        self.get_durations = True  # To stop this function, set self.get_durations to False 

        breaks_prev = self.total_beam_breaks 

        #
        #   Initialize Duration Variable 
        # Check if vole is already in the interaction zone. ( represented by an odd number of beam breaks )
        if self.inInteractionZone: 
            # vole is starting out in the interaction zone. Create a duration object to represent this. 
            duration = self.box.timestamp_manager.new_duration(description = oes.inside_interaction_zone, event_1 = 'Vole in the interaction zone at start of duration tracking.')
            print(f'Vole in the interaction zone at start of duration tracking. (total breaks: {self.total_beam_breaks})')
            state = True 
        else: 
            state = False 
            duration = None 

        while self.monitor and self.get_durations and not self.box.finished(): 
            
            # Wait to continue until inInteractionZone changes states 
            while self.monitor and self.get_durations and not self.box.finished():
                ''' do nothing until total_beam_breaks has been incremented '''
                if breaks_prev != self.total_beam_breaks: 
                    break 

            if not self.monitor or not self.get_durations: 
                return 

            breaks_prev = self.total_beam_breaks 

            # while get_durations is set to True, continuously create/submit duration objects thru the timestamp manager to represent when the vole is in the interaction zone
            if self.inInteractionZone: 
                state = True 
                # vole entered interaction zone. Set event 1
                print(f'vole entered interaction zone (total breaks: {self.total_beam_breaks})')
                duration = self.box.timestamp_manager.new_duration(description = oes.inside_interaction_zone+self.name, modifiers={'ID':self.name}, event_1=f'entered interaction zone')
            else: 
                state = False 
                # vole left the interaction zone. Set event 2 
                print(f'vole left interaction zone (total breaks: {self.total_beam_breaks})')
                duration.event_2 = 'exited interaction zone'
                duration.submit()
        
            
    @thread_it
    def count_beam_breaks( self, reset_on_call = False ): 
        ''' 
            counts the total number of beam breaks. if get_duration is set to True, then will create Duration objects and submit to the output file. 
            
            ** 
            This is for use in monitoring when a vole is in the 'interaction zone'. This only provides info on when a beam is broken, not when it is unbroken. 
            To retrieve info on when a beam is broken & unbroken, use the function monitor_beam_break instead. 
            ** 
        
        '''
        if reset_on_call is True: 
            self.total_beam_breaks = 0 # starts from scratch each time the function is called 


        self.counting = True # allows other functions to see that we are currently counting the total number of beam breaks!
        self._begin_monitoring() # sets monitoring to true 


        while self.monitor: 

            if self.switch.pressed: 
                self.total_beam_breaks += 1 

                print(f'total beam breaks: {self.total_beam_breaks} ')

                while self.monitor and self.switch.pressed: 
                    '''wait for state change/unpress to occur'''

        self.counting = False 


    def monitor_beam_break(self, latency_to_first_beambreak = None, end_with_phase = None):
        if self.monitor:
            print(f'beam monitoring already active, but monitor_beam_break was called again for {self.name}. this will be ignored')
        if end_with_phase:
            self._monitor_beam_break_for_phase(end_with_phase, latency = latency_to_first_beambreak)
        else:
            self._monitor_beam_break(latency = latency_to_first_beambreak)
    
    @thread_it     
    def _monitor_beam_break_for_phase(self, phase, latency = None):
        print(f'starting to monitor beam {self.name}')
        self._begin_monitoring()
        if latency:
            local_latency = copy.copy(latency)
            local_latency.event_2 = oes.beam_broken+self.name
            local_latency.reformat_event_descriptor()
            local_latency.add_modifier(key = 'beam_ID', value = self.name)
            latency_submitted = False
            while self.monitor and phase.active() and not latency_submitted:
                if self.switch.pressed:
                    local_latency.submit()
                    self.box.timestamp_manager.create_and_submit_new_timestamp(oes.beam_broken+self.name, 
                                                                                modifiers = {'ID':self.name}, 
                                                                                print_to_screen = False)
                    latency_submitted = True 
                    timeout = self.box.timing.new_timeout(0.1)
                    while self.switch.pressed or timeout.active():
                        ''''''
                    if self.monitor:
                        self.box.timestamp_manager.create_and_submit_new_timestamp(oes.beam_unbroken+self.name, 
                                                        modifiers = {'ID':self.name})
                    else:
                        self.box.timestamp_manager.create_and_submit_new_timestamp(oes.beam_unbroken+self.name, 
                                                        modifiers = {'ID':self.name})
        while self.monitor and phase.active():
            if self.switch.pressed:
                self.box.timestamp_manager.create_and_submit_new_timestamp(oes.beam_broken+self.name, 
                                                   modifiers = {'ID':self.name},
                                                   print_to_screen = False)
                
                while self.switch.pressed:
                    ''''''
                if self.monitor:
                        self.box.timestamp_manager.create_and_submit_new_timestamp(oes.beam_unbroken+self.name, 
                                                        modifiers = {'ID':self.name})
                else:
                    self.box.timestamp_manager.create_and_submit_new_timestamp(oes.beam_unbroken+self.name, 
                                                    modifiers = {'ID':self.name})
        self.end_monitoring()
    
    @thread_it     
    def _monitor_beam_break(self, latency = None):
        self._begin_monitoring()
        if latency:
            local_latency = copy.copy(latency)
            local_latency.event_2 = oes.beam_broken+self.name
            local_latency.add_modifier(key = 'beam_ID', value = self.name)
    
            while self.monitor:
                if self.switch.pressed:
                    local_latency.submit()
                    self.box.timestamp_manager.create_and_submit_new_timestamp(oes.beam_broken+self.name, 
                                                                                modifiers = {'ID':self.name})
                    
                    while self.switch.pressed and self.monitor:
                        ''''''
                        time.sleep(0.05)
                    if self.monitor:
                        self.box.timestamp_manager.create_and_submit_new_timestamp(oes.beam_unbroken+self.name, 
                                                        modifiers = {'ID':self.name})
                    else:
                        self.box.timestamp_manager.create_and_submit_new_timestamp(oes.beam_unbroken+self.name, 
                                                        modifiers = {'ID':self.name})
      
                    
        while self.monitor:
            if self.switch.pressed:
                self.box.timestamp_manager.create_and_submit_new_timestamp(oes.beam_broken+self.name, 
                                                   modifiers = {'ID':self.name})

                while self.switch.pressed and self.monitor:
                    ''''''
                if self.monitor:
                    self.box.timestamp_manager.create_and_submit_new_timestamp(oes.beam_unbroken+self.name, 
                                                        modifiers = {'ID':self.name})
                else:
                    self.box.timestamp_manager.create_and_submit_new_timestamp(oes.bb_monitor_ended_bb+self.name, 
                                                   modifiers = {'ID':self.name})
        
                
        
    def _begin_monitoring(self):
        self.monitor = True
    
    def end_monitoring(self):
        self.monitor = False
        


class BonsaiSender:

    # SENDER is the object that sends information to Bonsai which includes timestamps and information on what event has occured.
    #        The arduino will send analog signals via Firmata on the specified pin. Those values can be between 
    # INPUTS: port (str) - path of the serial port to connect to, defaults to GPIO serial of the pi
    #         baud (int) - Baud rate that the serial port runs on (default 9600 to match arduino)
    #         commandFile (str) - path of the commands.csv file where the commands are located

    def __init__(self, port = '/dev/serial0', baud = 9600, box = None):
        # Set the initial properties
        print('initializing sender')
        self.finished = False
        self.sending = False
        
        self.port        = port
        self.baudRate    = baud
        self.command_stack = queue.Queue()
        self.timeout = 2
        self.up = False
        if box:
            self.box = box
        # Initialize the port
        try:
            self.ser = ser.Serial(self.port, self.baudRate)
            time.sleep(1)
            self.ser.write('test_com_line 1 of 3\r'.encode('ascii'))
            time.sleep(0.25)
            self.ser.write('test_com_line 2 of 3\r'.encode('ascii'))
            time.sleep(0.25)
            self.ser.write('test_com_line 3 of 3\r'.encode('ascii'))
            time.sleep(0.25)
        except Exception as e:
            print('serial sender failed setup. If not sending serial data for Bonsai integration, ignore this warning.')
            print(e)
        self.up = True
        self.active = False


    def busy(self):
        return self.sending

    def shutdown(self):
        self.finished = True

    def running(self):
        return self.active
    
    @thread_it
    def run(self):
        self.active = True
        
        if not self.command_stack.empty():
            command = self.command_stack.get()
            self._send_data(command)
            while not self.command_stack.empty():
                command = self.command_stack.get()
                self._send_data(command)
        self.active = False

    def prepare_message(self, string):
        '''use this to pass a callable function that can be triggered'''
        return lambda: self.send_data(string)    
    
    def send_data(self, string):
        
        self.command_stack.put(string)
        if not self.active:
            self.run()
            
    def _send_string(self, string):
        
        #add termination char
        formatted = string + '\r'
        formatted = formatted.encode('ascii')
        
        self.ser.write(formatted)
        print(f'\n\nserial message sent: {string}\n\n')
        
    def _send_data(self, command):
        # SEND_DATA sends the data through the associated serial port, and then logs all the commands that have been send to the self.history queue object.
        

        #add termination char
        formatted = command + '\r'
        formatted = formatted.encode('ascii')
        if self.box:
            self.box.timestamp_manager.create_and_submit_new_timestamp(description = f'serial_send: {command}', print_to_screen = False)
        self.ser.write(formatted)
        
    
    
class Fake_GPIO:
    def __init__(self):
        self.IN = 1
        self.OUT = 0
    
    def setup(self, pin, val):
        pass
    
    def input(self, pin):
        return 3

def precise_sleeper(duration, get_now=time.perf_counter):
    now = get_now()
    end = now + duration
    while now < end:
        now = get_now()

#i bet I can generate this dynamically from the classes, if they have certain attrs,
#like "plural_name" and "component_type"
COMPONENT_LOOKUP = {
                    'doors':{'component_class':Door, 'label':'door'},
                    'levers':{'component_class':Lever, 'label':'lever'},
                    'inputs':{'component_class':Input, 'label':'input'},
                    'dispensers':{'component_class':Dispenser, 'label':'dispenser'},
                    'positional_dispensers':{'component_class':PositionalDispenser, 'label':'positional_dispenser'},
                    'port_dispensers':{'component_class':PortDispenser, 'label':'port_dispenser'},
                    'outputs':{'component_class':Output, 'label':'output'},
                    'speakers':{'component_class':Speaker, 'label':'speaker'}, 
                    'lasers':{'component_class':Laser, 'label':'laser'}, 
                    'beams': {'component_class':Beam, 'label':'beam'},
                    'nose_pokes': {'component_class':NosePoke, 'label':'nose_poke'}
                    }
