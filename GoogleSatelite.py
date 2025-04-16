import os

import geocoder
import requests
from PIL import Image
from io import BytesIO

# ss
API_KEY = os.getenv('EXPO_PUBLIC_GOOGLE_MAPS_API_KEY')

g = geocoder.ip('me')
print(f"Current location: {g.latlng}")


lat, lng = g.latlng[0], g.latlng[1] # Replace with actual lat/lng


def getDestination(location_name):
    # Google Geocoding API endpoint
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location_name}&key={API_KEY}"

    # Send GET request
    response = requests.get(url)
    data = response.json()

    # Extract latitude and longitude
    if data['status'] == 'OK':
        print(f"📍 Latitude: {lat}, Longitude: {lng}")
        return data['results'][0]['geometry']['location']['lat'], data['results'][0]['geometry']['location']['lng']
    else:
        print("❌ Location not found:", data['status'])
        return 0,0