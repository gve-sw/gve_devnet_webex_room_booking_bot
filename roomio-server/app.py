#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (c) 2021 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""


__author__ = "Josh Ingeniero <jingenie@cisco.com>"
__copyright__ = "Copyright (c) 2021 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"


from flask import Flask, jsonify, Response, request, render_template, session, request, redirect, url_for, send_from_directory
from webexteamssdk import WebexTeamsAPI
from webexteamssdk.utils import make_attachment
from webexteamssdk.models.cards import AdaptiveCard
from webexteamssdk.models.cards.inputs import Text, Number, Choices
from webexteamssdk.models.cards.components import TextBlock
from webexteamssdk.models.cards.actions import Submit
from DETAILS import *
from tinydb import TinyDB, Query
import logging
import urllib3
import pprint
import json
import re
import sys
import msal
import requests
import datetime
import dateutil.parser
import urllib.parse
import tinydb


app = Flask(__name__, static_folder='static', static_url_path='/roombot/static')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
pp = pprint.PrettyPrinter(indent=2)
api = WebexTeamsAPI(access_token=BOT_TOKEN)
db = TinyDB('tokens.json')


def location_list(building):
    if 'Centre' in building:
        locations = centre_locations
    elif 'Vista' in building:
        locations = vista_locations
    else:
        locations = []
    return locations


class GraphAPI:
    def __init__(self):
        # Create a preferably long-lived app instance which maintains a token cache.
        self.aad_app = msal.ConfidentialClientApplication(
            AAD_ID, authority=AAD_AUTHORITY,
            client_credential=AAD_SECRET,
            # token_cache=...  # Default cache is in memory only.
            # You can learn how to use SerializableTokenCache from
            # https://msal-python.rtfd.io/en/latest/#msal.SerializableTokenCache
        )
        self.result = None

    def request(self, method='GET', payload={}, endpoint=AAD_ENDPOINT, headers=None, sender=None):
        User = Query()
        field = db.search(User.id == sender)
        if field:
            access = field[0]['access']
            refresh = field[0]['refresh']
            # Calling graph using the access token
            access = access.replace('\r', '').replace('\n', '')
            basic_headers = {
                'Authorization': 'Bearer ' + access,
                'Prefer': 'outlook.timezone="Singapore Standard Time"',
                'Content-type': 'application/json'
            }
            if headers:
                final_headers = {**basic_headers, **headers}
            else:
                final_headers = basic_headers
            graph_data = requests.request(
                method,  # Use token to call downstream service
                endpoint,
                headers=final_headers,
                data=payload
            )
            code = graph_data.status_code
            if code == 401:
                print("AUTH ERROR")
                info = f"client_id={AAD_ID}&scope=offline_access%20calendars.readwrite.shared%20user.readbasic.all&refresh_token={refresh}&redirect_uri={urllib.parse.quote(AAD_CALLBACK,safe='')}&grant_type=refresh_token&client_secret={AAD_SECRET}"
                # info = f"client_id={AAD_ID}&scope=offline_access%20calendars.readwrite.shared%20user.readbasic.all&refresh_token={refresh}&redirect_uri=https%3A%2F%2Ftesting.hubslayer.cyou%2Froombot%2FgraphCallback&grant_type=refresh_token&client_secret={AAD_SECRET}"
                response = requests.request('POST',
                                            f'{AAD_AUTHORITY}/oauth2/v2.0/token',
                                            data=info)
                if response.status_code == 400:
                    return None
                pp.pprint(info)
                token_info = {
                    'id': sender,
                    'access': response.json()['access_token'],
                    'refresh': response.json()['refresh_token']
                }
                db.update(token_info, User.id == sender)
                access = access.replace('\r', '').replace('\n', '')
                basic_headers = {
                    'Authorization': 'Bearer ' + access,
                    'Prefer': f'outlook.timezone={TIMEZONE}',
                    'Content-type': 'application/json'
                }
                if headers:
                    final_headers = {**basic_headers, **headers}
                else:
                    final_headers = basic_headers
                graph_data = requests.request(
                    method,  # Use token to call downstream service
                    endpoint,
                    headers=final_headers,
                    data=payload
                )
                code2 = graph_data.status_code
                if code2 == 401:
                    return None
                # print("Graph API call result: ")
                # print(json.dumps(graph_data.json(), indent=2))
                return graph_data.json()
            else:
                # print("Graph API call result: ")
                # print(json.dumps(graph_data.json(), indent=2))
                return graph_data.json()
        else:
            return None


