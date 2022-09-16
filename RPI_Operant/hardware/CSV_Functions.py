from datetime import datetime
import pandas as pd
import importlib
import os
from .software_functions import load_config_file
import yaml
import threading
import time
DATA_TYPES = {'vole':int, 
              'day':int, 
              'runtime':datetime, 
              'rounds_completed':int, 
              'script_path':str, 
              'setup_path':str}


def r_mkdir(path):
    if not os.path.isdir(path):
        print(f'not a path: {path}')
        head, tail = os.path.split(path)
        success = r_mkdir(head)
        if success:
            try:
                print(f'trying to make {path}')
                os.mkdir(path)
            except:
                return False
            else:
                return True
        else:
            return False
    else:
        return True
class Experiment:
    def __init__(self, file, output_loc = '~/default_operant_outputs') -> None:
        self.file = file
        self.file_temp = self.file.split('.csv')[0]+'_tmp.csv'
        self.table = pd.read_csv(file)
        
        #start at the first location that is not finished
        self.location = self.get_unfinished_index()
        
        
        self.current_row = self.table.iloc[self.location]
        
        '''vvvv should probably wrap this up in its own setup function?'''
        self.current_args = self.parse_args()
        self.runtime_dict = self.generate_runtime_dict()
        self.load_module()
        '''^^^^^^^^^'''
        
        self.check_skipped()
        
        
        
    def get_unfinished_index(self): 
        return self.table.loc[(self.table.finished != True) & (self.table.finished != 'True') &(self.table.finished != 'skipped') ].index.values[0]

    def parse_args(self):
        if pd.isna(self.current_row['args']):
            out = {}
        else:
            vals = self.current_row['args'].split('|')
            out = {}
            for v in vals:
                if ':' in v:
                    k, v = v.split(':')
                    v_interpreted = yaml.safe_load(v)
                    out[k.lower()] = v_interpreted
        return out
    
    def next_experiment(self):
        return self.iterate_row()
    
    def iterate_row(self):
        if  len(self.table.loc[self.table.finished != True]) == 0:
            print('out of unfinished rows to run')
            return False
        self.location = self.get_unfinished_index()
        self.current_row = self.table.iloc[self.location]
        self.current_args = self.parse_args()
        self.runtime_dict = self.generate_runtime_dict()
        self.load_module()
        self.check_setup_filepaths()
        return True
    
    def check_setup_filepaths(self):
        if not os.path.isfile(self.current_row.script_setup):
             print(f'WARNING: Experiment class received a path to software setup that does not point to a file:\n{self.current_row.script_setup}\n')
        if not os.path.isfile(self.current_row.hardware_setup):
             print(f'WARNING: Experiment class received a path to hardware setup that does not point to a file:\n{self.current_row.hardware_setup}\n')
    
    def load_module(self):
        #dynamically reload the module with the new vole info.
        if os.path.isfile(self.current_row['script_path']):
            print(self.current_row['script_path'])
            spec = importlib.util.spec_from_file_location('module', self.current_row['script_path'])
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)
            if self.module == None:
                raise ImportError(f"couldnt import module from path:\n{self.current_row['script_path']}")
        else:
            raise ImportError(f"script_path does not point to a file:\n{self.current_row['script_path']}")
        #check for paths to hardware or software setup files. else use default files
        if not pd.isna(self.current_row['script_setup']):
            self.module.USER_SOFTWARE_CONFIG_PATH = self.current_row.script_setup
        if not pd.isna(self.current_row['hardware_setup']):
            self.module.USER_HARDWARE_CONFIG_PATH = self.current_row.hardware_setup
        
        self.module.RUNTIME_DICT.update(self.runtime_dict)
    
    
    def generate_runtime_dict(self):
        #generate dict from keys that are important to pass along to the module
        keys = ['vole', 'vole_2','day', 'title', 'output_path']
        d = {k:self.current_row[k] for k in keys if k in list(self.current_row.keys())}
        print(f'provided output path is {d["output_path"]}')
        if pd.isna(d["output_path"]):
            d.pop('output_path')
        
        #update the runtime dict with any k:v pairs from the "args" column
        d.update(self.current_args)
        return d
    
    def ask_to_run(self):
        
        
        print(f'\n\n{self.module.RUNTIME_DICT}')
        print('\n\nshould we run this experiment?\ny (yes)\nn (no/exit)\ns (skip to next unfinished row)')
        
        resp = input('').lower()
        
        if resp == 'y':
            return True
        elif resp == 'n': 
            return False
        elif resp == 's':
            self.table.loc[self.table.index == self.location, 'finished'] = 'skipped'
            self.save_file()
            next_exists = self.iterate_row()
            if next_exists:
                return self.ask_to_run()
            else: 
                return False
        else:
            print('\n\n\nhmmm, not a valid response, (y/n). try again.')
            return self.ask_to_run()
        
    def check_skipped(self):
        if self.current_row.finished == 'skipped':
            user_input = 'n'
            while user_input == 'n':
                print(self.current_row)
                print('this row was previously skipped. would you like to run it now? \nrun now--> y\nskip --> n\nskip forever --> f')
                user_input = input().lower()
                if user_input == 'y':
                    return
                elif user_input == 'n':
                    print('skipping')
                    self.iterate_row()
                elif user_input == 'f':
                    self.table.loc[self.table.index == self.location].finished = 'True'
                    self.iterate_row()
                else:
                    print('input error, plese enter either y or n')
                    user_input = 'n'
                


    def check_output_location(self):
        
        config = load_config_file(self.current_row['script_setup'])
        if not config['output_path'] == 'default':
            
            if not os.path.isdir(config['output_path']):
                response = input(f'output path does not exist. Should I make:\n{config["output_path"]}"y" : recursively make dir.\n"n" : fall back to default output location\n')
                if response.lower == 'y':
                    success = r_mkdir(config["output_path"])
                    if not success:
                        print('couldnt make path! falling back to default path.')
                        
                elif response.lower == 'n':
                    print('ok, falling back to normal output.')
    
    
    def update_rounds(self, round_number):
        self.table.loc[self.table.index ==self.location, 'rounds_completed'] = round_number
        self.save_file()
    
    def save_file(self):

        self.table.to_csv(self.file_temp, index = False)
        if len(open(self.file_temp).readlines()) > 0:
            os.popen(f'cp "{self.file_temp}" "{self.file}"')
            os.popen(f'rm "{self.file_temp}"')
        else:
            print('\n\n\ error saving experiment status! check experiment CSV file \n\n')
    

    
    def experiment_finished(self):
        
        self.table.loc[self.table.index == self.location, 'finished'] = True
        self.save_file()
    
    def experiment_failed(self):
        
        self.table.loc[self.table.index == self.location, 'finished'] = False
        self.save_file()

    def run_module(self):
  
        date = datetime.now()
        fdate = '%s_%s_%s__%s_%s'%(date.month, date.day, date.year, date.hour, date.minute)
        self.table.loc[self.table.index ==self.location, 'runtime'] = fdate
        self.save_file()
        self.module.run()
        start = time.time()
        while not self.module.box.successfully_run() and start + 5 >  time.time():
                pass
        if self.module.box.successfully_run():
            self.experiment_finished()
        else:
            self.experiment_failed()
        
        