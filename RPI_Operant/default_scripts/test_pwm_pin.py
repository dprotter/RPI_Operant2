
import os
import time
try:
    if os.system('sudo lsof -i TCP:8888'):
        os.system('sudo pigpiod -s 2') #not sure what to set -s (sample rate) to. 
                                    #https://abyz.me.uk/rpi/pigpio/python.html#set_PWM_frequency
                                    #looks like you only get 18 PWM settings, but what they are 
                                    #changes depending on -s. and the tradeoff is memory required
                                    #there is more info here
                                    #https://github.com/fivdi/pigpio/blob/master/doc/configuration.md#configureclockmicroseconds-peripheral
    import pigpio
except:
    print('pigpio not found, using Fake_pigio. FOR TESTING PURPOSES')
    from RPI_Operant.hardware.Fake_GPIO import Fake_pigpio as pigpio

pi = pigpio.pi()
class PWM_Pin:
        def __init__(self, pin_num, pigpio_instance):
            self.pi = pigpio_instance
            self.pin = pin_num


        def set_duty_cycle(self, percent):
            '''take a percent (0 <-> 100) and set equivalent duty cycle. IE pcnt/100 * 255'''
            self.pi.set_PWM_dutycycle(self.pin, percent * 255 / 100)

        def set_hz(self, hz):
            ''''''
            self.pi.set_PWM_frequency(self.pin, int(hz))

pin = PWM_Pin(14, pi)
start = 100
for i in range(10):
    print(f'setting duty cycle to {100 - i*10}')
    pin.set_duty_cycle(100 - i*10)

    time.sleep(0.5)

pin.set_duty_cycle(0)