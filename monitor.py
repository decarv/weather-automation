import os
import time
import utils
import logging
import psycopg2
import smtplib
import datetime
import schedule

class WeatherMonitor():
    
    
    def __init__(self, **kwargs):
        logging.basicConfig(
            level=logging.INFO, 
            format=f'[{__class__.__name__}: %(asctime)s] %(message)s'
        )
    
        logging.info("WeatherMonitor started.")

        self.DEFAULT_FALLBACK_DATE = datetime.datetime(2022,1,1)

        logging.info("Loading configuration data.")
        self.load_configuration_data(kwargs)

        logging.info("Connecting to the database.")
        self.conn, self.cursor = utils.db.connect(self.connection_string)
        logging.info("Job scheduled to run everyday at {}".format(self.schedule))
        schedule.every().day.at(self.schedule).do(self.job)
        schedule.every(1).minutes.do(self.job)

        while True:
            schedule.run_pending()
            time.sleep(10)


    def job(self):
        most_recent_emailed_date = utils.db.get_most_recent_emailed_instance_date(
            self.cursor, self.conn)
        if most_recent_emailed_date is None:
            most_recent_emailed_date = self.DEFAULT_FALLBACK_DATE

        unemailed_instances = utils.db.get_unemailed_instances_since_most_recent_emailed_date(
            self.cursor, 
            self.conn,
            most_recent_emailed_date,
            self.temperature_min,
            self.temperature_max,
            self.precipitation_probability_min)

        self.email_send(unemailed_instances)

        if unemailed_instances is not None:
            utils.db.update_emailed_instances(self.cursor, self.conn, unemailed_instances, most_recent_emailed_date)

    def load_configuration_data(self, kwargs):
        # TODO: create input validation
        self.temperature_min = kwargs["temperature_min"]
        self.temperature_max = kwargs["temperature_max"]
        self.precipitation_probability_min = kwargs["precipitation_probability_min"]
        self.smtp_server = kwargs["smtp_server"]
        self.smtp_server_port = kwargs["smtp_server_port"]
        self.sender_email = kwargs["sender_email"]
        self.email_password = kwargs["email_password"]
        self.receiver_email = kwargs["receiver_email"]
        self.connection_string = kwargs["db_connection_string"]
        self.schedule = kwargs["schedule"]

    def email_send(self, unemailed_instances):
        # DO NOT change the first line of email_body
        email_body = "From: {}\r\n\
                        To: {}\r\n\
                   Subject: {}\r\n\\r\n".format(self.sender_email, 
                                            self.receiver_email, 
                                            "Monitoramento do Tempo")

        email_body += "Lista dos dias em que a temperatura esteve acima de {} C e abaixo de {} C OU em que a probabilidade de chuva esteve acima de {}:\n".format(self.temperature_min, self.temperature_max, self.precipitation_probability_min)

        if unemailed_instances is not None and len(unemailed_instances) > 0:
            for instance in unemailed_instances:
                date, temp_mean, prec_prob, _ = instance
                email_body += "{} - {} C {}%\n".format(date, temp_mean, prec_prob)
        else:
            email_body += "\n~ * ~ Sem resultados ~ * ~"

        with smtplib.SMTP(self.smtp_server, self.smtp_server_port) as server:
            server.starttls()
            server.login(self.sender_email, self.email_password)
            server.sendmail(self.sender_email, self.receiver_email, email_body)
            logging.info("Email sent.")


if __name__ == '__main__':
    WeatherMonitor(
        schedule="10:00",
        temperature_min=15,
        temperature_max=20,
        precipitation_probability_min=50,
        sender_email="weather.monitor@outlook.com",
        receiver_email="decarv.henrique@gmail.com",
        email_password="weather.M0N1T0R",
        db_connection_string="postgres://postgres:postgrespw@localhost:32768",
        smtp_server="smtp-mail.outlook.com",
        smtp_server_port=587,
        # sender_email=os.getenv("SENDER_EMAIL"),
        # sender_email=os.getenv("SENDER_EMAIL"),
        # email_password=os.getenv("EMAIL_PASSWORD"),
        # receiver_email=os.getenv("RECEIVER_EMAIL"),
        # smtp_server=os.getenv("SMTP_SERVER"), 
        # smtp_server_port=int(os.getenv("SMTP_SERVER_PORT")),
        # db_connection_string=os.getevn("DB_CONNECTION_STRING"),
        # temperature_min=int(os.getenv("TEMPERATURE_MIN")),
        # temperature_max=int(os.getenv("TEMPERATURE_MAX")),
        # precipitation_probability_min=int(os.getenv("PRECIPITATION_PROBABILITY_MIN")),
    )
