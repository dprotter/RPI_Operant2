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
    
    def add_to_queue(self, updated_time = None): 
        # self.timestamp = "{:.2f}".format(self.timestamp)
        if updated_time is not None: 
            self.timestamp = "{:.2f}".format(updated_time - self.round_start_time)
        else: 
            self.timestamp = "{:.2f}".format(self.timestamp - self.round_start_time)
        self.timestamp_manager.record_new(self)
        #self.timestamp_manager.print_items()
        
        


class TimestampManager(): 
    def __init__(self): 
        self.queue = Queue()

        # Round and start time are updated each new round 
        self.round = 0 
        self.round_start_time = time.time() 
        self.phase = self.__first_phase()
    

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
    

    
    

    
    