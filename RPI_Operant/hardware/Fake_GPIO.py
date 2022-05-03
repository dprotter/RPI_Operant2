class Fake_GPIO:
    def __init__(self):
        self.IN = 1
        self.OUT = 0
    
    def setup(self, pin, val):
        pass
    
    def input(self, pin):
        return 3