import time
import RPi.GPIO as GPIO
import queue
from concurrent.futures import ThreadPoolExecutor



class Lever:
    
    def __init__(self, lever_config_dict, lever_default_dict, timestamp_q):
        
        self.pin = lever_config_dict['pin'] #int
        self.extended = lever_config_dict['extended'] #int, servo angle
        self.retracted = lever_config_dict['retracted'] #int, servo angle
        self.name = lever_config_dict['name'] #str
        self.servo = lever_config_dict['servo'] #kit.servo
        
        #replace this with a dict expression pulling with priority from lever_config_dict and falling abck to lever_default_dict
        self.retraction_timeout = lever_config_dict['retraction_timeout'] if 'retraction_timeout' in lever_config_dict.keys() else 2
        self.interpress_timeout = lever_config_dict['interpress_timeout'] if 'interpress_timeout' in lever_config_dict.keys() else 0.5
        
        #threading        
        self.threads = ThreadPoolExecutor(max_workers = 6)
        self.futures = []
        
        #attributes for tracking during runtime
        self.total_presses = 0
        self.presses_reached = False
        self.monitoring = False
        self.stop_threads = False
        self.press_q = queue.Queue()
        
        
        self.timestamp_q = timestamp_q
        self.wiggle = 10
        
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
            if not GPIO.input(self.pin):
                print(f'{self.name}pressed!')
                
                self.click_on()
                while not GPIO.input(self.pin) and self.end_monitor == False:
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