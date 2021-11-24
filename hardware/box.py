''' --------------------------------------------------------------------------------------------------------------------------------
                                                    filename: box.py
                description:  Box Class definition 
                - sets up the hardware components based on what the user specified to have setup in the configuration file 
                - if user does not pass the name of a file as an argument to Box instantiation, then the default configuration file is used. 
                                                
-----------------------------------------------------------------------------------------------------------------------------------'''

# Standard Library Imports 
import importlib.util

# Third Party Imports 
# Local Imports
'''from .lever import Lever 
from .door import Door 
from .button import Button
from .dispenser import Dispenser 
from .beam import Beam 
from .output import Output'''
import os
from hardware.components import Lever, Door, Button, Dispenser
from hardware.timing import Phase, TimestampManager


# Constants 
DEFAULT_CONFIG = os.path.join(os.getcwd(), 'hardware/default.yaml')


class Box: 

    def __init__(self, config_file=None): 
        
        # timestamp queue that gets setup by ScriptManager
        self.timestamp_manager = TimestampManager()
        
        # set file containing the box components we would like to get setup 
        self.config = config_file if config_file else DEFAULT_CONFIG
        self.config_name = self.config.split(sep='/')[-1].replace('.py','')

        # get setup info from config file 
        spec = importlib.util.spec_from_file_location(self.config_name, self.config)
        self.config_module = importlib.util.module_from_spec(spec)
        
        self.default_config_name = self.config.split(sep='/')[-1].replace('.py','')
        spec = importlib.util.spec_from_file_location(self.config_name, self.config)
        self.config_module = importlib.util.module_from_spec(spec)
        
        spec.loader.exec_module(self.config_module)



        '''###############
        for lever_dict in self.config_module.levers:
            self.levers = ComponentContainer('lever')
            # get buttons connected with door 
            for lever_dict in self.config_module.levers:
                 
                self.doors.add_component(Lever(lever_dict))'''


        ###############
        for door_dict in self.config_module.doors:
            self.doors = ComponentContainer('door')


            # get buttons connected with door 
            for door_dict in self.config_module.doors:
                
                self.doors.add_component(Door(door_dict, self))
            
        
        '''        ###############
        for button in self.config_module.buttons: 
            
            new_button = Button(button, self.timestamp_manager)

            door_name = new_button.door 
            door = getattr(self, door_name) # get door object 

            function = new_button.function 
            # name = (f'{function}_{door_name}_button')
            name = (f'{function}_button')

            if hasattr(door,name): 
                    raise NameError(f'{door_name} already contains a {name} attribute, but tried to make a button with that name. Check for duplicate names in the config file')

            self.object_list.append(new_button)
            setattr(door, name, new_button)

        ###############
        for dispenser_dict in self.config_module.dispensers:
            self.dispensers = ComponentContainer('dispenser')
            # get buttons connected with door 
            for dispenser_dict in self.config_module.dispensers:
                 
                self.doors.add_component(Dispenser(door_dict))


        ###############
        for beam in self.config_module.beams:
            new_beam = Beam(beam)
            
            name = new_beam.name
            
            if hasattr(self, name):
                raise NameError(f'box already has {name} attribute, but tried to make a beam with that name. Check for duplicate names in the config file')
            
            setattr(self, new_beam.name, new_beam)


        ###############
        for output in self.config_module.outputs:
            new_output = Output(output, self.timestamp_manager)
            
            name = new_output.name
            
            if hasattr(self, name):
                raise NameError(f'box already has {name} attribute, but tried to make an output with that name. Check for duplicate names in the config file')
            
            self.object_list.append(new_output)
            setattr(self, new_output.name, new_output)
            
        
        ###############'''


        

class ComponentContainer:
    
    def __init__(self, component_type):
        '''do we need anything at init?'''
        self.type = component_type 
        
    def get_components(self):
        '''return all contained objects'''
        obj_dict = self.__dict__
        return [obj_dict[key] for key in obj_dict.keys()]
    
    def add_component(self, component_object):
            name = component_object.name
            if hasattr(self, name):
                raise NameError(f'box already has a >{self.type}< named >{name}<, but tried to make another with that name. Check for duplicate names in the config file')

            setattr(self, name, component_object)
        
        


