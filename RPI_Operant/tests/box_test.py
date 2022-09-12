import sys, os 
sys.path.append(os.path.realpath(os.path.dirname(__file__)+"/.."))
from hardware import box 
from hardware.box import COMPONENT_LOOKUP, Box



'''
------------------------------------------------------
            tests for box.py
             << PART TWO >> 
<< this builds upon components.py, so when building tests, ideally 
classes in components.py should have already been tested individually >> 
------------------------------------------------------
'''


''' 
CLASS COMPONENT CONTAINER 
(class ComponentContainer)
(TODO) Hardware Tests\
    instantiate a couple instances of different components (reference the classes in components.py (e.g. door / lever / dispenser))
    create new instance of component container. 
    Test adding components to the container:\
        for new_component in new_component_list: container.add_component(new_component)
    Test retrieving components from the container:\
        single_component = container.get_component(specific_component_name)
        all_components = container.get_components()
    Test retrieving/using a component by directly accessing the attribute that was created (by the setattr() call in add_component)
(TODO) Edge Cases \
    try to add the same component to a componet_container twice 
    call get_component on a component that does not exist 
    try to add_component with a nonexistent/unknown component_object as the argument
'''

def test_component_creation_manually(): 
    '''
    test component adding and retrieval here 
    '''

def test_component_container_edge_cases(): 
    '''
    since we want this function to be causing errors, test should be a series of try/catch statements that attempts the task & prints the error if there is one
    '''

'''
CLASS BOX
(if using unittest library, this website has helpful explanations for how to test for threads that may be left running => https://pythonhosted.org/tl.testing/tl.testing-thread.html )

(TODO) Setup Box, No Simulations \
    create new box instance and call box.setup
    test basic methods in isolation: \
        box.get_component() ==> try retrieving a few diff components 
        box.shutdown() 
        box.reset() 
        box.abort_run()
    test early interrupt ==> ensure nothing gets left running (threads and hardware)

(TODO) Setup Box, With Simualtions \
    create new box instance with argument simulated set to True 
    test basic methods in isolation: \
        box.get_component() 
        box.shutdown() 
        box.reset() 
        box.abort_run() 
    test early interrupt ==> ensure no threads are left running

(TODO) Edge Cases \
    Change the configuration dictionaries so they hold some incorrect information, and then setup the Box => ensure that these errors are caught and the user is somehow notified of which configuration file holds an incorrect value. \\
        Also make sure that these errors are correctly written to the Error Logging File! 

    If this is a feature that you want to add to the Box class... alter box setup to allow for some some simulated components and some non-simulated components. Then test general functions (get_component,shutdown,reset,abort_run) for this box.
'''

def test_setup(): 
    '''
    check completeness of the box setup() method
    '''
    box = Box()
    box.setup() 
    print(vars(box)) # print the attributes that were added by setup() call

def test_setup_with_sim(): 
    '''
    check completeness of box setup() method when simulation = True 
    '''
    box = Box(simulated=True)
    box.setup() 
    print(vars(box))

def test_faulty_setup(): 
    '''
    EDGE CASES! (try/catch statements for each of the tasks) 
    try to cause errors by putting weird data into a config file? Leave diff columns empty? etc. 
    try to setup a hardware object with an unknown type 
    try to setup a hardware object with a duplicated name 
    specify a configuration filepath or filename that does not exist during setup 
    after running a faulty setup, check that the error logging file contains error messages! 
    '''

def test_early_interrupt(): 
    '''
    setup box and send a keyboard interrupt
    '''




