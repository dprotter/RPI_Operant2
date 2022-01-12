''' --------------------------------------------------------------------------------------------------------------------------------
                                                    filename: box.py
                description:  Box Class definition 
                - sets up the hardware components based on what the user specified to have setup in the configuration file 
                - if user does not pass the name of a file as an argument to Box instantiation, then the default configuration file is used. 
                                                
-----------------------------------------------------------------------------------------------------------------------------------'''

# Standard Library Imports 
import importlib.util
import RPi.GPIO as GPIO
# Third Party Imports 
# Local Imports

import os
from hardware.components import Button, Lever, Door, ButtonManager, Dispenser, Speaker
from hardware.timing import TimeManager, TimestampManager
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
import yaml
import queue
import time

# Constants 
DEFAULT_HARDWARE_CONFIG = os.path.join(os.getcwd(), 'hardware/default_hardware.yaml')
DEFAULT_SOFTWARE_CONFIG = os.path.join(os.getcwd(), 'hardware/default_software.yaml')
COMPONENT_LOOKUP = {
                    'doors':{'component_class':Door, 'label':'door'},
                    'levers':{'component_class':Lever, 'label':'lever'},
                    'buttons':{'component_class':ButtonManager.new_button, 'label':'button'},
                    'dispensers':{'component_class':Dispenser, 'label':'dispenser'},
                    'speakers':{'component_class':Speaker, 'label':'speaker'}
                    }



