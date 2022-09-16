from collections.abc import Mapping
import yaml
import queue
from .components import thread_it

def load_config_file(file):
    '''load a config yaml file and return the resulting dict'''
    print(f'loading {file}')
    with open(file, 'r') as f:
        config_dict = yaml.safe_load(f)
    return config_dict

def merge_config_files(new_config_file, old_config_file):
    new_config_dict = load_config_file(new_config_file)
    old_config_dict = load_config_file(old_config_file)
    return heirarchical_merge_dict(old_config_dict, new_config_dict)
    

def heirarchical_merge_dict(dict_default, dict_update):
    '''heirarchical update a dictionary, overwriting values in dict_default with values from dict_update'''
    for key, value in dict_update.items():
        if isinstance(value, Mapping):
            #note to self the get(key,{}) returns an empty list if the key is not found. good technique for avoiding KeyErrors
            dict_default[key] = heirarchical_merge_dict(dict_default.get(key,{}), value)
        else:
            dict_default[key] = value
    return dict_default

class ScreenPrinter:
    
    def __init__(self, box):
        self.print_queue = queue.Queue()
        self.display_list = ['-','-','-','-']
        self.box = box
        
    
    def format_line(self, obj):
        
        if 'latency' in obj.__dict__.keys():
            return f'{obj.round},  {obj.event_descriptor}, {obj.timestamp}, lat: {obj.latency}'
        else:
            return f'{obj.round},  {obj.event_descriptor}, {obj.timestamp}, lat: ___'
    
    @thread_it
    def print_output(self):
        
        '''while not self.box.finished():
            if not self.print_queue.empty():
                self.update_display_list(self.print_queue.get())
            print(self.display_list)'''
        while not self.box.finished():
            if not self.print_queue.empty():
                ob = self.print_queue.get()
                if ob.print_to_screen:
                    print(self.format_line(ob))
                    print()
            else:
                cd=self.format_phase_countdown()
                if cd:
                    print(' '*20, end = '\r')
                    print(cd, end = '\r')
                
    def format_phase_countdown(self):
        string = ''
        if len(self.box.timing.get_countdowns())>0:
            for obj in self.box.timing.get_countdowns():
                    string+=f'{obj.name}: {obj.get_time_remaining()}     '
            return string 
        else:
            return None
        
    def update_display_list(self, obj):
        self.display_list.append(obj)
        _ = self.display_list.pop(0)
    
    def format(self):
        ''''''
        output = '\n-------\n********\n'
        for obj in self.display_list:
            output+=self.format_line(obj)+'\n'
        output += '********\n-------\n'
        
