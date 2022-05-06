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

import os
import traceback

from RPI_Operant.hardware.components import Button, Lever, Door, ButtonManager, Dispenser, Speaker, PositionalDispenser, PortDispenser

from RPI_Operant.hardware.timing import TimeManager, TimestampManager
from concurrent.futures import ThreadPoolExecutor
import queue
import time
import datetime
from RPI_Operant.hardware.software_functions import merge_config_files, load_config_file

# Constants 
DEFAULT_HARDWARE_CONFIG = os.path.join(os.getcwd(), 'RPI_Operant/default_setup_files/default_hardware.yaml')
DEFAULT_SOFTWARE_CONFIG = os.path.join(os.getcwd(), 'RPI_Operant/default_setup_files/default_software.yaml')
DEFAULT_OUTPUT_LOCATION = os.path.join(os.getcwd(), 'RPI_Operant/default_output_location')
ERROR_LOG_PATH = os.path.join(os.getcwd(), 'RPI_Operant/default_output_location/error_logs/')
COMPONENT_LOOKUP = {
                    'doors':{'component_class':Door, 'label':'door'},
                    'levers':{'component_class':Lever, 'label':'lever'},
                    'buttons':{'component_class':ButtonManager.new_button, 'label':'button'},
                    'dispensers':{'component_class':Dispenser, 'label':'dispenser'},
                    'positional_dispensers':{'component_class':PositionalDispenser, 'label':'positional_dispenser'},
                    'port_dispensers':{'component_class':PortDispenser, 'label':'port_dispenser'},
                    'speakers':{'component_class':Speaker, 'label':'speaker'}
                    }