xapi = GraphAPI()


# AUTHENTICATION
@app.route('/', methods=['GET', 'POST'])
def webhook():
    payload = request.json
    if not payload['data']['personEmail'] == BOT_EMAIL:
        pp.pprint(payload)
        info = api.messages.get(payload['data']['id']).to_dict()
        pp.pprint(info)
        if re.search('book', info['text']):
            User = Query()
            field = db.search(User.id == info['personId'])
            if not field:
                return_url = f"{AAD_AUTHORITY}/oauth2/v2.0/authorize?client_id={AAD_ID}&response_type=code&redirect_uri={urllib.parse.quote(AAD_CALLBACK,safe='')}&response_mode=form_post&scope=offline_access%20calendars.readwrite.shared%20user.readbasic.all&state={info['personId']}"
                # return_url = f"https://login.microsoftonline.com/funvolcanoscientist.onmicrosoft.com/oauth2/v2.0/authorize?client_id=2bf1d107-0f51-43ca-8302-e09704dd4d12&response_type=code&redirect_uri=https%3A%2F%2Ftesting.hubslayer.cyou%2Froombot%2FgraphCallback&response_mode=form_post&scope=offline_access%20calendars.readwrite.shared%20user.readbasic.all&state={info['personId']}"
                api.messages.create(toPersonId=payload['data']['personId'], markdown=f'Please access [this]({return_url}) to login to O365')
                api.messages.create(toPersonId=payload['data']['personId'], text='Afterwards, please enter your Webex Personal Meeting Room Link',
                                    attachments=[json.loads(CARD_PAYLOAD_WEBEX)])
            else:
                api.messages.create(toPersonId=payload['data']['personId'], text='Let me help you book a room!',
                            attachments=[json.loads(CARD_PAYLOAD)])
    return jsonify({'info': 'Message callback'})


@app.route('/graphCallback', methods=['GET', 'POST'])
def graph_callback():
    payload = request.form
    code = payload['code']
    id = payload['state']
    pp.pprint(urllib.parse.quote(AAD_CALLBACK,safe=''))
    info = f"client_id={AAD_ID}&scope=offline_access%20calendars.readwrite.shared%20user.readbasic.all&code={code}&redirect_uri={urllib.parse.quote(AAD_CALLBACK,safe='')}&grant_type=authorization_code&client_secret={AAD_SECRET}"
    response = requests.request('POST', f'{AAD_AUTHORITY}/oauth2/v2.0/token',
                                data=info)
    token_info = {
        'id': id,
        'access': response.json()['access_token'],
        'refresh': response.json()['refresh_token']
    }
    pp.pprint(token_info)
    User = Query()
    db.upsert(
        token_info,
        User.id == id
    )
    return render_template('index.html', title='Roomio', header="Logged in to O365!",
                           body="Welcome to Roomio.")


