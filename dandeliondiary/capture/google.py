import json
import requests

from django.conf import settings

class ResponseError(Exception):
    pass


def get_nearby_places(location, radius):
    """
    Execute Google Nearby Search Request

    Enables the creation of a list of potential businesses to associate and categorize an expense by getting nearby
    businesses within a specified radius based on user's current location.

    Sample search:
    https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=-33.8670522, 151.1957362&radius=500
    &type=restaurant&name=cruise&key=YOUR_API_KEY
    """

    # Create search URL
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={},{}&radius={}&key={}".format(
        location[0],
        location[1],
        radius,
        settings.GOOGLE_API_KEY
    )

    try:
        response = requests.get(url)
        return response.json()
    except Exception as err:
        raise ResponseError('Something went wrong fetching nearby places: {}'.format(err))


def byteify(input):
    if isinstance(input, dict):
        return {byteify(key): byteify(value)
                for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input
