

from RPI_Operant.hardware.CSV_Functions import Experiment
import argparse
import os
parser = argparse.ArgumentParser(description='input io info')
parser.add_argument('--csv_in', '-i',type = str, 
                    help = 'where is the csv experiments file?',
                    action = 'store')


args = parser.parse_args()

if args.csv_in:
    csv_file = args.csv_in
 
else:
    csv_file = 'DataBaseControl/Test_CSV.csv'
    

if not os.path.isfile(csv_file):
    print('not a valid csvfile. double check that filepath! see ya.')
    exit()


    output = None

print(f'output to: {output}')
    
experiment =Experiment(csv_file)

resp = experiment.ask_to_run()

while resp:
    experiment.run()
    next_exists = experiment.next_experiment()
    if next_exists:
        resp = experiment.ask_to_run()
    else:
        break

print('whew! what a day of experiments!')