@app.route('/card', methods=['GET', 'POST'])
def card_webhook():
    payload = request.json
    pp.pprint(payload)
    info = api.attachment_actions.get(payload['data']['id']).to_dict()['inputs']
    pp.pprint(api.attachment_actions.get(payload['data']['id']).to_dict())
    sender = payload['data']['personId']
    action = info['action']

    if action == 'webexForm':
        User = Query()
        api.messages.create(toPersonId=sender,
                            markdown=f'Your future meetings will include this meeting room link')
        link = info['webexLink']
        db.update({'webex': link}, User.id == sender)
        return jsonify({'info': 'webex form!'})

    building = info['building']
    date = info['date']
    title = info['title']
    webex = ''
    User = Query()
    field = db.search(User.id == sender)
    if field:
        if 'webex' in field[0].keys():
            webex = field[0]['webex']
            description = info['description'] + f'\n{webex}'
        else:
            api.messages.create(toPersonId=payload['data']['personId'],
                                text='Please enter your Webex Personal Meeting Room Link',
                                attachments=[json.loads(CARD_PAYLOAD_WEBEX)])
            return jsonify({'info': 'webex form add'})

    if action == 'bookingConfirm':
        api.messages.create(toPersonId=sender,
                            markdown=f'Getting your recommendations for {title} on {date}')
        pp.pprint(info)
        info_list = list(info.items())
        emails = [item[1] for item in info_list if re.search('^matching', item[0])]
        attendees = []
        for person in emails:
            temp = {}
            temp['type'] = 'required'
            temp['emailAddress'] = {
                "address": person
            }
            attendees.append(temp)
        locations = location_list(building)

        data = {
            "attendees": attendees,
            "locationConstraint": {
                "isRequired": True,
                "suggestLocation": False,
                "locations": locations
            },
            "timeConstraint": {
                "activityDomain": "work",
                "timeslots": [
                    {
                        "start": {
                            "dateTime": f"{date}{START_TIME}",
                            "timeZone": TIMEZONE
                        },
                        "end": {
                            "dateTime": f"{date}{END_TIME}",
                            "timeZone": TIMEZONE
                        }
                    }
                ]
            },
            "meetingDuration": MEETING_DURATION,
            "maxCandidates": MAX_CANDIDATES,
            "isOrganizerOptional": True,
            "returnSuggestionReasons": True,
            "minimumAttendeePercentage": MIN_PERCENTAGE
        }
        graph_data = xapi.request(endpoint='https://graph.microsoft.com/v1.0/me/findMeetingTimes', payload=json.dumps(data),
                     method='POST', sender=sender)

        if graph_data:
            markdown = [
                'Here are your meeting recommendations:\n'
            ]
            times = graph_data['meetingTimeSuggestions']
            for slot in times:
                temp = {}
                temp['start'] = slot['meetingTimeSlot']['start']['dateTime']
                temp['end'] = slot['meetingTimeSlot']['end']['dateTime']
                temp['startTime'] = datetime.datetime.strptime(slot['meetingTimeSlot']['start']['dateTime'], '%Y-%m-%dT%H:%M:%S.%f0').time()
                temp['endTime'] = datetime.datetime.strptime(slot['meetingTimeSlot']['end']['dateTime'], '%Y-%m-%dT%H:%M:%S.%f0').time()
                temp['rooms'] = slot['locations']
                temp['attendees'] = ','.join(emails)
                temp['availability'] = slot['attendeeAvailability']
                for room in temp['rooms']:
                    query = {
                        "start": temp['start'],
                        "end": temp['end'],
                        "room": room['locationEmailAddress'],
                        "attendees": temp['attendees'],
                        "title": title,
                        "description": description
                    }
                    people = ""
                    for item in temp['availability']:
                        if item['availability'] != 'free':
                            people = people + item['attendee']['emailAddress']['address'].split('@')[0] + ', '
                    # pp.pprint(query)
                    markdown.append(f"* [{temp['startTime']} to {temp['endTime']} - {room['displayName']}]({ENDPOINT_URL}/book?sender={sender}&{urllib.parse.urlencode(query, doseq=False)})\n")
                    if people:
                        markdown.append(f"{people} are not free\n")
            markdown = ''.join(markdown)
            # print(markdown)
            api.messages.create(toPersonId=payload['data']['personId'], markdown=markdown)
            return jsonify({'info': 'find suggestions!'})
        else:
            return_url = f"{AAD_AUTHORITY}/oauth2/v2.0/authorize?client_id={AAD_ID}&response_type=code&redirect_uri={urllib.parse.quote(AAD_CALLBACK,safe='')}&response_mode=form_post&scope=offline_access%20calendars.readwrite.shared%20user.readbasic.all&state={info['personId']}"
            # return_url = f"https://login.microsoftonline.com/funvolcanoscientist.onmicrosoft.com/oauth2/v2.0/authorize?client_id=2bf1d107-0f51-43ca-8302-e09704dd4d12&response_type=code&redirect_uri=https%3A%2F%2Ftesting.hubslayer.cyou%2Froombot%2FgraphCallback&response_mode=form_post&scope=offline_access%20calendars.readwrite.shared%20user.readbasic.all&state={sender}"
            api.messages.create(toPersonId=sender,
                                markdown=f'Please access [this]({return_url}) to login to O365')
            return jsonify({'info': 'not logged in!'})
    elif action == 'bookingForm':
        api.messages.create(toPersonId=sender,
                            markdown=f'Looking up attendees...')
        emails = info['emails'].split(',')
        user_data = xapi.request(endpoint='https://graph.microsoft.com/v1.0/users',
                                 method='GET', sender=sender)

        if user_data:
            user_data = user_data['value']
            people_match = []
            for person in emails:
                matches = [{'title': name['displayName'], 'value': name['mail']} for name in user_data if
                           any([re.search(str(person).lower(), str(name['givenName']).lower()),
                                re.search(str(person).lower(), str(name['displayName']).lower()),
                                re.search(str(person).lower(), str(name['surname']).lower()),
                                re.search(str(person).lower(), str(name['mail']).lower())])]
                people_match.append({
                    'name': person,
                    'matches': matches
                })
            # pp.pprint(people_match)
            body = [
                {
                    "type": "TextBlock",
                    "size": "Medium",
                    "weight": "Bolder",
                    "text": "Name Verification",
                    "horizontalAlignment": "Center"
                },
                {
                    "type": "TextBlock",
                    "text": f"Building: {building}",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": f"Date: {date}",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": f"Title: {title}",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": f"Description: {description}",
                    "wrap": True
                }
            ]
            for person in people_match:
                name = person['name']
                matches = person['matches']
                greeting = {
                    "type": "TextBlock",
                    "text": f"'{name}'",
                    "wrap": True
                }
                select = {
                    "type": "Input.ChoiceSet",
                    "choices": matches,
                    "id": f"matching_{name}"
                }
                body.append(greeting)
                body.append(select)
            card_base = json.loads(CARD_PAYLOAD_BASE)
            submit = {
                "type": "Action.Submit",
                "title": "Submit",
                "data": {
                    'building': info['building'],
                    'date': info['date'],
                    'title': info['title'],
                    'description': info['description'],
                    'action': 'bookingConfirm'
                }
            }
            card_base['content']['body'] = body
            card_base['content']['actions'].append(submit)
            # pp.pprint(card_base)
            api.messages.create(toPersonId=payload['data']['personId'], text='Let me help you book a room!',
                                attachments=[card_base])
        else:
            return_url = f"{AAD_AUTHORITY}/oauth2/v2.0/authorize?client_id={AAD_ID}&response_type=code&redirect_uri={AAD_CALLBACK}&response_mode=form_post&scope=offline_access%20calendars.readwrite.shared%20user.readbasic.all&state={sender}"
            # return_url = f"https://login.microsoftonline.com/funvolcanoscientist.onmicrosoft.com/oauth2/v2.0/authorize?client_id=2bf1d107-0f51-43ca-8302-e09704dd4d12&response_type=code&redirect_uri=https%3A%2F%2Ftesting.hubslayer.cyou%2Froombot%2FgraphCallback&response_mode=form_post&scope=offline_access%20calendars.readwrite.shared%20user.readbasic.all&state={sender}"
            api.messages.create(toPersonId=sender,
                                markdown=f'Please access [this]({return_url}) to login to O365')
            return jsonify({'info': 'not logged in!'})

    return jsonify({'info': 'Your meeting has been booked! Thanks for using Roomio!'})