class Box: 

    def __init__(self, user_config_file_path=None, user_software_config_file_path = None, start_now = False): 
        GPIO.setmode(GPIO.BCM)
        ###### load and merge config files
        self.done = False
        self.config_file_path = DEFAULT_HARDWARE_CONFIG
        self.config = self.load_config_file(self.config_file_path)
        self.user_config_file_path = user_config_file_path
        if self.user_config_file_path:
            self.config = self.merge_config_files(user_config_file_path)

        self.software_config_file_path = DEFAULT_SOFTWARE_CONFIG
        self.software_config = self.load_config_file(self.software_config_file_path)
        self.user_software_config_file_path = user_software_config_file_path
        if self.user_software_config_file_path:
            self.software_config = self.merge_config_files(user_software_config_file_path)
        
        #self.timing is in charge tracking start time, making new timeouts, latencies, etc
        self.timing = TimeManager(self)

        #### timestamp queue that gets setup by ScriptManager
        self.timestamp_manager = TimestampManager(self)
        self.timestamp_q = self.timestamp_manager.queue

        
        #threading        
        self.thread_executor = ThreadPoolExecutor(max_workers = 10)
        self.worker_queue = queue.Queue()
        

        #the manager for creating, adding, and monitoring new binary inputs
        self.button_manager = ButtonManager(self)

        ###############

        #iterate across groups (IE doors, levers, etc etc)
        #lookup class object (ie Door() ) and label (ie "door")
        for component_group_name, group_dict in self.config.items():
            
            #create a new container to put components within
            if component_group_name in COMPONENT_LOOKUP.keys():
                label = COMPONENT_LOOKUP[component_group_name]['label']
                comp_container = ComponentContainer(label)
            else:
                print(f'{component_group_name} in hardware config, but Box does not yet have the ability to instantiate that class.')
                continue
            #iterate across all components in this class and use their dicts to instantiate a new 
            #component object
            component_class = COMPONENT_LOOKUP[component_group_name]['component_class']
            for name, comp_dict in group_dict.items():
                print(f'adding {name} to {component_class}')
                
                #this is where we instantiate our component (IE a new Door)
                component = component_class(name, comp_dict, self)
                comp_container.add_component(name, component)
            
            #add completed components (within component container) to the box
            setattr(self, component_group_name, comp_container)

        #VVVVVVVVVVVVVVVV wanted to simplify this call elsewhere as box.speaker.click_on etc etc
        self.speaker = self.speakers.speaker
        #^^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


        fut = self.thread_executor.submit(self.monitor_workers, verbose = True)
        
        #startup queue monitoring
        fut2 = self.thread_executor.submit(self.timestamp_manager.monitor_queue)
        self.worker_queue.put((fut2,'timestamp monitor_queue'))
        if not fut.running:
            if fut.exception():
                print(fut.exception())

        if start_now:
            self.timing.start_timing()

    def reload_hardware_config(self):
        '''reload config file'''
        self.config_file_path = DEFAULT_HARDWARE_CONFIG
        self.config = self.load_config_file(self.config_file_path)
        if self.user_config_file_path:
            self.config = self.merge_config_files(self.user_config_file_path)

    def load_config_file(self, file):
        '''load a config yaml file and return the resulting dict'''
        with open(file, 'r') as f:
            config_dict = yaml.safe_load(f)
        return config_dict

    def merge_config_files(self, new_file):
        new_config_dict = self.load_config_file(new_file)
        return self.heirarchical_merge_dict(self.config_dict, new_config_dict)
        

    def heirarchical_merge_dict(self, dict_default, dict_update):
        for key, value in dict_update.items():
            if isinstance(value, Mapping):
                #note to self the get(key,{}) returns an empty list if the key is not found. good technique for avoiding KeyErrors
                dict_default[key] = self.heirarchical_merge_dict(dict_default.get(key,{}), value)
            else:
                dict_default[key] = value
        return dict_default

    def get_component(self, component_type, component_name):
        attr_dict = self.__dict__
        if component_type not in attr_dict.keys():
            if component_type + 's' in attr_dict.keys():
                component_type = component_type + 's'
            else:
                raise KeyError(f'box has no component type {component_type}')

        component = attr_dict[component_type].get_component(component_name)
        return component

    def wait(self, worker, func_name):
        '''from main thread, hold the like a join() until a worker has finished'''
        if isinstance(worker, list):
            print(f'waiting for one of the workers assigned to function "{func_name}"')
            while not any([w.done() for w in worker]):
                '''waiting for threads to finish'''
                time.sleep(0.025)

        else:
            print(f'waiting for function "{func_name}"')
            while not worker.done():
                time.sleep(0.025)
        

    def monitor_workers(self, verbose = False):
        workers = []
        
        
        while not self.done:
            if not self.worker_queue.empty():
                #receive worker, parent function, round of initiation
                worker_and_info = self.worker_queue.get()
                if verbose:
                    print(f'worker queue received worker {worker_and_info}')
                #if we have an identically named worker, we will need to modify this tuple
                
                workers += [worker_and_info]
                print('\nvvvvvvvvvvvvvvvvvv')
                print(f'currently {len(workers)} threads running via pool executor')
                print(workers)
                print('\n\n^^^^^^^^^^^^^^^')

            for element in workers:
                worker, name= element
                '''print(f'checking {element}')'''
                
                if not worker.running():
                    if worker.exception():
                        print('oh snap! one of your threads had a problem.\n\n\n')
                        
                        print('******-----ERROR------******')
                        print(f"function: {name}")
                        print(worker.exception())
                        print('******-----ERROR------******\n\n\n')
                        workers.remove(element)
                    elif worker.done():
                        if verbose:
                            print(f'worker done {element}')
                        workers.remove(element)
                    else:
                        pass
                    #print(f'$$$$$$$$$$$$ currently {len(workers)} threads running via pool executor $$$$$$$$$$$$')
                
            time.sleep(0.025)
        
        time.sleep(1)
        print('done and exiting')
        while len(workers) > 0:
            for element in workers:
                worker, _, _ = element
                if not worker.done():
                    print(f'{element} still not done... you may need to force exit')
                else:
                    workers.remove(element)
            time.sleep(0.25)

    def reset(self):
        for lever in self.levers:
            lever.retract()
        for door in self.doors:
            door.close()

    def shutdown(self):
        self.done = True

    def finished(self):
        time.sleep(0.05)
        return self.done

        
class ComponentContainer:
    
    def __init__(self, component_type):
        '''do we need anything at init?'''
        self.type = component_type 
    
    
    def __iter__(self):
        '''override builtin iterator function to return a list
        of component objects to iterate over'''
        return iter(self.get_components())

    def get_component(self, name):
        '''return all contained objects'''
        obj_dict = self.__dict__
        return obj_dict[name]

    def get_components(self):
        '''return all contained objects'''
        obj_dict = self.__dict__
        return [value for _, value in obj_dict.items() if not isinstance(value, str)]
    
    def add_component(self, name, component_object):
            name = component_object.name
            if hasattr(self, name):
                raise NameError(f'box already has a >{self.type}< named >{name}<, but tried to make another with that name. Check for duplicate names in the config file')

            setattr(self, name, component_object)
        
        
class ScreenOutput:
    '''format and handle updating the output screen'''
    def __init__(self, box):
        self.box = box
