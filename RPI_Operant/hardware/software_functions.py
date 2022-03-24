from collections.abc import Mapping
import yaml

def load_config_file( file):
    '''load a config yaml file and return the resulting dict'''
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