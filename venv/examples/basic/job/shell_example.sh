#!/bin/bash

# Creating a shell script that execute a job file. This allows to already
# mention the arguments that will be needed for the run. This way, you can
# execute this file, with no argument, or only a few.
pwd_=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

# Simplest example. Only execute the script
pyats run job $pwd_"/basic_example_job.py"


echo $pwd_"/basic_example_job.py --no-archive"
# Pass some argument to easypy
pyats run job $pwd_"/basic_example_job.py --no-archive"

# Lastly, some argument could be passed via argv
if [[ $# -ne 0 ]]; then
    pyats run job $pwd_"/basic_example_job.py $@"
fi
