from datetime import datetime
import pandas as pd
import importlib
import os
from RPI_Operant.hardware.software_functions import load_config_file
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
        self.unfinished_list_index = 0
        self.location = self.get_unfinished_index()
        
        
        self.current_row = self.table.iloc[self.location]
        self.check_skipped()
        
        
    def get_unfinished_index(self): 
        return self.table.loc[self.table.finished != 'True'].index[self.unfinished_list_index]

    def iterate_row(self):
        self.unfinished_list_index +=1
        self.location = self.get_unfinished_index()
        self.current_row = self.table.iloc[self.location]
        
    def run_row(self):
        #dynamically reload the module with the new vole info.
        if os.path.isfile(self.current_row['script_path'].values[0]):
            spec = importlib.util.spec_from_file_location(self.vals["script"],
                        f'{self.path_to_scripts}/{self.vals["script"]}.py')
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)
        
        #check for paths to hardware or software setup files. else use default files
        if not pd.isna(self.current_row.script_setup):
            self.module.USER_SOFTWARE_CONFIG_PATH = self.current_row.script_setup
        if not pd.isna(self.current_row.hardware_setup):
            self.module.USER_CONFIG_PATH = self.current_row.hardware_setup
        
        self.module.RUNTIME_DICT = self.generate_runtime_dict()
        
        self.module.run()
    
    
    def generate_runtime_dict(self):
        keys = ['vole', 'day', 'title']
        return {k:self.current_row[k] for k in keys if k in list(self.current_row.keys())}
    
    def ask_to_run(self):
        
        self.print_vals()
        print(self.current_setup_dictionary)
        print('\n\n\n\nshould we run this experiment?\ny (yes)\nn (no/exit)\ns (skip to next unfinished row)')
        
        resp = input('').lower()
        
        if resp == 'y':
            return True
        elif resp == 'n': 
            return False
        elif resp == 's':
            self.table.loc[self.table.index == self.location].finished = 'skipped'
            return self.ask_to_run()
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
                response = input(f'output path does not exist. Should I make:\n{config["output_path"]}"y" : recursively make dir.\n"n"fall back to default output location\n')
                if response.lower == 'y':
                    success = r_mkdir(config["output_path"])
                    if not success:
                        print('couldnt make path! falling back to default path.')
                        
                elif response.lower == 'n':
                    print('ok, falling back to normal output.')
                    