@app.route('/book', methods=['GET', 'POST'])
def room_booking():
    payload = request.args
    pp.pprint(payload)
    attendees = []
    people = payload['attendees'].split(',')
    people.append(payload['room'])
    pp.pprint(people)
    for person in people:
        temp = {}
        temp = {
            "emailAddress": {
                "address": person
            },
            "type": "required"
        }
        attendees.append(temp)
    data = {
        "subject": payload['title'],
        "body": {
            "contentType": "HTML",
            "content": payload['description']
        },
        "start": {
            "dateTime": payload['start'],
            "timeZone": TIMEZONE
        },
        "end": {
            "dateTime": payload['end'],
            "timeZone": TIMEZONE
        },
        "location": {
            "locationEmailAddress": payload['room'],
            "displayName": payload['room']
        },
        "attendees": attendees
    }
    graph_data = xapi.request(endpoint='https://graph.microsoft.com/v1.0/me/calendar/events', payload=json.dumps(data),
                              method='POST', sender=payload['sender'])
    pp.pprint(graph_data)
    return render_template('index.html', title='Roomio', header="Your meeting has been booked!",
                           body="Thanks for using Roomio.")


@app.route('/test', methods=['GET', 'POST'])
def test():
    return render_template('index.html', title='Roomio', header="Roomio",
                           body="Test message")


@app.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5030', debug=True)
