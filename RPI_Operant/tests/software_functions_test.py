import sys, os 
sys.path.append(os.path.realpath(os.path.dirname(__file__)+"/.."))
from hardware import software_functions, box 


'''
-----------------------------------------------------
        tests for software_functions.py
            << PART THREE >> 
<< assumes that components and box have already been tested >> 
-----------------------------------------------------
'''

box = box.Box() 



'''
(TODO) Add a function in the file setup_for_testing.py that specifies the configurations for setting up a Box. 
        Then, create the box instance and call box.setup()
        Return box instance from this function. 
        At the start of each test, call this same setup function so we can ensure consistency between tests!
'''

'''
METHODS THAT ARE NOT IN CLASSES 
(TODO) General Tests \
    make calls to load_config_file(), merge_config_files(), and hierarchical_merge_dicts()\\
        after each of these calls, print the resulting dictionary
'''

'''
CLASS SCREEN PRINTER 
(TODO) General Tests\
    create box, pass to a new instance of ScreenPrinter\\
        in a loop, add random stuff to ScreenPrinter.print_queue  
    call update_display_list with random <obj> arguments
(TODO) Edge Cases
    add a bunch of stuff to ScreenPrinter.print_queue and then immediately set Box.finished=True    
'''





''' testing for methods and things in software_functions.py

load_config_file -- loads yaml and returns resulting dict 

merge_config_files -- returns hierarchical_merge_dict(old_config_dict, new_config_dict)

heirarchical_merge_dict(dict_default, dict_update) -- updates dictionary, overwriting values in dict_default with values from dict_update

'''

