# To run the job:
# easypy pyats_test.py
# Description: This job file shows ios version of the device
import os
from ats.easypy import run


# All run() must be inside a main function
def main():
    # Find the location of the script in relation to the job file
    testscript = os.path.join('./version_check.py')
    run(testscript=testscript)
