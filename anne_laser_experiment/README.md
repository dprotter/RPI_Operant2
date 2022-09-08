Terminal Commands
------

*for all of these commands, ensure that you are positioned in the RPI_Operant2 directory* 


command to run experiment(s) that are specified by the csv file lasers_csv_mac.csv: 
~~~
python3 -m RPI_Operant.launcher -i 'anne_laser_experiment/lasers_csv_mac.csv'
~~~

commands to run hardware tests: 
~~~
python3 -m RPI_Operant.default_scripts.calibrate_lasers
python3 -m RPI_Operant.default_scripts.calibrate_levers
python3 -m RPI_Operant.default_scripts.calibrate_dispenser
python3 -m RPI_Operant.default_scripts.show_outputs
~~~


**notes on Laser Script Syntax when writing new scripts**
- to iterate thru every laser pattern, loop thru any laser object's pattern list ( e.g. for pattern in box.lasers.laser1.patterns )
- to add logic for when we should trigger playing a certain pattern, we can use the phase functionality ( like while phase.active, check for a certain condition that if met will cause us to exit from the phase early and enter a new phase)