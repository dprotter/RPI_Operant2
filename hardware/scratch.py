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
            box.delay('reward_delay')
            door = box.doors[lever.target]
            door.open()
        

for lever in box.levers:
    lever.reset()



while not box.finished:
    box.new_round()  #this will iterate round numbers

    

    box.levers.door_1.extend()
    box.levers.door_2.extend()

    fr = box.config.fixed_ratio
    box.levers.door_1.wait_for_n_presses(n = fr, reset_next_round = True)
    box.levers.door_2.wait_for_n_presses(n = fr, reset_next_round = True)


    box.timer.new_phase(name = 'test', time = 30) #starting a new phase
    while box.phases['test'].is_active():   #try having sleep built into the is_active check to allow thread swapping
    
        if box.levers.door_1.presses_reached:  #will it be confusing to switch between attributes and methods?
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
    
    box.timer.new_phase(name = 'reward_time', time = 60)
    box.timer.wait_for_phase('reward_time')

    door.close()
    box.timer.new_phase(name = 'ITI', time = 90)
    box.timer.wait_for_phase('ITI')
