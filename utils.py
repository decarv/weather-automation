import psycopg2
import datetime

def datetime_to_timestamp(date):
    """ Converts datetime object to POSTGRESQL timestamp format YYYY-MM-DD. """
    return date.strftime("%Y-%m-%d")

def timestamp_to_datetime(timestamp):
    """ Converts POSTGRESQL timestamp format YYYY-MM-DD to datetime object. """
    return datetime.datetime(*tuple(map(lambda s : int(s), timestamp.split("-"))))

def db_connect(connection_string):
    print(connection_string)
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()
    return conn, cursor
