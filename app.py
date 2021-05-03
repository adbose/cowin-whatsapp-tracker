from flask import Flask, request
import requests
import geopy
# import geopy.distance
from geopy.geocoders import Nominatim
import constants
import json
import utils
from api.messaging import as_twilio_response


# Create Flask app instance
app = Flask(__name__)

# Create geolocator object as an instance of geopy's Nominatim class
geolocator = Nominatim(user_agent="covid-bot", timeout=5)

# Base API URL
base_url = 'https://cdn-api.co-vin/api'


# Create the API route
@app.route('/bot', methods=['POST'])
def bot():
    # import ipdb;ipdb.set_trace()
    # Get the incoming message request data
    incoming_values = request.values
    print("Incoming Values:\n", incoming_values)

    # Get Geolocation sent by user
    latitude = incoming_values.get('Latitude',  '')
    longitude = incoming_values.get('Longitude', '')

    # geopy geolocator API expects coordinates as a single comma separated string of latitude and longitude
    geo_coordinates_string = ", ".join((latitude, longitude))

    # Get the incoming message from incoming_values
    incoming_msg = incoming_values.get('Body', '').lower()

    if incoming_msg in constants.greeting_tokens:
        # return greeting message
        return as_twilio_response(constants.welcome_message)

    if 'help' in incoming_msg:
        # return help message
        return as_twilio_response(constants.help_message)

    if latitude:
        # Get the address dict from the geolocation data sent
        geo_location_dict = get_reverse_geocode(geo_coordinates_string)
        pincode = geo_location_dict.get('postcode', '')
        print('Pincode:', pincode)

        date_now = datetime.datetime.now().strftime('%d-%m-%Y')
        print("Today's Date:", date_now)

        appointment_api = base_url + '/v2/appointment/sessions/public/findByPin?pincode={pincode}&date={date_now}'
        
        appointment_response = get_appointment_response_by_pincode(appointment_api)
        
        location_response = get_location_message(geo_location_dict, appointment_response)
        return as_twilio_response(location_response)


# helper functions
def get_response(url):
    response = requests.get(url)
    return response.json()


# Get the address dict
def get_reverse_geocode(coordinates):
    location = geolocator.reverse(coordinates, exactly_one=True)
    address_dict = location.raw['address']
    print("Address Dict:", address_dict)
    return address_dict


def get_appointment_response_by_pincode(appointment_api):
    appointment_data = get_response(appointment_api)
    return appointment_data


def get_location_message(geo_location_dict, appointment_response):
    # TODO: Add complete address to show in Location response
    # or add entire address, but remove 'country_code': 'in'
    village = geo_location_dict.get('village', '')
    city = geo_location_dict.get('city', '')
    county = geo_location_dict.get('county', '')
    district = geo_location_dict.get('state_district', '')
    state = geo_location_dict.get('state', '')
    if city:
        address = ', '.join([city, county, district, state])
    elif village:
        address = ', '.join([village, county, district, state])
    else:
        address = ', '.join([county, district, state])
    
    location_message = f'''
Your detected location is {address}.

Available vaccine slots: {appointment_response}
'''
    return location_message




# Get states and districts
# base_api = 'https://cdn-api.co-vin/api'
# # API to get all the states in India.
# states_api = base_api + '/v2/admin/location/states'
# states_data = get_response(states_api)
# print(states_data)

# API to get districts for a given state
# district_api = base_api + '/v2/admin/location/districts/{state_id}'
# district_data_per_state = get_response(district_api)

# Checkout https://apisetu.gov.in/public/marketplace/api/cowin#/ for the CoWin Public API