FROM ciscotestautomation/pyats:latest
ENV TZ 'Europe/Stockholm'

COPY ssh_config /etc/ssh/ssh_config


COPY requirements.txt /pyats/requirements.txt

COPY tests /pyats/tests

CMD ["pyats", "run", "job", "tests/test_job.py", "--testbed-file", "tests/testbed.yml", "--html-logs", "/pyats_local/html_logs/", "--liveview-host", "0.0.0.0", "--liveview-port", "8080", "--liveview-keepalive"]