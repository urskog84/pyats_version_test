FROM ciscotestautomation/pyats:latest
ENV TZ 'Europe/Stockholm'

COPY requirements.txt /pyats/requirements.txt
#COPY pyats.conf /etc/pyats.conf
COPY tests /pyats/tests

CMD ["easypy", "tests/test_job.py", "-testbed_file", "tests/testbed.yml", "-html_logs", "/pyats_local/html_logs"]
