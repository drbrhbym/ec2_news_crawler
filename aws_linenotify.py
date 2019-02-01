import requests
import os
#pip install requests
def lineNotify(msg):
    url = "https://notify-api.line.me/api/notify"
    token = "*****************************"
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = {'message': msg}
    r = requests.post(url, headers=headers, params=payload)
    return r.status_code

# token = "*****************************"
