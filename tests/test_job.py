# To run the job:
# easypy pyats_test.py
# Description: This job file shows ios version of the device
import os
from pyats.easypy import run


# All run() must be inside a main function
def main(runtime):

    runtime.job.name = 'my-job-overwrite-name'
#    runtime.job.report.attachment

    # Find the location of the script in relation to the job file
    run(
        testscript='./tests/test_version.py',
        runtime=runtime,
        taskid='my_task_version'
    )
    run(
        testscript='./tests/test_interface.py',
        runtime=runtime
    )
    run(
        testscript='./tests/test_dot1x.py',
        runtime=runtime
    )
    mailto_list = ['karl.petter.andersson@gmail.com']
    runtime.mailbot.mailto = mailto_list
