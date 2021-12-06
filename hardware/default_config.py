from adafruit_servokit import ServoKit
kit = ServoKit(channels=16)

servo_dict = {'lever_food':kit.servo[14], 'dispense_pellet':kit.continuous_servo[1],
                'lever_door_1':kit.servo[2], 'door_1':kit.continuous_servo[0],
                'lever_door_2':kit.servo[12],'door_2':kit. continuous_servo[13]}

doors = [
    
        {'name':'door_1',
         'servo':kit.continuous_servo[0],
         'stop':0.05,
         'close':-0.1,
         'open':0.8,
         'open_time':1.6,
         'override_open_pin':24,
         'override_close_pin':25,
         'state_switch':4},

        {'name':'door_2',
         'servo':kit.continuous_servo[13],
         'stop':0.03,
         'close':-0.1,
         'open':0.8,
         'open_time':1.6,
         'override_open_pin':24,
         'override_close_pin':25,
         'state_switch':17}
         
         ]

levers = [
    
        {'name':'food',
         'servo':kit.servo[14],
         'extended':30,
         'retracted':105,
         'pin':19,
         'pullup_pulldown':'pull_up',
         'target_name':'pellet_dispenser',
         'target_type':'dispenser'
         },
    
        {'name':'door_1',
         'servo':kit.servo[2],
         'extended':20,
         'retracted':100,
         'pin':18,
         'pullup_pulldown':'pull_up',
         'target_name':'door_1',
         'target_type':'door'
         },

        {'name':'door_2',
         'servo':kit.servo[12],
         'extended':20,
         'retracted':100,
         'pin':22,
         'pullup_pulldown':'pull_up',
         'target_name':'door_2',
         'target_type':'door'
         }
         
         ]
          
          
          
          