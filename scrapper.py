import os
import datetime
import requests
import logging
import time
import json
import utils
import psycopg2
from interface import *
from bs4 import BeautifulSoup

class WeatherScrapper:

    CREATE_TABLE = """
            CREATE TABLE IF NOT EXISTS public.weather
            (
            date timestamp without time zone NOT NULL,
            temperature_mean double precision NOT NULL,
            precipitation_probability double precision NOT NULL,
            emailed boolean NOT NULL DEFAULT false,
            CONSTRAINT weather_pkey PRIMARY KEY (date)
        )

    """
    INSERT_QUERY = """INSERT INTO weather (date, temperature_mean, precipitation_probability, emailed) VALUES (%s, %s, %s, %s)"""
    MOST_RECENT_STORED_DATE_QUERY = """SELECT date FROM weather ORDER BY date DESC LIMIT 1"""

    def __init__(self, **kwargs):
               
        logging.basicConfig(
            level=logging.INFO, format=f'[{__class__.__name__}: %(asctime)s] %(message)s'
        )
        
        logging.info("WeatherScrapper started.")
        
        self.DEFAULT_FIRST_DATE = datetime.datetime(2022, 1, 1)
        self.REQUEST_MAX_RETRIES = 5
        self.REQUEST_WAIT_TIME = 10 # in seconds

        self.load_configuration_data(kwargs)
        self.db_connect()
        if not self.db_table_exists():
            self.db_create_table()
        self.scrape()
        self.db_disconnect()

    def load_configuration_data(self, kwargs):
        logging.info("Loading configuration data.")
        
        self.service = kwargs["service"] 
        self.connection_string = kwargs["db_connection_string"]
        
        if self.service == "weather.com":
            self.post_request = kwargs["post_request"]
            self.place_id = kwargs["place_id"]
            self.latitude, self.longitude = kwargs["geocode"].split(",")
            self.request_endpoint = self.post_request["headers"]["scheme"] + "://" + self.post_request["headers"]["authority"] + self.post_request["headers"]["path"]
            self.days_per_request = int(self.post_request["payload"][1]["params"]["days"])
            
            # TODO: assertions

        else:
            logging.error("Service not implemented.")
            exit(1)
        
        logging.info("Data loaded correctly.")
    
    def scrape(self):
        """ This method pulls and stores historical data since the value stored in ``.
        """
        logging.info("Starting data scraping.")

        if self.service == "weather.com":
            self.start_date = self.db_get_most_recent_stored_date()
            if self.start_date == None:
                self.start_date = self.DEFAULT_FIRST_DATE
            self.end_date = datetime.datetime.today()

            post_request_max_timedelta = datetime.timedelta(self.days_per_request, 0, 0)
            while self.end_date - self.start_date > post_request_max_timedelta:
                start_date = utils.datetime_to_timestamp(self.start_date)
                end_date = utils.datetime_to_timestamp(self.start_date + post_request_max_timedelta)
                response = self.make_post_request(start_date, end_date)
                structured_data = self.process_response(response)
                self.db_put_data(structured_data['dates'], structured_data['temperature_mean'], structured_data['precipitation_probability'])
                if self.end_date - self.start_date > post_request_max_timedelta:
                    self.start_date += post_request_max_timedelta
                else:
                    self.start_date += self.end_date - self.start_date

        logging.info("Data scraping successfuly done.")
            
    def make_post_request(self, start_date, end_date):
        logging.info(f"Making POST request to collect data between {start_date} and {end_date}.")
        
        formatted_start_date = "".join(start_date.split("-"))
        formatted_end_date = "".join(end_date.split("-"))
        self.fill_post_request(formatted_start_date, formatted_end_date)
        
        attempts = 0
        while True:
            attempts += 1
            try:
                response = requests.post(url=self.request_endpoint, 
                                         params=self.post_request["headers"], 
                                         json=self.post_request["payload"])
            except Exception as error:
                logging.error(f"Found exception while trying to make POST request: {error}")
                continue

            if response.status_code == 200:
                break
            
            if attempts > self.REQUEST_MAX_RETRIES:
                logging.error("Number of attempts exceeded. Exiting.")
                exit(1)

            sleep_time = self.REQUEST_WAIT_TIME * attempts
            logging.error(f"Last attempt to make POST request failed. Trying again in {sleep_time} seconds.")
            time.sleep(sleep_time)
        
        logging.info("POST request realizado com sucesso.")
        
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
    
    def db_connect(self, function=None, *args):
        logging.info("Connecting to the database.")
        self.conn = psycopg2.connect(self.connection_string)
        self.cursor = self.conn.cursor()
        logging.info("Successfully connected to the database.")

        if function is not None:
            function(*args) # TODO: Test this
    
    def db_disconnect(self):
        logging.info("Disconnecting from the database.")
        # TODO
    
    def db_get_most_recent_stored_date(self):
        date = None
        try:
            self.cursor.execute(self.MOST_RECENT_STORED_DATE_QUERY)
            date = self.cursor.fetchone()
            if date is not None:
                date = date[0] # the returned value is a tuple (value)
            self.conn.commit()
            
        except psycopg2.OperationalError:
            self.db_connect(function=self.db_get_most_recent_stored_date)
        except Exception as error:
            logging.error(f"Found exception while trying to get data from the database: {error}")
        return date 
    
    def db_put_data(self, dates, temperature_means, rain_probabilities):
        for i in range(len(dates)):
            try:
                insert_data = (dates[i], 
                               temperature_means[i],
                               rain_probabilities[i],
                               False
                               )
                self.cursor.execute(self.INSERT_QUERY, insert_data)
                self.conn.commit()
            except psycopg2.OperationalError:
                self.db_connect(self.db_put_data, dates[i:], temperature_means[i:], rain_probabilities[i:])
            except Exception as error:
                logging.error(f"Found exception while trying to put data to the database: {error}")

    def db_table_exists(self):
        self.cursor.execute("""SELECT EXISTS (SELECT * 
                                                FROM information_schema.tables
                                               WHERE table_name = 'weather')""")
        return_value = self.cursor.fetchone()[0]
        self.conn.commit()
        return return_value

    def db_create_table(self):
        self.cursor.execute(self.CREATE_TABLE)
        self.conn.commit()


if __name__ == "__main__":

    WeatherScrapper(
        place_id=CITY_IDS["SAO PAULO"],
        geocode=GEOCODES[CITY_IDS["SAO PAULO"]],
        service="weather.com",
        db_connection_string="postgres://postgres:postgrespw@localhost:32769", # TODO
        post_request=POST_REQUEST,
        )

    # WeatherScrapper(
    #     place_id=CITY_IDS[os.getenv("CITY")],
    #     geocode=GEOCODES[CITY_IDS[os.getenv("CITY")]],
    #     service=os.getenv("SERVICE"),
    #     db_connection_string=os.getenv("DB_CONNECTION_STRING"), # TODO
    #     post_request=POST_REQUEST,
    #     )
