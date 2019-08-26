# To run the job:
# easypy pyats_test.py
# Description: This job file shows ios version of the device
import os
from ats.easypy import run


# All run() must be inside a main function
def main(runtime):
    # Find the location of the script in relation to the job file
    run(testscript='test_version.py', runtime=runtime)
    run(testscript='test_interface.py', runtime=runtime)
