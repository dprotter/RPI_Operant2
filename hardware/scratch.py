from collections.abc import Mapping
import inspect
dict_1 = {'doors':{
                'door_1':{'pin':22, 'speed':10, 'default_val':1},
                'door_2':{'pin':24, 'speed':20}

}}

dict_2 = {'doors':{
                'door_1':{'pin':22, 'speed':15, 'name':'test'},
                'door_2':{'pin':23, 'speed':12}

}}
d_out = dict_1.copy()
d_out.update(dict_2)

d_l1_out = dict_1.copy()
d_out['doors'].update(dict_2['doors'])
print(dict_1)
print(d_out)
print(d_l1_out)

def heirarchical_merge_dict(dict_default, dict_update):
    for key, value in dict_update.items():
        if isinstance(value, Mapping):
            #note to self the get(key,{}) returns an empty list if the key is not found. good technique for avoiding KeyErrors
            dict_default[key] = heirarchical_merge_dict(dict_default.get(key,{}), value)
        else:
            dict_default[key] = value
    return dict_default


def get_default_args(func):
    def wrapper(*in_args, **in_kwargs):
        bound_args = inspect.signature(func).bind(*in_args, **in_kwargs)
        print(bound_args)
        bound_args.apply_defaults()
        print(bound_args.arguments)

    return wrapper

@get_default_args
def test(i, j = 1):
    '''thats it'''

test(0)
test(0, j = 3)




box = an_object


box.timer.new_phase(name = 'test', time = 30)
active_levers = box.levers.get_components('''***get from config***''')

for lever in active_levers:
    lever.extend()
    lever.wait_for_n_presses(n = 5)
        
while box.phases['test'].active():
    for lever in active_levers:
        if lever.presses_reached:
            
            box.retract_all_levers()

            box.speaker.play_tone('door_open')
            box.delay(box.config['reward_delay'])
            door = box.doors[lever.target]
            door.open()
        

for lever in box.levers:
    lever.reset()



while not box.finished: #box will check how many rounds it needs to complete from config file
    box.new_round()  #this will iterate round numbers

    

    box.levers.door_1.extend()
    box.levers.door_2.extend()

    fr = box.config['fixed_ratio']
    box.levers.door_1.wait_for_n_presses(n = fr, reset_next_round = True)
    box.levers.door_2.wait_for_n_presses(n = fr, reset_next_round = True)


    box.timer.new_phase(name = 'test', time = 30) #starting a new phase
    while box.phases['test'].is_active():   #try having sleep built into 
                                            #the is_active check to allow 
                                            #thread swapping

        if box.levers.door_1.presses_reached:  #will it be confusing to switch 
                                               #between attributes and methods?

            door = box.doors.door_1   
            box.phases['test'].finished()


        elif box.levers.door_2.presses_reached:

            door = box.doors.door_2   
            box.phases['test'].finished()
        
        else:
            door = None

    #check if a lever was pressed enough to open a door. if so, reward and open  
    if door:
        box.speaker.play_tone('door_open')
        box.delay('reward_delay')
        door.open()
    
        box.timer.new_phase(name = 'reward_time', time = box.config['reward_time'])
        box.timer.wait_for_phase('reward_time')

    door.close()
    box.timer.new_phase(name = 'ITI', time = 90)
    box.timer.wait_for_phase('ITI')

[('doors', 
        {'door_1': 
            {'servo': 0, 'stop': 0.05, ...}, 
         'door_2': 
            {'servo': 13, 'stop': 0.03, ...}}),
 ('levers',
        {'food':
            {'servo':4, 'extended':30...}
            })]


def get_file_list(path_to_files):
    '''lots of ways to do this, but this one is easy'''
    files = glob.glob(path_to_files + '/**/*.txt', recursive=True)
    return files

def my_function(file):
    '''process data from a file. IE multiply data by 10'''
    data = open(file)
    
    '''do stuff here!'''
    output = data*10
    return output

def my_plotter(data):
    '''take data and plot it'''
    xvals = data[0]
    yvals = data[1]
    fig, ax = plt.subplots()
    ax.plot(xvals, yvals)
    return ax

def make_output_file_name(path, extension = '.txt'):
    return path.split(extension)[0] + '.png'

############################################################

file_list = get_file_list(path)
assembled_data = []
for file in file_list:
    analyzed_data = my_function(file)
    plot_object = my_plotter(analyzed_data)

    out_fname = make_output_file_name(file)
    plot_object.save(out_fname)

    assembled_data.append(analyzed_data)

'''do more stuff with assembled data here!'''

latency_obj = box.timstamps.new_latency()
timestamp = box.timestamps.new_timestamp()
