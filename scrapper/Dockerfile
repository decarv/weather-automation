FROM ubuntu:latest

WORKDIR /scrapper

# Install python/pip
RUN apt update
RUN apt upgrade
RUN apt -y install cron
RUN apt -y install rsyslog
RUN python3 -m ensurepip --upgrade
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --upgrade setuptools
RUN python3 -m pip install ez_setup
ENV PYTHONUNBUFFERED=1

# Copy files
COPY . .
COPY .. .
COPY cronjob /etc/cron.d/cronjob
RUN touch /var/log/cron.log

# install any Python requirements used by the jobs
# RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install requirements.txt

RUN chmod +x ./scrapper.py
RUN chmod +x /etc/cron.d/cronjob
RUN crontab /etc/cron.d/cronjob

CMD ["cron", "-f"]
