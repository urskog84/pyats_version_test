# load the virtual python enviralment
'source venv/bin/activate'

# testbed_from_inventory
this module add a function to create a pyats testbed object from a ansible inventory.

# envioment variables
spesify the two vaiables, it's mndatory for the creation of the tesbed
- PYATS_USERNAME
- PYATS_PASSWORD

# To run the test
'easypy version_check_job.py'
## with html report
easypy version_check_job.py -html_logs html_logs/
