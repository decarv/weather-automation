import psycopg2
import datetime

def datetime_to_timestamp(date):
    """ Converts datetime object to POSTGRESQL timestamp format YYYY-MM-DD. """
    return date.strftime("%Y-%m-%d")

def timestamp_to_datetime(timestamp):
    """ Converts POSTGRESQL timestamp format YYYY-MM-DD to datetime object. """
    return datetime.datetime(*tuple(map(lambda s : int(s), timestamp.split("-"))))

class db:

    def connect(connection_string):
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        return conn, cursor

    def table_exists(cursor, connection):
            cursor.execute("""SELECT EXISTS (SELECT * 
                                               FROM information_schema.tables
                                              WHERE table_name = 'weather')""")
            result = cursor.fetchone()[0]
            connection.commit()
            return result
        
    def table_create(cursor, conn):
        cursor.execute("""CREATE TABLE IF NOT EXISTS public.weather (
                            date timestamp without time zone NOT NULL,
                            temperature_mean double precision NOT NULL,
                            precipitation_probability double precision NOT NULL,
                            emailed boolean NOT NULL DEFAULT false,
                            CONSTRAINT weather_pkey PRIMARY KEY (date))"""
        )
        conn.commit()

    def get_most_recent_stored_date(cursor, conn):
            date = None
            try:
                cursor.execute("""SELECT date 
                                    FROM weather 
                                   ORDER BY date DESC 
                                   LIMIT 1""")
                date = cursor.fetchone()
                if date is not None:
                    date = date[0] # the returned value is a tuple: (value,)
                conn.commit()
                
            # TODO: DANGER: potential recursive bomb
            # except psycopg2.OperationalError:
            #     pass

            except Exception as error:
                print(f"Found exception while trying to get \
                        data from the database: {error}")
            return date 
        
    def put(cursor, conn, dates, temperature_means, rain_probabilities):
        for i in range(len(dates)):
            try:
                insert_data = (dates[i], 
                               temperature_means[i],
                               rain_probabilities[i],
                               False
                               )
                cursor.execute("""INSERT INTO weather 
                (date, temperature_mean, precipitation_probability, emailed) 
                VALUES (%s, %s, %s, %s)""", 
                insert_data)
                conn.commit()

            except Exception as error:
                print(f"Found exception while trying to put \
                        data to the database: {error}")


    def get_most_recent_emailed_instance_date(cursor, conn):
        most_recent_emailed_date = None
        try:
            cursor.execute("""SELECT date 
                                FROM weather 
                               WHERE emailed = true 
                               ORDER BY date DESC 
                               LIMIT 1""")
            most_recent_emailed_date = cursor.fetchone()
            if most_recent_emailed_date is not None:
                most_recent_emailed_date = most_recent_emailed_date[0]
            conn.commit()

        except Exception as e:
            print(f"Found Exception: {e}")

        return most_recent_emailed_date

    def get_unemailed_instances_since_most_recent_emailed_date(
        cursor, 
        conn, 
        most_recent_emailed_date,
        temperature_min,
        temperature_max,
        precipitation_probability_min):

            unemailed_instances = None
            try:
                args = (datetime_to_timestamp(most_recent_emailed_date), 
                        temperature_min, 
                        temperature_max, 
                        precipitation_probability_min)

                cursor.execute("""SELECT * 
                                    FROM weather 
                                   WHERE emailed = FALSE 
                                         AND date > %s 
                                         AND ((temperature_mean >= %s 
                                               AND temperature_mean <= %s) 
                                         OR (precipitation_probability >= %s))
                                   ORDER BY date""", args)

                unemailed_instances = cursor.fetchall()
                conn.commit()

            # TODO:
            #  To recover here the connection string has to be passed from 
            # except psycopg2.OperationalError:
            #     db.connect(cursor, conn)
            #     return get_unemailed_instances_since_most_recent_emailed_date(
            #         cursor,
            #         conn, 
            #         most_recent_emailed_date,
            #         temperature_min,
            #         temperature_max,
            #         precipitation_probability_min)

            except Exception as e:
                print(f"Found Exception: {e}")

            return unemailed_instances

    def update_emailed_instances(cursor, conn, emailed_instances, most_recent_emailed_date):
            if len(emailed_instances) > 0:
                latest_emailed_date = emailed_instances[-1][0] # get lastest emailed date
                start_date = most_recent_emailed_date
                end_date = latest_emailed_date
                while start_date <= end_date:
                    try:
                        arg = (datetime_to_timestamp(start_date),)
                        cursor.execute("""UPDATE weather 
                                             SET emailed = true 
                                           WHERE date = %s""", arg)
                        conn.commit()
                        start_date += datetime.timedelta(1, 0, 0)

                    # TODO:
                    # except psycopg2.OperationalError:
                    #     db.connect(cursor, conn)
                    #     db.update_emailed_instances(cursor, conn, 
                    #                                 emailed_instances, 
                    #                                 most_recent_emailed_date)

                    except Exception as error:
                        print(f"Found Exception: {error}")
                        exit(1) # TODO: problem to exit here?
