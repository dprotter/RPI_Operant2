import sys, os
from RPI_Operant2_Testing.RPI_Operant2.RPI_Operant.hardware.timing import TimeManager, TimestampManager
sys.path.append(os.path.realpath(os.path.dirname(__file__)+"/.."))

from hardware import box 
from hardware import components



'''
-----------------------------------------------
        tests for components.py
            << PART ONE >> 
<< run these tests before everything else!! >> 
-----------------------------------------------
'''

'''
SERVOS + Class Servo_Sim
(TODO) Hardware Tests \
    import adafruit_servokit.ServoKit 
    call get_servo() 
(TODO) Simulation Tests \
    create dictionary containing the servo specs with servo_type=positional and call new_fake_servo()
    create dictioanry containing the servo specs with servo_type=continuous and call new_fake_servo()
    Reuse These Throughout Tests Below! 
'''


'''
Class Button + Class ButtonManager

(TODO) Create a Box Instance that we can pass to Button for testing ( Do Not Call Setup )

(TODO) Hardware Tests \
    setup Button, call watch_buttons() \\
        - physically press button to ensure that it properly works 
        - press button a bunch of times in a row 
        - make a singular, long press
    setup 2+ Buttons, call watch_buttons() on all buttons and physically press buttons to ensure that everything works with multiple buttons running
(TODO) Sim Tests \
    setup simulated Button \\
        call watch_buttons_sim() on the button 
        in test script, manually simulate a button press occurrence 
(TODO) Edge Cases \
    setup 1 simulated and 1 real button, and all watch_buttons() on one and watch_buttons_sim() on the other \\
        in test script, manually simulate a button press 
        physically make a button press around the time of the simulated button press occurrence
'''




'''
(TODO) Box Setup without calling box.setup() 
    manually set box attributes that are needed for setting up the other components \
        Attributes accessed by the components: \\
            done, button_manager, timing, timestamp_manager
'''
def box_setup(): 
    ''' Reuse this throughout tests! Make sure to call function each time so tests are consistent, and each recieve a newly created Box class '''
    box = box.Box() 
    box.done = False 
    box.button_manager = components.ButtonManager(box, simulated=False)
    box.timing = TimeManager()
    box.timestamp_manager = TimestampManager(timing_obj = box.timing, 
                                                  save_timestamps= box.software_config['checks']['save_timestamps'],
                                                  box = box)



'''
Class Lever 
    (TODO) call box_setup() to retrieve box instance
    (TODO) Hardware Tests \
        create lever which sets up with actual servo and actual button 
        test following function calls for the lever, and make sure that hardware components pick up on presses: \
            lever.wait_for_n_presses() 
            lever.monitor_lever() 
            lever.reset_lever()
    (TODO) Sim Tests \
        create lever which sets up with simulated servo 
        create lever which sets up with simulated button
        test following function calls for the simualted lever. \
            lever.wait_for_n_presses() 
            lever.monitor_lever() 
            lever.simulate_lever_press() 
            lever.reset_lever() 
    (TODO) Edge Case Tests \
        create a non-simulated lever and call the simulate_lever_press() function on the lever 
'''

food_lever_dict = { 'servo':4, 'extended':30, 'retracted':30, 'pin':19, 'pullup_pulldown':'pullup', 'servo_type':'positional', 
        'target_name':'positional_dispenser_1', 'target_type':'positional_dispenser' } 

def test_lever_hardware(): 
    lever = components.Lever('food_lever', food_lever_dict, box, simulated = False)

def test_lever_sim(): 
    simLever = components.Lever('food_lever', food_lever_dict, box, simulated = True)




'''
class Door
    (TODO) call box_setup() to retrieve box instance

    (TODO) Hardware Tests \
        - create door which sets up with an acutal servo and button 
        test the following functions, and make sure that the physical door moves/reacts as expected throughout: \
            door.open() 
            door.close() 
            door.override() 
        - after testing the override() function with a direct call to override(), test the override buttons by physically pressing the buttons 
        - Early Interrupt Test: test that servos shut off correctly in the case of an early interrupt
    (TODO) Sim Tests \
        create door which sets up with simulated servo and button 
        test the following methods in isolation \
            door.simulate_open() 
            door.is_open() 
            door.simualte_closed() 
            door.is_closed() 
            door.override() --> should this work for a simulated door?
    (TODO) Edge Cases \
        create a door with simulated servo and button 
        Ensure that Errors are Caught If Call gets made to non-simualted functions (potentially redirect to the simulated version of the function? ): \
            simDoor.open() 
            simDoor.close() 
'''



'''
class Dispenser
    (TODO) call box_setup() to retrieve box instance

    (TODO) Hardware Tests \
        - create dispenser and test its basic methods
        test the following methods in isolation \
            dispenser.dispense() 
            dispenser.monitor_pellet() 
        - early interrupt test; make sure that dispenser servo does not get left running if interrupted in the middle of a dispense() function call
    (TODO) Simulation Tests \
        - create dispenser w/ simulated features 
        test the following methods in isolation \
            dispenser.monitor_pellet() 
            dispenser.simulate_dispense() 
            dispenser.simualte_pellet_retrieved() 
    (TODO) Edge Cases \
        Ensure that Simulation & Hardware Features Work Together 
        - setup actual dispenser \
            make call to dispenser.monitor_pellet() 
            make call to dispenser.simulate_dispense()
            make call to dispenser.simulate_pellet_retrieved()
        - setup simulated dispenser \
            make call to dispenser.dispense() ==> should cause some kinda Error Message since we are calling hardware function on simulated dispenser. 
'''




'''
class PositionalDispenser
    (TODO) Hardware Tests \
        create positional dispenser and test its basic methods in isolation
        methods to test: \
            dispense() 
            monitor_pellet() 
        early interrupt test: Make sure that nothing gets left running in the case of early random exit from the program.

    (TODO) Simulated Tests \
        create simulate positional dispenser and test important methods in isolation \
            simulate_dispensed() 
            simulate_pellet_retrieved()

    (TODO) Edge Cases\
        Ensure that Simulation & Hardware Features Work Together 
        - setup actual positional dispenser \
            make call to simulate_dispense() & simulate_pellet_retrieved() 
        - setup simulated positional dispenser \
            make call to dispense() => handle error/display error message 
'''




'''
class PortDispenser(Dispenser)
    (TODO) --> Same Tests As Dispenser! 
'''



'''
class Beam
    (TODO) Hardware Tests \
        create actual Beam 
    (TODO) Simulated Tests \
        create beam with simulated button 

'''




'''
class Speaker + class Tone + class ToneTrain(Tone)
    (TODO) Hardware Tests \
        create actual speaker
        test tone features using the speaker object \
            tone = speaker.new_tone() 
            tone.get_hz 
        test ToneTrain features using the speaker object \
            tonetrain = ToneTrain() 
            tonetrain.add_tone() 
            tonetrain.get_hz() 
            tonetrain.check_tone_list() 
        Test Speaker Methods 
        Early Interrupt Test --> Ensure that speakers are not left playing sounds. 
    (TODO) Simulated Tests \
        create simulated speaker 
        Test speaker methods 
    (TODO) Edge Cases \


    (TODO) Now that all components, including Speaker, have been tested on its own, repeat the setup of components and pass in a Speaker_dict so classes that 
    utilize a speaker will setup and use an instance of the Speaker class \
        in the function box_setup, add a line which will add the additional attribute of a speaker \
            box.speaker = Speaker()
        then rerun the tests for the other component now that the box class will include a Speaker!
''' 