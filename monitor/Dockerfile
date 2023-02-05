FROM python:3.9
WORKDIR /monitor
COPY ../requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt --user
COPY . .
CMD ["python", "monitor.py"]