class Box: 
    def __init__(self):
        ''''''
        self.setup_complete = False

    def setup(self, run_dict = {'vole':000, 'day':1, 'experiment':'none'}, user_hardware_config_file_path=None, 
                 user_software_config_file_path = None, 
                 start_now = True, simulated = False): 
        
        #threading        
        self.thread_executor = ThreadPoolExecutor(max_workers = 20)
        self.worker_queue = queue.Queue()
        
        self.done = False
        self.completed = False
        self.run_dict = run_dict
        
        ###### load and merge config files
        if user_hardware_config_file_path:
            self.config = load_config_file(user_hardware_config_file_path)
        else:
            self.config = load_config_file(DEFAULT_HARDWARE_CONFIG)
        
        if user_software_config_file_path:
            self.software_config = load_config_file(user_software_config_file_path)
        else:
            self.software_config = load_config_file(DEFAULT_SOFTWARE_CONFIG)

        
        
        #self.timing is in charge tracking start time, making new timeouts, latencies, etc
        self.timing = TimeManager(self)

        #### timestamp queue that gets setup by ScriptManager
        self.timestamp_manager = TimestampManager(timing_obj = self.timing, 
                                                  save_timestamps= self.software_config['checks']['save_timestamps'],
                                                  box = self)

        self.output_file_name = self.generate_output_fname()
        self.output_file_path = self.generate_output_path()
        self.output_error_file_path = self.generate_error_output_path()

        #the manager for creating, adding, and monitoring new binary inputs
        self.button_manager = ButtonManager(self, simulated = simulated)

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
                component = component_class(name, comp_dict, self, simulated = simulated)
                comp_container.add_component(name, component)
            
            #add completed components (within component container) to the box
            setattr(self, component_group_name, comp_container)

        #VVVVVVVVVVVVVVVV wanted to simplify this call elsewhere as box.speaker.click_on etc etc
        if len(self.speakers) ==1:
            self.speaker = self.speakers.get_components()[0]
        
        #^^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


        self.monitor_worker_future = self.thread_executor.submit(self.monitor_workers, verbose = True)
        
        #startup queue monitoring
        fut2 = self.thread_executor.submit(self.timestamp_manager.monitor_queue)
        self.worker_queue.put((fut2,'timestamp monitor_queue'))
        if not self.monitor_worker_future.running:
            if self.monitor_worker_future.exception():
                print(self.monitor_worker_future.exception())

        if start_now:
            self.timing.start_timing()
        self.setup_complete = True
    
    def generate_output_fname(self):
        vole = self.run_dict['vole']
        day = self.run_dict['day']
        exp = self.run_dict['experiment']
        date = datetime.datetime.now()
        if 'vole_2' in self.run_dict.keys():
            vole_2 = self.run_dict['vole_2']
            fdate = f'{date.month}_{date.day}_{date.year}___{date.hour}_{date.minute}_'
            fname = f'{vole}_{vole_2}_{fdate}_{exp}_day_{day}'
        else:
            fdate = f'{date.month}_{date.day}_{date.year}___{date.hour}_{date.minute}_'
            fname = f'{vole}_{fdate}_{exp}_day_{day}'
        
        return fname
        
    
    def generate_output_path(self):
        if self.software_config['output_path'].lower() == 'default':
            
            path =  DEFAULT_OUTPUT_LOCATION
            
        else:
            path = self.software_config['output_path']
            
        if not os.path.isdir(path):
            print(f'cant save to path provided! {path}')
            if self.software_config['output_path'].lower() == 'default':
                print('already on default location')
            else:
                print('falling back to default save path')
                path = DEFAULT_OUTPUT_LOCATION
                if not os.path.isdir(path):
                    print(f'cant save to default path! {path}')
        return os.path.join(path, self.output_file_name)
    
    
    def generate_error_output_path(self):
        if self.software_config['output_path'].lower() == 'default':
            
            path =  ERROR_LOG_PATH
            
        else:
            path = self.software_config['output_path']
            
        if not os.path.isdir(path):
            print(f'cant save to path provided! {path}')
            if self.software_config['output_path'].lower() == 'default':
                print('already on default location')
            else:
                print('falling back to default save path')
                path = DEFAULT_OUTPUT_LOCATION
                if not os.path.isdir(path):
                    print(f'cant save to default path! {path}')
        return os.path.join(path, self.output_file_name+'errors.txt')
    
    
    def new_round(self):
        self.timing.new_round()
        self.timestamp_manager.create_and_submit_new_timestamp()
        

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
        
        
        print(f'error_log_path: {self.output_error_file_path}')
        with open(self.output_error_file_path, 'w') as f:
            print('creating log file')
        
        while not self.done:
            if not self.worker_queue.empty():
                #receive worker, parent function, round of initiation
                worker_and_info = self.worker_queue.get()
                if verbose:
                    ''''''
                    #print(f'worker queue received worker {worker_and_info}')
                #if we have an identically named worker, we will need to modify this tuple
                
                workers += [worker_and_info]
                
                '''print('\nvvvvvvvvvvvvvvvvvv')
                print(f'currently {len(workers)} threads running via pool executor')
                print(workers)
                print('\n\n^^^^^^^^^^^^^^^')'''

            for element in workers:
                worker, name= element
                '''print(f'checking {element}')'''
                
                if not worker.running():
                    if worker.exception():
                        print('oh snap! one of your threads had a problem.\n\n\n')
                        
                        print('******-----ERROR------******')
                        print(f"function: {name}\n{worker.exception()}\n")
                        with open(self.output_error_file_path, 'a') as f:
                            try: 
                                worker.result()
                            except:
                                f.write(traceback.format_exc())
                        
                        print('******-----ERROR------******\n\n\n')
                        workers.remove(element)
                    elif worker.done():
                        if verbose:
                            '''print(f'worker done {element}')'''
                        workers.remove(element)
                    else:
                        pass
                    #print(f'$$$$$$$$$$$$ currently {len(workers)} threads running via pool executor $$$$$$$$$$$$')
                
            time.sleep(0.025)
        
        time.sleep(1)
        print('done and exiting')
        print(f'currently {len(workers)} threads running via pool executor')
        print(workers)
        while len(workers) > 0:
            for element in workers:
                worker, _, _ = element
                if not worker.done():
                    print(f'{element} still not done... you may need to force exit')
                else:
                    print(f'shutting down, removing {element}')
                    workers.remove(element)
            time.sleep(0.25)
        print('worker queue empty')

    def reset(self):
        if 'levers' in self.__dict__.keys():
            for lever in self.levers:
                lever.retract()
        if 'doors' in self.__dict__.keys():
            for door in self.doors:
                door.close()

    def shutdown(self):
        
        if not self.timing.current_phase == None:
            self.timing.current_phase.end_phase()
        self.done = True
        
        val = 0
        while not self.monitor_worker_future.done():
            time.sleep(0.05)
            val +=1
            if val>500:
                print('waiting for shutdown')
                val = 0
        
        for l in self.levers:
            l.retract()
        for speaker in self.speakers:
            speaker.set_off()
        
        print('monitor_workers complete')
        self.completed = True
        
    def finished(self):
        time.sleep(0.05)
        return self.done
    
    def successfully_run(self):
        time.sleep(0.05)
        return self.completed
    
    def abort_run(self):
        
        if not self.timing.current_phase == None:
            self.timing.current_phase.end_phase()
        self.done = True
        
        val = 0
        while not self.monitor_worker_future.done():
            time.sleep(0.05)
            val +=1
            if val>500:
                print('waiting for shutdown')
                val = 0
        
        for l in self.levers:
            l.retract()
        for speaker in self.speakers:
            speaker.set_off()
        
        print('monitor_workers complete')
        

        
class ComponentContainer:
    
    def __init__(self, component_type):
        '''do we need anything at init?'''
        self.type = component_type 
    
    
    def __iter__(self):
        '''override builtin iterator function to return a list
        of component objects to iterate over'''
        self.__comps = iter(self.get_components())
        return self
    def __next__(self):
        return next(self.__comps)
    
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
            
    def __len__(self):
        return len(self.get_components())
        
