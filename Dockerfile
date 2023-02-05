FROM python:3.9
WORKDIR /dir
COPY . .
COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt --user
CMD ["python", "scrapper.py"]