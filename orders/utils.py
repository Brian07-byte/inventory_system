import requests
import base64
from django.conf import settings

def get_mpesa_access_token():
    """
    Fetches OAuth token from Safaricom Daraja API
    """
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET

    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    auth = (consumer_key, consumer_secret)
    
    response = requests.get(url, auth=auth)
    return response.json().get("access_token")
