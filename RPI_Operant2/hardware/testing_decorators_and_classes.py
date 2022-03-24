def outer_decorator(func):
        def wrapper(self, *args, **kwargs):
            print(f'decorated! {self.id}')
        return wrapper


class A:

    def __init__(self):
        self.id = 'a'

    '''    def test_decorator(func):
        def wrapper(self, *args, **kwargs):
            print(f'decorated! {self.id}')
        return wrapper'''
    
    @outer_decorator
    def who_am_i(self):
        print('i am....')

class B:
    def __init__(self):
        self.id = 'b'

    @outer_decorator
    def who_am_i(self):
        print('i am....')

if __name__ == '__main__':
    a = A()
    b = B()

    a.who_am_i()
    b.who_am_i()