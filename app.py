from flask import Flask, request
import requests
import geopy
# import geopy.distance
from geopy.geocoders import Nominatim
import json
from datetime import datetime
import constants
from twilio.twiml.messaging_response import MessagingResponse

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
        # pincode = geo_location_dict.get('postcode', '')
        # print('Pincode:', pincode)

        date_now = datetime.today().strftime('%d-%m-%Y')
        print("Today's Date:", date_now)

        
        # appointment_response = get_appointment_response_by_pincode(appointment_api)
        
        location_response = get_location_message(geo_location_dict, date_now)
        return as_twilio_response(location_response)


# helper functions
def as_twilio_response(message: str) -> str:
    resp = MessagingResponse()
    msg = resp.message()
    msg.body(message)
    return str(resp)

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
    appointment_api = base_url + '/v2/appointment/sessions/public/findByPin?pincode={pincode}&date={date_now}'

    appointment_data = get_response(appointment_api)
    return appointment_data


def get_location_message(geo_location_dict, date_now):
    # TODO: Add complete address to show in Location response
    # or add entire address, but remove 'country_code': 'in'
    # village = geo_location_dict.get('village', '')
    # city = geo_location_dict.get('city', '')
    # county = geo_location_dict.get('county', '')

    pincode = geo_location_dict.get('postcode', '')
    district = geo_location_dict.get('state_district', '')
    state = geo_location_dict.get('state', '')
    
    # states_api = base_url + '/v2/admin/location/states'
    # states_data = get_response(states_api)
    # print(states_data)

    appointment_api_by_pin = base_url + '/v2/appointment/sessions/public/findByPin?pincode={pincode}&date={date_now}'.format(pincode=pincode, date_now=date_now)
    appointment_data = get_response(appointment_api_by_pin)

    appointment_response = f'''
    '''
    sessions = appointment_data.get("sessions", [])
    if sessions:
        count = 1
        for each in session:
            # Print the name, address, district
            serial_number = count
            name = each.get("name", "")
            address = each.get("address", "")
            district = each.get("district_name", "")
            from_time = each.get("from", "")
            to_time = each.get("to", "")
            fee_type = each.get("fee_type", "")
            fee = each.get("fee", 0)
            available_capacity = each.get("available_capacity", 0)
            min_age_limit = each.get("min_age_limit", 18)
            vaccine = each.get("vaccine", "")

            each_response = f'''
            {serial_number}. {name}
            {address}, {district}
            Vaccine: {vaccine}, {fee_type}
            Available: {available_capacity} 
            '''
            appointment_response += each_response
        
    location_message = f'''
Your location pincode is {pincode}.

Available vaccine slots today: {appointment_response}

Visit www.cowin.gov.in to book your vaccination
'''
    return location_message


if __name__ == '__main__':
    app.run()

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