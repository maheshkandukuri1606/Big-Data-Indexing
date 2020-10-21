from google.oauth2 import id_token
from google.auth.transport import requests

def validate_token(token):
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), '1063884087527-psdchsl15ekh5bjcfibq9erfcebgjhpo.apps.googleusercontent.com')
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        userid = idinfo['sub']
        return True
    except ValueError:
        return False