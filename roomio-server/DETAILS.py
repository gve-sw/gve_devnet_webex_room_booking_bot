# Webex Bot
BOT_ID = 'BOTID'
BOT_TOKEN = 'BOTTOKEN'
BOT_EMAIL = 'yourbotemail@webex.bot'

ENDPOINT_URL = "https://myexample.site.com/"  # Where you are hosting your bot
AAD_ID = 'CLIENT ID'  # Your application's Client ID on AAD
AAD_SECRET = 'CLIENT SECRET'  # Your application's Client Secret on AAD
AAD_AUTHORITY = 'https://login.microsoftonline.com/YOURDOMAIN'  # Your organisation's domain login url
AAD_ENDPOINT = "https://graph.microsoft.com/v1.0/users/me"
AAD_CALLBACK = "https://myexample.site.com/graphCallback"  # Your Redirect URI

TIMEZONE = "Singapore Standard Time"
START_TIME = "T09:00:00"
END_TIME = "T18:00:00"
MEETING_DURATION = "PT1H"
MAX_CANDIDATES = 10
MIN_PERCENTAGE = 50

centre_locations = [

                {
                    "resolveAvailability": True,
                    "displayName": "Centre 4F",
                    "locationEmailAddress": "c4@email.com"
                },
                {
                    "resolveAvailability": True,
                    "displayName": "Centre 2F",
                    "locationEmailAddress": "c2@email.comm"
                }
            ]

vista_locations = [

                {
                    "resolveAvailability": True,
                    "displayName": "Vista 5F",
                    "locationEmailAddress": "v5f@email.com"
                },
                {
                    "resolveAvailability": True,
                    "displayName": "Vista 5D",
                    "locationEmailAddress": "v5d@email.com"
                },
                {
                    "resolveAvailability": True,
                    "displayName": "Vista 5G",
                    "locationEmailAddress": "v5g@email.com"
                }
            ]

CARD_PAYLOAD = """{
      "contentType": "application/vnd.microsoft.card.adaptive",
      "content": {
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "type": "AdaptiveCard",
    "version": "1.2",
    "body": [
        {
            "type": "TextBlock",
            "size": "Medium",
            "weight": "Bolder",
            "text": "Room Booking Details",
            "horizontalAlignment": "Center"
        },
        {
            "type": "TextBlock",
            "text": "Building",
            "wrap": true
        },
        {
            "type": "Input.ChoiceSet",
            "choices": [
                {
                    "title": "Centre Building",
                    "value": "Centre"
                },
                {
                    "title": "Vista Building",
                    "value": "Vista"
                }
            ],
            "id": "building"
        },
        {
            "type": "TextBlock",
            "text": "Date",
            "wrap": true
        },
        {
            "type": "Input.Date",
            "id": "date"
        },
        {
            "type": "TextBlock",
            "text": "Attendee names/usernames (separated by commas)",
            "wrap": true
        },
        {
            "type": "Input.Text",
            "placeholder": "mark,sandra",
            "style": "Email",
            "maxLength": 0,
            "id": "emails",
            "isMultiline": true
        },
        {
            "type": "TextBlock",
            "text": "Event Title",
            "wrap": true
        },
        {
            "type": "Input.Text",
            "placeholder": "Team Meeting",
            "id": "title"
        },
        {
            "type": "TextBlock",
            "text": "Event Description",
            "wrap": true
        },
        {
            "type": "Input.Text",
            "placeholder": "Talking about the new initiatives",
            "id": "description"
        }
    ],
    "actions": [
        {
            "type": "Action.Submit",
            "title": "Submit",
            "data": {
                "action": "bookingForm"
            }
        }
    ]
}
    }"""


CARD_PAYLOAD_BASE = """{
      "contentType": "application/vnd.microsoft.card.adaptive",
      "content": {
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "type": "AdaptiveCard",
    "version": "1.2",
    "body": [
    ],
    "actions": [
    ]
}
    }"""

CARD_PAYLOAD_WEBEX = """{
      "contentType": "application/vnd.microsoft.card.adaptive",
      "content": {
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "type": "AdaptiveCard",
    "version": "1.2",
    "body": [
        {
            "type": "TextBlock",
            "size": "Medium",
            "weight": "Bolder",
            "text": "After logging in, enter your Webex Meeting Room Link",
            "horizontalAlignment": "Center"
        },
        {
            "type": "Input.Text",
            "placeholder": "https://webex.com/meet/username",
            "style": "text",
            "maxLength": 0,
            "id": "webexLink",
            "isMultiline": false
        }
    ],
    "actions": [
        {
            "type": "Action.Submit",
            "title": "Submit",
            "data": {
                "action": "webexForm"
            }
        }
    ]
}
    }"""