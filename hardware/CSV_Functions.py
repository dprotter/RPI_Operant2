from datetime import datetime
import pandas as pd
import importlib
'''todo
where to check if next unfinished index exists or not


'''
DATA_TYPES = {'vole':int, 
              'day':int, 
              'runtime':datetime, 
              'rounds_completed':int, 
              'script_path':str, 
              'setup_path':str}

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
        return self.table.loc[self.experiment_status.done != 'True'].index[self.unfinished_list_index]

    def iterate_row(self):
        self.unfinished_list_index +=1
        self.location = self.get_unfinished_index()
        self.current_row = self.table.iloc[self.location]
        
    def run_row(self):
        #dynamically reload the module with the new vole info.
        spec = importlib.util.spec_from_file_location(self.vals["script"],
                    f'{self.path_to_scripts}/{self.vals["script"]}.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.module.load_setup(self.current_row.setup_path)
        self.module.run()
        
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
                print('this row was previously skipped. would you like to run it now? \nrun now--> y\nskip --> n')
                user_input = input().lower()
                if user_input == 'y':
                    return
                elif user_input == 'n':
                    print('skipping')
                    self.iterate_row()
                else:
                    print('input error, plese enter either y or n')
                    user_input = 'n'
                
                    
                    