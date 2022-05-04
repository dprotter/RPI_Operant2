class Fake_GPIO:
    def __init__(self):
        self.IN = 1
        self.OUT = 0
        self.PUD_UP = 1
        self.PUD_DOWN = 1
    def setup(self, *args,**kwargs):
        pass
    
    def input(self, pin):
        return 3