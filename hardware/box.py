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
from components import Lever, Door, Button, Dispenser, Beam, Output



# Constants 
DEFAULT_CONFIG = 'class_definitions/hardware_classes/operant_cage_settings_default.py'


class Box: 

    def __init__(self, timestamp_manager, config_file=None): 
        
        # timestamp queue that gets setup by ScriptManager
        self.timestamp_manager = timestamp_manager

        # set file containing the box components we would like to get setup 
        self.config = config_file if config_file else DEFAULT_CONFIG
        self.config_name = self.config.split(sep='/')[-1].replace('.py','')

        # get setup info from config file 
        spec = importlib.util.spec_from_file_location(self.config_name, self.config)
        self.config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.config_module)



        ###############
        for lever in self.config_module.levers:
            new_lever = Lever(lever, self.timestamp_manager)
            
            name = new_lever.name+'_lever'
            if hasattr(self, name):
                raise NameError(f'box already has {name} attribute, but tried to make a lever with that name. Check for duplicate names in the config file')
            
            self.object_list.append(new_lever)
            setattr(self, name, new_lever)


        ###############
        for door in self.config_module.doors:

            # get buttons connected with door 
            button_dict = {}
            for button in self.config_module.buttons: 
                if button['name'] == door['name']: 
                    new_button = Button(button, self.timestamp_manager)
                    button_dict[new_button.function] = new_button
            new_door = Door(door, button_dict, self.timestamp_manager)
            
            name = new_door.name
            if hasattr(self, name):
                raise NameError(f'box already has {name} attribute, but tried to make a door with that name. Check for duplicate names in the config file')

            self.object_list.append(new_door)
            setattr(self, new_door.name, new_door)
        
        
        ###############
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
        for dispenser in self.config_module.dispensers:
            new_dispenser = Dispenser(dispenser, self.timestamp_manager)
            
            name = new_dispenser.name
            
            if hasattr(self, name):
                raise NameError(f'box already has {name} attribute, but tried to make a dispenser with that name. Check for duplicate names in the config file')
            
            self.object_list.append(new_dispenser)
            setattr(self, name, new_dispenser)


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
            
        
        ###############

        

        
    
        


