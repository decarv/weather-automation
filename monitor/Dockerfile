FROM python:3.9

WORKDIR /monitor

RUN apt update
RUN apt upgrade
# RUN apt -y install cron
# RUN apt -y install rsyslog
RUN python3 -m ensurepip --upgrade
RUN python3 -m pip install --upgrade pip
# RUN python3 -m pip install --upgrade setuptools
# RUN python3 -m pip install ez_setup
ENV PYTHONUNBUFFERED=1

# Copy files
COPY . .
COPY monitor .
# COPY monitorjob /etc/cron.d/monitorjob
# RUN touch /var/log/cron.log

# install any Python requirements used by the jobs
RUN pip3 install --no-cache-dir -r requirements.txt

# RUN chmod +x /monitor/monitor.py
# RUN chmod +x /etc/cron.d/monitorjob
# RUN crontab /etc/cron.d/monitorjob

CMD ["python3", "/monitor/monitor.py"]
