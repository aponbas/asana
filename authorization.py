# Copyright 2023 by Sebastiaan Apon (github.com/aponbas).
# All rights reserved.
# This file is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.

from base64 import b64encode
from hashlib import sha256
import json
import random
import requests
import string

# After creating an app in Asana (https://app.asana.com/0/my-apps) you will find the "Client ID" and "Client secret"
# under "Basic information".

client_id = "<client_id>"  # TODO fill this in
client_secret = "<client_secret>"  # TODO fill this in

# You will also need a self-generated random string, at least 43 and at most 128 characters long, using only:
# a-z A-Z 0-9 - . _ ~
# You can use the function or generate something yourself

code_verifier = ''.join(random.choices(string.ascii_lowercase +
                                       string.ascii_uppercase +
                                       string.digits +
                                       "-._~", k=random.randrange(43, 129)))

# This code_verifier needs to be base64 and SHA256 encoded to form the code_challenge
h = sha256()
h.update(code_verifier.encode())
b64bytes = b64encode(h.digest())
code_challenge = b64bytes.decode()

# The method is always SHA256. In the parameters this is just called "S256".
code_challenge_method = "S256"

# URI to your app or website. After authorization, you'll be redirected to this URI with the code that you need later in
# parameters of the URI.
redirect_uri = "<your URI>"  # TODO fill this in

# To check if the response matches the request, another random string is used. Check this with the parameter in the
# URI that you get redirected to after authorization.
state = ''.join(random.choices(string.ascii_lowercase +
                               string.ascii_uppercase +
                               string.digits, k=random.randrange(32, 64)))
print(f"This is the state: {state}")

# Now we make the URL you will have to click.
url = f"https://app.asana.com/-/oauth_authorize?" \
      f"client_id={client_id}" \
      f"&redirect_uri={redirect_uri}" \
      f"&response_type=code" \
      f"&state={state}" \
      f"&code_challenge_method={code_challenge_method}" \
      f"&code_challenge={code_challenge}" \
      f"&scope=default"
print(f"Click this URL: {url}")
# Click this URL manually and authorize. Find the "code" in the parameters of the URI you get redirected to.
# Check if the "state" in the parameters is equal to the state printed above. If not: don't use this code.
# The code will have this form:
# 1%2F123412341234%3A4e4f6c75636b5448495374696d65
# Note that this is HTML encoded, you'll have to decode it to form something like this:
# 1/123412341234:4e4f6c75636b5448495374696d65

code = "<code from the URI>"  # TODO fill this in
body = {
    "grant_type": "authorization_code",
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uri": redirect_uri,
    "code": code,
    # "code_verifier": code_verifier  # The Asana documentation says you have to add this. Don't, or it'll error.
}

# Now we retrieve the refresh_token
token_url = "https://app.asana.com/-/oauth_token"
response = requests.post(url=token_url, data=body)
refresh_token = json.loads(response.content.decode("UTF-8"))["refresh_token"]
print(f"This is the refresh token:\n{refresh_token}")

# Store this refresh_token in a secure location for future use.
# The refresh_token can be used to get an access_token.
# For future API requests, you only need the client_id, client_secret and this refresh_token.
# Below is an example using the access_token.

# First get an access_token
body = {
    "grant_type": "refresh_token",
    "client_id": client_id,
    "client_secret": client_secret,
    "refresh_token": refresh_token,
}

token_url = "https://app.asana.com/-/oauth_token"
response = requests.post(url=token_url, data=body)

access_token = json.loads(response.content.decode("UTF-8"))["access_token"]
# The access_token can be used to retrieve data with the API (example below). It expires after 1 hour.
# Now call the API for data. This example retrieves metadata from all your workspaces.

host = "https://app.asana.com/api/1.0/"
endpoint = "workspaces"  # Find other endpoints in the documentation: https://developers.asana.com/reference
url = host + endpoint

headers = {"accept": "application/json",
           "authorization": f"Bearer {access_token}"}

params = {"limit": 100}

response = requests.get(url=url, headers=headers, params=params)
content = json.loads(response.content.decode("UTF-8"))
output = content["data"]

# Including pagination
while content.get("next_page"):
    params["offset"] = content["next_page"]["offset"]
    response = requests.get(url=url, headers=headers, params=params)
    content = json.loads(response.content.decode("UTF-8"))
    output += content["data"]

print(output)
