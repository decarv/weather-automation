import os
import utils
import logging
import psycopg2
import smtplib, ssl
import datetime

class WeatherMonitor():
    
    MOST_RECENT_EMAILED_DATE_QUERY = "SELECT date FROM weather WHERE emailed = true ORDER BY date DESC LIMIT 1"
    LEAST_RECENT_DATE_QUERY = "SELECT date FROM weather ORDER BY date ASC LIMIT 1"

    # arguments: (most_recent_emailed_date, temperature_min, temperature_max, precipitation_probability_min)
    UNEMAILED_QUERY = """SELECT * 
                           FROM weather 
                          WHERE emailed = FALSE 
                            AND date > %s 
                            AND ((temperature_mean >= %s AND temperature_mean <= %s) 
                                  OR (precipitation_probability >= %s))
                            ORDER BY date"""

    # arguments: (most_recent_emailed_date)
    UPDATE_EMAILED_INSTANCES = "UPDATE weather SET emailed = TRUE WHERE date = %s"
    
    def __init__(self, **kwargs):

        logging.basicConfig(
            level=logging.INFO, format=f'[{__class__.__name__}: %(asctime)s] %(message)s'
        )

        self.DEFAULT_FALLBACK_DATE = datetime.datetime(2021,12,1)

        # TODO: create input validation
        self.temperature_min = kwargs["temperature_min"]
        self.temperature_max = kwargs["temperature_max"]
        self.precipitation_probability_min = kwargs["precipitation_probability_min"]
        
        self.smtp_server = kwargs["smtp_server"]
        self.sender_email = kwargs["sender_email"]
        self.email_password = kwargs["email_password"]
        self.receiver_email = kwargs["receiver_email"]
        self.connection_string = kwargs["db_connection_string"]

        self.conn, self.cursor = utils.db_connect(self.connection_string)

        self.most_recent_emailed_date = None
        self.db_get_most_recent_emailed_instance_date()
        if self.most_recent_emailed_date == None:
            self.most_recent_emailed_date = self.DEFAULT_FALLBACK_DATE
        self.unemailed_instances = None
        self.db_get_unemailed_instances_since_most_recent_emailed_date()
        self.email_create_body()

        self.email_send()
        self.db_update_emailed_instances()

    def db_get_most_recent_emailed_instance_date(self):
        try:
            self.cursor.execute(self.MOST_RECENT_EMAILED_DATE_QUERY)
            self.most_recent_emailed_date = self.cursor.fetchone()
            self.conn.commit()
        except psycopg2.OperationalError:
            self.conn, self.cursor = utils.db_connect(self.connection_string)
            self.db_get_most_recent_emailed_instance_date()
        except Exception as e:
            logging.error(f"Found Exception: {e}")

    def db_get_unemailed_instances_since_most_recent_emailed_date(self):
        try:
            args = (utils.datetime_to_timestamp(self.most_recent_emailed_date), 
                    self.temperature_min, 
                    self.temperature_max, 
                    self.precipitation_probability_min)
            self.cursor.execute(self.UNEMAILED_QUERY, args)
            self.unemailed_instances = self.cursor.fetchall()
            self.conn.commit()

        except psycopg2.OperationalError:
            #todo
            pass

        except Exception as e:
            logging.error(f"Found Exception: {e}")

    def db_update_emailed_instances(self):
        self.emailed_instances = self.unemailed_instances
        latest_emailed_date = self.emailed_instances[-1][0] # get lastest emailed date

        # update everything from most_recent_emailed_date to TIMESTAMP(TODAY()-1)
        start_date = utils.timestamp_to_datetime(self.most_recent_emailed_date)
        end_date = utils.timestamp_to_datetime(latest_emailed_date)
        while start_date <= end_date:
            try:
                arg = utils.datetime_to_timestamp(start_date)
                self.cursor.execute(self.UPDATE_EMAILED_INSTANCES, arg)
                self.conn.commit()
                start_date += datetime.timedelta(1, 0, 0)
            except psycopg2.OperationalError:
                self.db_connect(function=self.db_update_emailed_instances)
            except Exception as e:
                logging.error(f"Found Exception: {e}")
                exit(1) # TODO: problem to exit here?

    def email_create_body(self):
        self.email_body = "Lista dos dias em que a temperatura esteve acima de {} C e abaixo de {} C OU em que a probabilidade de chuva esteve acima de {}:\n".format(self.temperature_min, self.temperature_max, self.precipitation_probability_min)

        for instance in self.unemailed_instances:
            date, temp_mean, prec_prob, is_emailed = instance
            self.email_body += "{} - {}C {}%\n".format(date, temp_mean, prec_prob)

    def email_send(self):
       PORT = 465
       context = ssl.create_default_context()
       with smtplib.SMTP_SSL(self.smtp_server, PORT, context=ssl.create_default_context()) as server:
           server.login(self.sender_email, self.email_password)
           server.sendmail(self.sender_email, self.receiver_email, self.email_body)


if __name__ == '__main__':
    WeatherMonitor(
        temperature_min=15,
        temperature_max=40,
        precipitation_probability_min=50,
        sender_email="weather.monitor.test@gmail.com",
        receiver_email="decarv.henrique@gmail.com",
        email_password="weather.monitor.T3ST",
        db_connection_string="postgres://postgres:postgrespw@localhost:32769",
        smtp_server="smtp.gmail.com",
        # temperature_min=os.getenv("TEMPERATURE_MIN"),
        # temperature_max=os.getenv("TEMPERATURE_MAX"),
        # precipitation_probability_min=os.getenv("PRECIPITATION_PROBABILITY_MIN"),
        # sender_email=os.getenv("SENDER_EMAIL"),
        # receiver_email=os.getenv("RECEIVER_EMAIL"),
        # email_password=os.getenv("EMAIL_PASSWORD"),
    )
