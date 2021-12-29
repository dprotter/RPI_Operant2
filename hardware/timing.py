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

class TimeManager:

    def __init__(self, box):
        ''''''
        self.output_queue = Queue()
        self.box = box
        self.start_time = None
        self.round = 1
        self.current_phase = None
    
    def start_timing(self):
        self.start_time = time.time()

    def new_timeout(self, length):
        return Timeout(length)


class Phase: 
    def __init__(self, name, length, box): 
            # if timeframe is None, then there is no time limit on this phase. As a result, it will run until interrupt or a new phase is created
            self.start_time = time.time()
            self.end_time = self.start_time + length
            self.active = True 
            self.name = name 
            self.timeframe = length
            
    
    def display_countdown_timer(self): 
        # print a countdown to the screen based on the remaining time left in <timeframe> 
        print("\r")
        timeinterval = self.timeframe
        while timeinterval:
            mins, secs = divmod(timeinterval, 60)
            timer = '{:02d}:{:02d}'.format(mins, secs)
            sys.stdout.write(f"\r{timer} until end of Phase: {self.name}  ")
            time.sleep(1)
            timeinterval -= 1

    def is_active(self):
        if time.time() >= self.end_time:
            return False
        else:
            time.sleep(0.05)
            return True


class Timestamp: 
    def __init__(self, timestamp_manager, event_descriptor, modifiers): 
        
        # self.timestamp = "{:.2f}".format(timestamp) # format time to 2 decimal points 
        self.timestamp_manager = timestamp_manager 
        self.event_descriptor = event_descriptor # string that describes what the event is 
        self.round = timestamp_manager.round # round number that event occurred during 
        self.round_start_time = timestamp_manager.round_start_time
        self.phase = timestamp_manager.phase
        self.round_initialized = timestamp_manager.round 
    
    def submit(self): 
        t = time.time()
        self.timestamp = round(t - self.timestamp_manager.experiment_start_time, 2)
        self.timestamp_manager.queue.put(self)

class Latency: 
    def __init__(self, timestamp_manager, event_descriptor, modifiers): 

        self.start_time = time.time()
        self.timestamp_manager = timestamp_manager 
        self.event_descriptor = event_descriptor # string that describes what the event is 
        self.phase_initialized = timestamp_manager.phase # phase that timestamp was initialized occurred during 
        self.round_initialized = timestamp_manager.round  # round number that timestamp was initialized occurred during 
        self.modifire = modifiers

    def submit(self): 
        # self.timestamp = "{:.2f}".format(self.timestamp)
        t = time.time()
        self.latency = round(t - self.start_time, 2)
        self.timestamp = round(t - self.timestamp_manager.experiment_start_time, 2)
        self.timestamp_manager.queue.put(self)

class TimestampManager: 
    def __init__(self, box): 
        self.queue = Queue()

        # Round and start time are updated each new round 
        self.box = box
        self.round = 0 
        self.round_start_time = time.time() 
        self.phase = None
        self.save_path = self.box.software_config['output_path']
        self.experiment_start_time = None
        

    def start_timing(self):
        self.experiment_start_time = time.time()

    def new_timestamp(self, description, modifiers = None):
        '''how to create a new timestamp object'''
        return Timestamp(self, description, modifiers)

    def submit_new_timestamp(self, description, modifiers = None):
        '''how to create a new timestamp object'''
        Timestamp(self, description, modifiers).submit()

    def new_latency(self, description, modifiers = None):
        '''will track latency between initialization and submission'''
        return Latency(self, description, modifiers)

    def new_phase(self, name, length=None): # creates a new phase, forgetting whatever phase we were previously in
        self.phase = Phase(self, name, length, box = self.box)


    def new_round(self, round, round_start_time): 
        self.round = round 
        self.round_start_time = round_start_time


    def record_new(self, timestamp_obj): 
        self.queue.put(timestamp_obj)


    def print_items(self): 
        print('--Timestamp Queue--')
        for q_item in self.queue.items: 
            print((q_item.timestamp, q_item.event))
        print('----------------')


    def finish_writing_items(self): 
        self.queue.join()

    def format(self, timestamp_obj):
        if isinstance(timestamp_obj, Timestamp):
            return [timestamp_obj.round, timestamp_obj.event_descriptor, timestamp_obj.timestamp, timestamp_obj.phase, None, timestamp_obj.round_initialized]
        
        elif isinstance(timestamp_obj, Latency):
            return [timestamp_obj.round, timestamp_obj.event_descriptor, timestamp_obj.timestamp, timestamp_obj.phase, timestamp_obj.latency, timestamp_obj.round_initialized]
        
        else:
            print(f'timestamp error, unknown object passed to timestamp manager: {timestamp_obj}')

    def monitor_queue(self):
        '''monitor and write to queue. some threading here''' 
        if self.box.software_config['checks']['save_timestamps']:
            while not self.box.finished():
                
                if not  self.queue.empty():

                    #open file here to prevent repeated opening and closing
                    with open(self.save_path, 'a') as file:
                        csv_writer = csv.writer(file, delimiter = ',')
                        while not self.queue.empty():

                            ts = self.queue.get()
                            line = self.format(ts)
                            ######add ts to screen write queue
                            csv_writer.writerow(line)
                            time.sleep(0.005)

        #dont save timestamps, but do print them to the terminal
        else:
            while not self.box.finished():
                if not  self.queue.empty():

                    while not self.queue.empty():
                        ######add ts to screen write queue
                        time.sleep(0.005)

    
class Timeout:
    '''a class used to make temporary timeout objects to streamline code.'''
    def __init__(self, length):
        self.start_time = time.time()
        self.end_time = self.start_time + length

    def is_active(self):
        '''when queried check if time has expired'''
        if time.time() >= self.end_time:
            return False
        else:
            time.sleep(0.05)
            return True
    
    def wait(self):
        while self.is_active():
            '''hold this thread'''
        return None