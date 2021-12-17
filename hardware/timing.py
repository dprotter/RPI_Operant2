''' --------------------------------------------------------------------------------------------------------------------------------
                                                    filename: timing.py
                description:  Classes that control the timing and record timestamps throughout experiment execution 
                - TimestampManager
                - Timestamp 
                - Phase                                                 
-----------------------------------------------------------------------------------------------------------------------------------'''

#!/usr/bin/python3

# standard lib imports 
from _typeshed import Self
import time
from queue import Queue 
import sys
import csv

class TimeManager():

    def __init__(self, box):
        ''''''
        self.output_queue = Queue()
        self.box
        self.start_time = None
        self.round = 1
    
    def start_timing(self):
        self.start_time = time.time()

    

class Phase(): 
    def __init__(self, timestamp_manager, name, length, print_countdown): 
            # if timeframe is None, then there is no time limit on this phase. As a result, it will run until interrupt or a new phase is created
            self.active = True 
            self.name = name 
            self.timestamp_manager = timestamp_manager
            self.timeframe = length
            if print_countdown: self.display_countdown_timer() 
    
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



class Timestamp(): 
    def __init__(self, timestamp_manager, event_descriptor, timestamp): 
        
        # self.timestamp = "{:.2f}".format(timestamp) # format time to 2 decimal points 
        self.timestamp = timestamp
        self.timestamp_manager = timestamp_manager 
        self.event_descriptor = event_descriptor # string that describes what the event is 
        self.round = timestamp_manager.round # round number that event occurred during 
        self.round_start_time = timestamp_manager.round_start_time
        self.phase = timestamp_manager.phase
        self.round_initialized = timestamp_manager.round 
    
    def add_to_queue(self, updated_time = None): 
        # self.timestamp = "{:.2f}".format(self.timestamp)
        if updated_time is not None: 
            self.timestamp = "{:.2f}".format(updated_time - self.round_start_time)
        else: 
            self.timestamp = "{:.2f}".format(self.timestamp - self.round_start_time)
        self.timestamp_manager.record_new(self)
        #self.timestamp_manager.print_items()
        
class Latency(): 
    def __init__(self, timestamp_manager, event_descriptor): 
        
        
        self.start_time = time.time()
        self.timestamp_manager = timestamp_manager 
        self.event_descriptor = event_descriptor # string that describes what the event is 
        self.phase_initialized = timestamp_manager.phase # phase that timestamp was initialized occurred during 
        self.round_initialized = timestamp_manager.round  # round number that timestamp was initialized occurred during 
    
    def submit(self): 
        # self.timestamp = "{:.2f}".format(self.timestamp)
        t = time.time()
        self.latency = round(t - self.start_time, 2)
        self.timestamp = round(t - self.timestamp_manager.start_time, 2)
        self.timestamp_manager.queue.put(self)

class TimestampManager(): 
    def __init__(self): 
        self.queue = Queue()

        # Round and start time are updated each new round 
        self.round = 0 
        self.round_start_time = time.time() 
        self.phase = self.__first_phase()
        self.save_path = self.box.config['output_path']
        self.start_time = None

    def start_timing(self):
        self.start_time = time.time()

    def new_timestamp(self, description):
        '''how to create a new timestamp object'''
        return Timestamp(self, description)

    def new_latency(self, description):
        '''will track latency between initialization and submission'''
        return Latency(self, description)

    def __first_phase(self): 
        Phase(self, 'Object Instantiation & Experiment Setup', length=None, print_countdown=False )

    def new_phase(self, name, length=None, print_countdown=False): # creates a new phase, forgetting whatever phase we were previously in
        self.phase = Phase(self, name, length, print_countdown)


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
        
        elif isinstance(timestamp_obj, Latency)
            return [timestamp_obj.round, timestamp_obj.event_descriptor, timestamp_obj.timestamp, timestamp_obj.phase, timestamp_obj.latency, timestamp_obj.round_initialized]
        
        else:
            print(f'timestamp error, unknown object passed to timestamp manager: {timestamp_obj}')

    def monitor_queue(self):
        '''monitor and write to queue. some threading here''' 
        while not self.box.finished():

            if not  self.queue.empty():

                #open file here to prevent repeated opening and closing
                with open(self.save_path, 'a') as file:
                    csv_writer = csv.writer(file, delimiter = ',')
                    while not self.queue.empty():

                        ts = self.queue.get()
                        line = self.format(ts)
                        csv_writer.writerow(line)
                        time.sleep(0.005)


    
    

    
    