import os
import datetime
import requests
import logging
import time
import json
import utils
import psycopg2
import schedule
from interface import *
from bs4 import BeautifulSoup

class WeatherScrapper:

    def __init__(self, **kwargs):
        logging.basicConfig(
            level=logging.INFO, 
            format=f'[{__class__.__name__}: %(asctime)s] %(message)s'
        )
        
        logging.info("WeatherScrapper started.")

        self.DEFAULT_FALLBACK_DATE = datetime.datetime(2022, 1, 1)
        self.REQUEST_MAX_RETRIES = 5
        self.REQUEST_WAIT_TIME = 10 # in seconds

        logging.info("Loading configuration data.")
        logging.info(kwargs)
        self.load_configuration_data(kwargs)
        
        logging.info("Connecting to the database.")
        self.conn, self.cursor = utils.db.connect(self.connection_string)
        if not utils.db.table_exists(self.cursor, self.conn):
            utils.db.table_create(self.cursor, self.conn)

        logging.info("Job scheduled to run everyday at {}".format(self.schedule))
        schedule.every().day.at(self.schedule).do(self.job)
        
        while True:
            schedule.run_pending()
            time.sleep(10)

    def load_configuration_data(self, kwargs):

        self.service = kwargs["service"] 
        self.connection_string = kwargs["db_connection_string"]
        self.schedule = kwargs["schedule"]

        if self.service == "weather.com":
            self.post_request = kwargs["post_request"]
            self.place_id = kwargs["place_id"]
            self.latitude, self.longitude = kwargs["geocode"].split(",")
            self.request_endpoint = self.post_request["headers"]["scheme"] + "://" + self.post_request["headers"]["authority"] + self.post_request["headers"]["path"]
            self.days_per_request = int(self.post_request["payload"][1]["params"]["days"])
            
            # TODO: data validation
        else:
            logging.error("Service not implemented.")
            exit(1)
    
    def job(self):
        """ This method pulls and stores historical data since the value stored in ``.
        """
        logging.info("Starting data scraping.")

        if self.service == "weather.com":
            self.start_date = utils.db.get_most_recent_stored_date(self.cursor, self.conn)
            if self.start_date == None:
                self.start_date = self.DEFAULT_FALLBACK_DATE
            else: 
                # the start_date is one day after the last date stored
                self.start_date += datetime.timedelta(1, 0, 0) 

            self.end_date = datetime.datetime.today()

            post_request_max_timedelta = datetime.timedelta(self.days_per_request, 0, 0)
            while self.start_date <= self.end_date:
                request_start_date = utils.datetime_to_timestamp(self.start_date)
                if self.start_date + post_request_max_timedelta < self.end_date:
                    request_end_date = utils.datetime_to_timestamp(self.start_date + post_request_max_timedelta)
                else:
                    request_end_date = utils.datetime_to_timestamp(self.end_date)

                response = self.make_post_request(request_start_date, request_end_date)
                structured_data = self.process_response(response)

                utils.db.put(self.cursor, 
                             self.conn,
                             structured_data['dates'], 
                             structured_data['temperature_mean'], 
                             structured_data['precipitation_probability']
                             )

                self.start_date += post_request_max_timedelta


        logging.info("Data scraping successfuly done.")
            
    def make_post_request(self, start_date, end_date):
        logging.info(f"Making POST request to collect data between {start_date} and {end_date}.")
        
        formatted_start_date = "".join(start_date.split("-"))
        formatted_end_date = "".join(end_date.split("-"))
        self.fill_post_request(formatted_start_date, formatted_end_date)
        
        attempts = 0
        while True:
            attempts += 1
            if attempts > self.REQUEST_MAX_RETRIES:
                logging.error("Number of attempts exceeded. Exiting.")
                exit(1)

            try:
                response = requests.post(url=self.request_endpoint, 
                                         params=self.post_request["headers"], 
                                         json=self.post_request["payload"])

                if response.status_code == 200:
                    break
                
            
            except Exception as error:
                logging.error(f"Found exception while trying to make POST\
                                request: {error}")
                continue

            sleep_time = self.REQUEST_WAIT_TIME * attempts
            logging.error(f"Last attempt to make POST request failed. Trying again in {sleep_time} seconds.")
            time.sleep(sleep_time)
        
        return response 
        
    def fill_post_request(self, start_date, end_date):
        for key in self.post_request:
            self.recursive_fill_post_request(self.post_request, key, start_date, end_date)

    def recursive_fill_post_request(self, attr, key, start_date, end_date):
        value = attr[key]
        value_type = type(value)
        if value_type == dict:
            for key in value:
                self.recursive_fill_post_request(value, key, start_date, end_date)
        elif value_type == list:
            for i in range(len(value)):
                self.recursive_fill_post_request(value, i, start_date, end_date)
        else:
            if key == "latitude":
                attr[key] = self.latitude
            elif key == "longitude":
                attr[key] = self.longitude
            elif key == "date" or key == "startDate":
                attr[key] = start_date
            elif key == "endDate":
                attr[key] = end_date
            elif key == "startDay":
                attr[key] = int(start_date[6:])
            elif key == "startMonth":
                attr[key] = int(start_date[4:6]) 
    
    def process_response(self, response):
        data = response.content
        structured_data = {}

        if self.service == "weather.com":
            # extract data
            json_data = json.loads(data)
            params = self.post_request['payload'][1]['params']
            parameter_string = "days:{};geocode:{};language:{};startDay:{};"\
                               "startMonth:{};units:{}".format(
                                                       params['days'], 
                                                       params['geocode'], 
                                                       params['language'], 
                                                       params['startDay'], 
                                                       params['startMonth'], 
                                                       params['units']
                                                   )
            data = json_data['dal']['getSunV3DailyAlmanacUrlConfig'][parameter_string]['data']
            structured_data['temperature_mean'] = data['temperatureMean'] # TODO: generalize?
            structured_data['precipitation_probability'] = data['precipitationAverage'] # TODO: generalize?
            structured_data['dates'] = [datetime.timedelta(i, 0, 0) + self.start_date for i in range(self.days_per_request)]

        elif self.service == "SCRAPE_HTML":
            pass

        return structured_data
    
if __name__ == "__main__":

    # Run locally for debugging:
    # WeatherScrapper(
    #     place_id=CITY_IDS["SAO PAULO"],
    #     geocode=GEOCODES[CITY_IDS["SAO PAULO"]],
    #     service="weather.com",
    #     db_connection_string="postgres://postgres:postgrespw@postgres:5432", # TODO
    #     post_request=POST_REQUEST,
    #     schedule="10:30"
    #     )

     WeatherScrapper(
         schedule=os.getenv("SCHEDULE"),
         place_id=CITY_IDS[os.getenv("CITY")],
         geocode=GEOCODES[CITY_IDS[os.getenv("CITY")]],
         service=os.getenv("SERVICE"),
         db_connection_string=os.getenv("DB_CONNECTION_STRING"), # TODO
         post_request=POST_REQUEST,
         )
