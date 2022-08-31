''' --------------------------------------------------------------------------------------------------------------------------------
                                                    filename: timing.py
                description:  Classes that control the timing and record timestamps throughout experiment execution 
                - TimestampManager
                - Timestamp 
                - Phase                                                 
-----------------------------------------------------------------------------------------------------------------------------------'''

#!/usr/bin/python3

# standard lib imports 
import time
from queue import Queue 
import sys
import csv
import socket
from RPI_Operant.hardware.software_functions import ScreenPrinter

def format_ts(timestamp_obj):
    
    mod_string = ''
    if timestamp_obj.modifiers:
        
        #access our dictionary, sorted
        for key,val in sorted(timestamp_obj.modifiers.items(), key = lambda item: item[0]):
            mod_string+=f'{key}:{val}|'
            
    if isinstance(timestamp_obj, Timestamp):
        return [timestamp_obj.round, timestamp_obj.event_descriptor, timestamp_obj.timestamp, timestamp_obj.phase_initialized, timestamp_obj.phase_submitted, None, mod_string, timestamp_obj.round_initialized]
    
    elif isinstance(timestamp_obj, Latency):
        return [timestamp_obj.round, timestamp_obj.event_descriptor, timestamp_obj.timestamp, timestamp_obj.phase_initialized, timestamp_obj.phase_submitted, timestamp_obj.latency, mod_string, timestamp_obj.round_initialized]
    
    else:
        print(f'timestamp writing error, unknown object passed to timestamp manager: {timestamp_obj}')

class TimeManager:

    def __init__(self, box):
        ''''''
        self.output_queue = Queue()
        self.round = 0
        self.current_phase = None
        self.start_time = None
        self.round_start_time = None
        self.box = box
        self.countdowns = []
    
    def add_countdown(self, obj):
        #print(f'adding cd {obj.name}')
        self.countdowns += [obj]
    
    def get_countdowns(self):
        self.check_countdowns()
        return self.countdowns

    def check_countdowns(self):
        for countdown in self.countdowns:
            if not countdown.active():
                #print(f'removing cd {countdown.name}')
                self.countdowns.remove(countdown)
    
    def start_timing(self):
        if self.start_time:
            raise Exception('woah! timing already started. if you want to *restart* timing, use restart_timing()')
        else:
            self.start_time = time.time()
            self.round_start_time = time.time()
            self.box.timestamp_manager.create_save_file()
            self.box.timestamp_manager.screen.print_output()

    def restart_timing(self):
        self.start_time = time.time()

    def new_timeout(self, length):
        return Timeout(length)

    
    def new_phase(self, name, length=None): # creates a new phase, forgetting whatever phase we were previously in
        self.current_phase = Phase(name, length, box = self.box)
        return self.current_phase

    def new_round(self, length = None): 
        self.round = self.round + 1 
        self.round_start_time = time.time()
        if length:
            self.round_length = length
    
    def wait_for_round_finish(self):
        while not self.round_over():
            time.sleep(0.1)
            
    def round_time_remaining(self):
        return (self.round_start_time + self.round_length) - time.time()
    
    def round_over(self):
        if 'round_length' in self.__dict__.keys():
            if self.round_start_time + self.round_length < time.time():
                self.round_length = None
                return True
            else:
                time.sleep(0.05)
                return False
        else:
            print('WARNING --> CANT ask if round is finished using round_finished(), no round length provided')
            
class Phase: 
    def __init__(self, name, length=1000, box=None, countdown = True): 
            # if timeframe is None, then there is no time limit on this phase. As a result, it will run until interrupt or a new phase is created
            self.start_time = time.time()
            self.end_time = self.start_time + length
            self.name = name 
            self.timeframe = length
            self.is_active = True
            if countdown:
                if box:
                    box.timing.add_countdown(self)
    
    def get_time_remaining(self):
        
        return round(self.end_time - time.time(), 1)

    def active(self):
        if self.is_active:
            if time.time() >= self.end_time:
                self.is_active = False
                return False
            else:
                time.sleep(0.0025)
                return True
        else:
            return False

    def end_phase(self):
        self.is_active = False
        
    def wait(self):
        '''hold onto this thread while active. essentially a join function. other threads will continue, but
        whatever thread called this will be blocked until the time is up, no matter what.'''
        while self.active():
            time.sleep(0.1)

