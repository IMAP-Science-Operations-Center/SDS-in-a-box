import requests
import json
import os
import datetime

COGNITO_CLIENT_ID = "eapgusfsbcep6ph6ukd7omo7v"
API_URL = "https://hbzxte4isrjr277pxtt5mmg4jm0vkqtx.lambda-url.us-west-2.on.aws/"

USER_TOKEN = None
LOGIN_TIME = None

def _set_user_token(t):
    global USER_TOKEN
    global LOGIN_TIME

    LOGIN_TIME = datetime.datetime.now()
    USER_TOKEN = t


def _get_user_token():
    global USER_TOKEN
    global LOGIN_TIME
    if LOGIN_TIME is None:
        print("New login needed.  Login is valid for 60 minutes.")
    elif (datetime.datetime.now() - LOGIN_TIME).total_seconds() >= 3600:
        print("Login expired.  Please log in again.")
    else:
        return USER_TOKEN

    t = get_sdc_token()

    return t


def get_sdc_token(user_name=None, password=None):
    '''
    This function authenticates the user.  An access token is automatically stored in the USER_TOKEN
    variable in this file, and functions will attempt to find a valid user token in that variable.

    :param user_name: User's SDC username
    :param password: User's SDC password

    :return: A string that also gets stored in the USER_TOKEN variable in this file.  You don't need this string unless
             you plan on making your own API calls, using functions outside of this file.
    '''
    global COGNITO_CLIENT_ID
    if user_name is None:
        user_name = input("Username:")
    if password is None:
        import getpass
        password = getpass.getpass("Password for " + user_name + ":")

    authentication_url = "https://cognito-idp.us-west-2.amazonaws.com/"
    authentication_headers = {'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth',
                              'Content-Type': 'application/x-amz-json-1.1'}
    data = json.dumps({"ClientId": COGNITO_CLIENT_ID, "AuthFlow": "USER_PASSWORD_AUTH",
                       "AuthParameters": {"USERNAME": user_name, "PASSWORD": password}})

    # Attempt to grab the SDC token.
    try:
        token_response = requests.post(authentication_url, data=data, headers=authentication_headers)
        t = token_response.json()['AuthenticationResult']['AccessToken']
    except KeyError:
        print("Invalid username and/or password.  Please try again.  ")
        return

    _set_user_token(t)

    return t    
	

def execute_api(**kwargs):
    global API_URL
    token = _get_user_token()
    headers = {"Authorization": token}
    query_url = API_URL + "?"
    query_parameters = []
    for kw in kwargs:
        query_parameters.append(kw + "=" + str(kwargs[kw]))
    query_parameters = '&'.join(query_parameters)
    query_url_with_parameters = query_url + query_parameters
    try:
        response = requests.get(query_url_with_parameters, headers=headers)
    except Exception as e:
        print(f"Could not finish query due to error {str(e)}")
        return
    print(response)
    return response.json()