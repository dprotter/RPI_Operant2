
import pytest
import os
import RPI_Operant.hardware.box as Box


@pytest.fixture
def arrange_box(hw_path, sw_path):
    box = Box()
    box.setup(run_dict = {'vole':0,'day':1,'experiment':'python_run_tests'}, 
          user_hardware_config_file_path = hw_path,
          user_software_config_file_path = sw_path,
          start_now = True,
          simulated = True)
    
class TestLever:
    def __init__(self):
        self.box = arrange_box()
    def extend_levers(self):
        for lever in self.box.levers:
            self.extend_lever(lever)
            
    def extend_lever(self, lever):
        lever.extend()
        assert lever.is_extended == True