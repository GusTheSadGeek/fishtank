# ------------- Begin doorSensor.py ------------------ #
import logging
import pycurl     # sudo apt-get install python-pycurl
import json
from StringIO import StringIO

import cfg


def temp_err(minimum, maximum, actual):
    hostname = open('/etc/hostname').read().strip()
    msg = "{h} : Temperature Alert min={m}, max={M}, Actual={a}".format(h=hostname, m=minimum, M=maximum, a=actual)
    send_alert(msg)

def water_alert(minimum, maximum, actual):
    hostname = open('/etc/hostname').read().strip()
    msg = "{h} : Water Alert min={m}, max={M}, Actual={a}".format(h=hostname, m=minimum, M=maximum, a=actual)
    send_alert(msg)

def send_alert(message):
    config = cfg.Config()

    # set this to Application ID from Instapush
    app_id = config.instapush_app_id

    # set this to the Application Secret from Instapush
    app_secret = config.instapush_secret

    # leave this set to DoorAlert unless you named your event something different in Instapush
    push_event = "OverTemp"

    # set this to what you want the push message to say
    push_message = message

    # use StringIO to capture the response from our push API call
    response_buffer = StringIO()

    # use Curl to post to the Instapush API
    curl = pycurl.Curl()

    # set Instapush API URL
    curl.setopt(curl.URL, 'https://api.instapush.im/v1/post')

    # setup custom headers for authentication variables and content type
    curl.setopt(curl.HTTPHEADER,
                ['x-instapush-appid: ' + app_id,
                 'x-instapush-appsecret: ' + app_secret,
                 'Content-Type: application/json'])

    # create a dictionary structure for the JSON data to post to Instapush
    json_fields = {
        'event': push_event,
        'trackers': {
            'message': push_message
        }
    }

    postfields = json.dumps(json_fields)

    # make sure to send the JSON with post
    curl.setopt(curl.POSTFIELDS, postfields)

    # set this so we can capture the resposne in our buffer
    curl.setopt(curl.WRITEFUNCTION, response_buffer.write)

    # uncomment to see the post that is sent
    #curl.setopt(c.VERBOSE, True)

    # Send the event notificaton
    curl.perform()

    # capture the response from the server
    body = response_buffer.getvalue()
    # print the response
    logging.info(body)

    # reset the buffer
    response_buffer.truncate(0)
    response_buffer.seek(0)

    # cleanup
    curl.close()


def main():
    temp_err(10, 20, 30)
    water_alert(60, 70, 71)

if __name__ == '__main__':
    main()