class Timestamp: 
    def __init__(self, timestamp_manager, event_descriptor, modifiers = None, print_to_screen = True): 
        
        
        self.timestamp_manager = timestamp_manager 
        self.event_descriptor = event_descriptor # string that describes what the event is 
        self.round = timestamp_manager.timing.round # round number that event occurred during 
        self.round_start_time = timestamp_manager.timing.round_start_time
        self.phase_initialized = timestamp_manager.timing.current_phase.name if timestamp_manager.timing.current_phase else Phase(name = 'NoPhase').name
        self.print_to_screen = print_to_screen
        
        self.round_initialized = timestamp_manager.timing.round
        if modifiers:
            if not isinstance(modifiers, dict):
                print('WARNING! Latency object instantiated with non-dictionary "modifiers" argument.')
                self.modifiers = {'unknown':modifiers} 
            else:
                self.modifiers = modifiers
        else:
            self.modifiers = {}
        
    def add_modifier(self, key, value):
        
        self.modifiers.update({key:value})
        
    def submit(self): 
        t = time.time()
        self.timestamp = round(t - self.timestamp_manager.timing.start_time, 2)
        self.phase_submitted = self.timestamp_manager.timing.current_phase.name if self.timestamp_manager.timing.current_phase else Phase(name = 'NoPhase').name
        self.timestamp_manager.queue.put(format_ts(self))
        self.timestamp_manager.screen.print_queue.put(self)

class Latency: 
    def __init__(self, timestamp_manager, event_descriptor, modifiers = None): 

        self.start_time = time.time()
        self.timestamp_manager = timestamp_manager 
        self.event_descriptor = event_descriptor # string that describes what the event is 
        self.phase_initialized = timestamp_manager.timing.current_phase.name if self.timestamp_manager.timing.current_phase else Phase(name = 'NoPhase').name # phase that timestamp was initialized occurred during 
        self.round_initialized = timestamp_manager.timing.round  # round number that timestamp was initialized occurred during 
        if modifiers:
            if not isinstance(modifiers, dict):
                print('WARNING! Latency object instantiated with non-dictionary "modifiers" argument.')
                self.modifiers = {'unknown':modifiers} 
            else:
                self.modifiers = modifiers
        else:
            self.modifiers = {}
        
    def add_modifier(self, key, value):
        
        self.modifiers.update({key:value})
        
    def submit(self): 
        # self.timestamp = "{:.2f}".format(self.timestamp)
        t = time.time()
        self.round = self.timestamp_manager.timing.round
        self.latency = round(t - self.start_time, 2)
        self.timestamp = round(t - self.timestamp_manager.timing.start_time, 2)
        self.phase_submitted = self.timestamp_manager.timing.current_phase.name if self.timestamp_manager.timing.current_phase else Phase(name = 'NoPhase')
        
        
        self.timestamp_manager.queue.put(format_ts(self))
        self.timestamp_manager.screen.print_queue.put(self)

class TimestampManager: 
    def __init__(self, timing_obj, save_timestamps, box): 
        self.queue = Queue()
        self.box = box
        # Round and start time are updated each new round 
        self.timing = timing_obj
        self.save_timestamps = save_timestamps
        self.screen = ScreenPrinter(self.box)

    

    
    def create_save_file(self):
        self.save_path = self.box.output_file_path + '.csv'
        print(f'csv path: {self.save_path}')
        if self.save_timestamps:
            with open(self.save_path, 'w') as file:
                header = ['round','event','time','phase initialized','phase submitted','latency','modifiers','round timestamp initialized']
                csv_writer = csv.writer(file, delimiter = ',')
                csv_writer.writerow(header)
                

    def new_timestamp(self, description, modifiers = None):
        '''how to create a new timestamp object'''
        return Timestamp(self, description, modifiers)

    def create_and_submit_new_timestamp(self, description, modifiers = None):
        '''create and immediately submit new timestamp'''
        Timestamp(self, description, modifiers).submit()

    def new_latency(self, description, modifiers = None):
        '''will track latency between initialization and submission'''
        return Latency(self, description, modifiers)


    def finish_writing_items(self): 
        self.queue.join()

    
    def monitor_queue(self):
        '''monitor and write to queue. some threading here''' 
        if self.save_timestamps:
            while not self.box.finished():
                
                if not  self.queue.empty():

                    #open file here to prevent repeated opening and closing
                    with open(self.save_path, 'a') as file:
                        csv_writer = csv.writer(file, delimiter = ',')
                        while not self.queue.empty():

                            line = self.queue.get()
                            ######add ts to screen write queue
                            csv_writer.writerow(line)
                            
                            time.sleep(0.005)

        #dont save timestamps, but do print them to the terminal
        else:
            while not self.box.finished():
                if not self.queue.empty():

                    while not self.queue.empty():
                        ######add ts to screen write queue
                        line = self.queue.get()
                        
                        print(line)
                        time.sleep(0.005)

    
class Timeout:
    '''a class used to make temporary timeout objects to streamline code.'''
    def __init__(self, length):
        self.start_time = time.time()
        self.end_time = self.start_time + length

    def active(self):
        '''when queried check if time has expired'''
        if time.time() >= self.end_time:
            return False
        else:
            time.sleep(0.05)
            return True
    
    def wait(self):
        '''essentially a join function. Other things in other threads will still occur, but whatever thread called this will
        be blocked until the time is up, no matter what.'''
        while self.active():
            '''hold this thread'''
            time.sleep(0.05)
        return None