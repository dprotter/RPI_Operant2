import sys, os, time, random


# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.abspath(__file__))
# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)
# adding the parent directory to 
# the sys.path.
sys.path.append(parent)
print(parent)

from hardware.box import Box
box=Box()


def run():
    
    box.setup(simulated = True) # setting up a simulated box!

    print('box setup complete') 

    for i in range(3): 

        box.timing.new_round()
        
        print('New Phase, new Pattern')
        phase = box.timing.new_phase(f'test_{i+1}', length =30) # iterate thru phases 

        laser1_pattern = box.lasers.laser1.patterns[i]

        # iterate both phase and laser pattern 

        while phase.active(): 
   
            reward = box.timing.new_phase(name = f'{box.lasers.laser1.name}, {laser1_pattern.name}', length=laser1_pattern.total_time)

            laser1_pattern.trigger() # turns on laser 1, pattern i
            
            phase.end_phase()
    

        
    

    box.shutdown() 

    return 
    


if __name__ == '__main__':
    run()