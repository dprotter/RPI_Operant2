# RPI_Operant2

My Commands for running basic tests/scripts
------

*for all of these commands, ensure that you are positioned in the RPI_Operant2 directory* 


run a set of scripts by pointing the launcher to a csv file: 
~~~
python3 -m RPI_Operant.launcher -i '/home/pi/RPI_Operant2/RPI_Operant/example_csv_mac.csv'
~~~

commands to run hardware tests: 
~~~
python3 -m RPI_Operant.default_scripts.calibrate_lasers
python3 -m RPI_Operant.default_scripts.calibrate_levers
python3 -m RPI_Operant.default_scripts.calibrate_dispenser
python3 -m RPI_Operant.default_scripts.show_outputs
~~~

CSV File Inputs
------
Fill out the CSV file with values that will direct the launcher to the script you want to run and what hardware/software configurations should be used when running that script.

**script_path** contains the filepath to the directory with the scripts to run 
~~~
/home/pi/anne_experiment/script_files/file_name.py
~~~

**script_setup** contains the filepath to the yaml file that specifies the *software* configurations. **hardware_setup** contains the filepath to the yaml file that specifies the *hardware* configurations. The filepath to the directory containing the setup files is: 
~~~
/home/pi/anne_experiment/yaml_setup_files/file_name.yaml
~~~

**output_path** contains the path to a directory where the experiments output data should get written 
~~~
/home/pi/anne_experiment/outputs
~~~






**notes on Laser Script Syntax when writing new scripts**
- to iterate thru every laser pattern, loop thru any laser object's pattern list ( e.g. for pattern in box.lasers.laser1.patterns )
- to add logic for when we should trigger playing a certain pattern, we can use the phase functionality ( like while phase.active, check for a certain condition that if met will cause us to exit from the phase early and enter a new phase)