from setuptools import setup, find_packages

# To update your package with the latest version of your code pushed
# to the repo, simply call the "pip install git+[url-to-github-repo]"
# again and it should check for the version # in the setup.py file and
# update your package.


# This function is used to tell pip how to install the package
# Most of these are optional except name, author, author email, git url, and packages
setuptools.setup(
    # Give package a name (Must match package folder name)
    name = 'RPI_Operant',
    # Version of your package, pip uses this to see if packages need updating;
    # If you make any changes to your code make sure to increment the version number i.e. 1.1 -> 1.2
    version = '2.0',
    author = 'Donaldson Lab',
    author_email = 'david.protter@colorado.edu',
    description = 'Testing installation of package',
    # URL to your repo
    url = 'https://github.com/dprotter/RPI_Operant2',
    # Optional licensing
    license = 'MIT',
    # list of packages that need to be built; if not using find_packages(), must match package folder name
    packages = ['RPI_Operant'], # for multi-file packages replace: packages = ['PhAT'] with packages = find_packages()
    # list of packages that your package relies upon
    install_requires = ['numpy==1.25.2', 'pandas==1.5.3', 'pyyaml','RPi-GPIO','himl', 'serial', 'adafruit-circuitpython-servokit']
    
)

