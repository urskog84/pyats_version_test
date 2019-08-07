# load the virtual python enviralment
'source venv/bin/activate'

# testbed_from_inventory
this module add a function to create a pyats testbed object from a ansible inventory.

# credential - username/password
the credentials are provided to the "config.ini" file
simply rename the config_template.ini and modify to your need 

# To run the test
´easypy version_check_job.py´
## with html report
´easypy version_check_job.py -html_logs html_logs/´
