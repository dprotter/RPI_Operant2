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
'''from .lever import Lever 
from .door import Door 
from .button import Button
from .dispenser import Dispenser 
from .beam import Beam 
from .output import Output'''
import os
from hardware.components import Button, Lever, Door, ButtonManager, Dispenser
from hardware.timing import Phase, TimestampManager
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
import yaml
import queue
import time

# Constants 
DEFAULT_CONFIG = os.path.join(os.getcwd(), 'hardware/default.yaml')

COMPONENT_LOOKUP = {
                    'doors':{'component_class':Door, 'label':'door'},
                    'levers':{'component_class':Lever, 'label':'lever'},
                    'buttons':{'component_class':ButtonManager.new_button, 'label':'button'},
                    'dispenser':{'component_class':Dispenser, 'label':'dispenser'},
                    }



class Box: 

    def __init__(self, user_config_file_path=None): 
        GPIO.setmode(GPIO.BCM)
        # timestamp queue that gets setup by ScriptManager
        self.timestamp_manager = TimestampManager()
        self.timestamp_q = self.timestamp_manager.queue

        #threading        
        self.thread_executor = ThreadPoolExecutor(max_workers = 6)
        self.worker_queue = queue.Queue()

        #the manager for creating, adding, and monitoring new binary inputs
        self.button_manager = ButtonManager()

        # load and merge config files
        self.config_file_path = DEFAULT_CONFIG
        self.config_dict = self.load_config_file(self.config_file_path)
        if user_config_file_path:
            self.config_dict = self.merge_config_files(user_config_file_path)

        
        ###############

        #iterate across groups (IE doors, levers, etc etc)
        #lookup class object (ie Door() ) and label (ie "door")
        for component_group_name, group_dict in self.config_dict.items():
            
            #create a new container to put components within
            label = COMPONENT_LOOKUP[component_group_name]['label']
            comp_container = ComponentContainer(label)

            #iterate across all components in this class and use their dicts to instantiate a new 
            #component object
            component_class = COMPONENT_LOOKUP[component_group_name]['component_class']
            for name, comp_dict in group_dict.items():
                print(f'adding {name} to {component_class}')
                component = component_class(name, comp_dict, self)
                comp_container.add_component(name, component)
            
            setattr(self, component_group_name, comp_container)

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
        start = time.time()
        if isinstance(worker, list):
            print(f'waiting for one of the workers assigned to function "{func_name}"')
            while not any([w.done() for w in worker]):
                '''waiting for threads to finish'''
                time.sleep(0.025)

        else:
            print(f'waiting for function "{func_name}"')
            while not worker.done():
                time.sleep(0.025)
        done = time.time()
        print(f'"{func_name}" complete at {done - self.start_time} in {done - start}')

            

class ComponentContainer:
    
    def __init__(self, component_type):
        '''do we need anything at init?'''
        self.type = component_type 
    
    def get_component(self, name):
        '''return all contained objects'''
        obj_dict = self.__dict__
        return obj_dict[name]

    def get_components(self):
        '''return all contained objects'''
        obj_dict = self.__dict__
        return [obj_dict[key] for key in obj_dict.keys()]
    
    def add_component(self, name, component_object):
            name = component_object.name
            if hasattr(self, name):
                raise NameError(f'box already has a >{self.type}< named >{name}<, but tried to make another with that name. Check for duplicate names in the config file')

            setattr(self, name, component_object)
        
        


