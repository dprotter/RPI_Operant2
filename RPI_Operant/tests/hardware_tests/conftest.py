import pytest
import os

DEFAULT_HARDWARE = os.path.join(os.getcwd(), 'RPI_Operant/default_setup_files/default_hardware.yaml')
DEFAULT_SOFTWARE = os.path.join(os.getcwd(), 'RPI_Operant/default_setup_files/default_software.yaml')
DEFAULT_OUTPUT_LOCATION = os.path.join(os.getcwd(), 'RPI_Operant/default_output_location')
RUNTIME_DICT = ''


def pytest_adoption(parser):
    parser.addoption('--hardware_config', action ="store", default =DEFAULT_HARDWARE)
    parser.addoption('--software_config', action ="store", default =DEFAULT_SOFTWARE)

@pytest.fixture()
def hw_path(request):
    return request.config.getoption('--hardware_config')

@pytest.fixture()
def sw_path(request):
    return request.config.getoption('--software_config')