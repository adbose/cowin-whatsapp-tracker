from flask import Flask, request
import requests
import geopy
import re
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
base_url = 'https://cdn-api.co-vin.in/api'


# The root endpoint
@app.route("/")
def hello():
    return "Hello, World!"


# The /bot webhook endpoint
@app.route('/bot', methods=['POST'])
def bot():
    # Get the incoming message request data
    incoming_values = request.values
    print("Incoming Values:\n", incoming_values)

    # Get Geolocation sent by user
    latitude = incoming_values.get('Latitude',  '')
    longitude = incoming_values.get('Longitude', '')

    # Geopy geolocator API expects coordinates as a single comma separated string of latitude and longitude
    geo_coordinates_string = ", ".join((latitude, longitude))

    # Get the incoming message from incoming_values
    incoming_msg = incoming_values.get('Body', '').lower()


    if incoming_msg in constants.greeting_tokens:
        # Return greeting message
        return as_twilio_response(constants.welcome_message)

    if 'help' in incoming_msg:
        # Return help message
        return as_twilio_response(constants.help_message)

    if latitude:
        geo_location_dict = get_reverse_geocode(geo_coordinates_string)

        date_now = datetime.today().strftime('%d-%m-%Y')
        # Get the location wise response
        location_response = get_location_response(geo_location_dict, date_now)
        return as_twilio_response(location_response)

    m = re.match(r"^\d+$", incoming_msg)
    if m:
        date_now = datetime.today().strftime('%d-%m-%Y')
        return as_twilio_response(get_by_pincode(m.string, date_now))
    

    return as_twilio_response('Could not understand your message. Please type "help".')


# Helper functions
def as_twilio_response(message: str) -> str:
    resp = MessagingResponse()
    msg = resp.message()
    msg.body(message)
    return str(resp)

def get_response(url):
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0'})
    return response.json()


# Get the address dict
def get_reverse_geocode(coordinates):
    location = geolocator.reverse(coordinates, exactly_one=True)
    address_dict = location.raw['address']
    print("Address Dict:", address_dict)
    return address_dict

def get_location_response_by_pincode(pincode, date_now):
    appointment_api_by_pin = base_url + '/v2/appointment/sessions/public/findByPin?pincode={pincode}&date={date_now}'.format(pincode=pincode, date_now=date_now)
    appointment_data = get_response(appointment_api_by_pin)

    appointment_response = f'''
    '''
    sessions = appointment_data.get("sessions", [])
    if sessions:
        for idx, each in enumerate(sessions):
            serial_number = idx + 1
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
    else:
        appointment_response = "0"
        
    location_message = f'''
Your location pincode is {pincode}.

Available vaccine slots today: {appointment_response}

Visit www.cowin.gov.in to book your vaccination
'''
    return location_message

def get_location_response(geo_location_dict, date_now):
    pincode = geo_location_dict.get('postcode', '')

    return get_location_response_by_pincode(pincode, date_now)



if __name__ == '__main__':
    app.run()
