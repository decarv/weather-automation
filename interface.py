""" This file is contains specially crafted requests to interface with weather.com
private APIs and borrow its data.

"""

CITY_IDS = {
    "SAO PAULO" : "63e18eea74a484c42c3921cf52a8fec98113dbb13f6deb7c477b2f453c95b837" 
    }

# <placeId, geolocation>
# En: placeId can be obtained in the url of weather.com
GEOCODES = {
    "63e18eea74a484c42c3921cf52a8fec98113dbb13f6deb7c477b2f453c95b837" : "-23.55,-46.63"
    }

#
POST_REQUEST = {
    "headers" : {
        "authority" : "weather.com",
        "method" : "POST",
        "path" : "/api/v1/p/redux-dal",
        "scheme" : "https",
        "accept" : "*/*",
        "content_length" : "748",
        "content_type" : "application/json",
        "accept_encoding" : "gzip",
        "user_agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
        },
    "payload" : [
{
    "name": "getSunV2AstroUrlConfig",
    "params": {
        "geocode": "-23.55,-46.63",
        "days": "30",
        "date": "",
        "language": "en-US"
    }
},

{
    "name": "getSunV3DailyAlmanacUrlConfig",
    "params": {
        "geocode": "-23.55,-46.63",
        "units": "m",
        "days": "45",
        "startDay": 0,
        "startMonth": 0,
        "language": "en-US"
    }
},

    ]
}

if __name__ == "__main__":
    print("Usage: python3 main.py")
    exit(1)
