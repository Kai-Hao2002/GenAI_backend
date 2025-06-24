import os
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.conf import settings

from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


# Start the OAuth authorization process
def google_auth_init(request):
    flow = Flow.from_client_secrets_file(
        'credentials.json',  # Google Cloud Console 的 client_secret
        scopes=[
            'https://www.googleapis.com/auth/forms.body',
            'https://www.googleapis.com/auth/forms.responses.readonly'
        ],
        redirect_uri=request.build_absolute_uri(reverse('google_auth_callback'))
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        include_granted_scopes='true'
    )
    request.session['state'] = state
    return HttpResponseRedirect(authorization_url)

# Receive the code returned by Google OAuth, obtain and store the token
def google_auth_callback(request):
    state = request.session['state']
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=[
            'https://www.googleapis.com/auth/forms.body',
            'https://www.googleapis.com/auth/forms.responses.readonly'
        ],
        state=state,
        redirect_uri=request.build_absolute_uri(reverse('google_auth_callback'))
    )
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    credentials = flow.credentials

    #Store token 
    with open('token.json', 'w') as token_file:
        token_file.write(credentials.to_json())

    return HttpResponse("✅ Authorization successful, token stored")



def create_google_form(creds, form_title, form_fields, form_description):
    service = build('forms', 'v1', credentials=creds)

    # 1. Create a form, only info.title can be set
    form_data = {
        "info": {
            "title": form_title,
        }
    }
    result = service.forms().create(body=form_data).execute()

    form_id = result['formId']

    # 2. Use batchUpdate to update description and add a new title
    requests = []

    # update description
    requests.append({
        "updateFormInfo": {
            "info": {
                "description": form_description
            },
            "updateMask": "description"
        }
    })

    # Add new topic
    for idx, field in enumerate(form_fields):
        requests.append({
            "createItem": {
                "item": {
                    "title": field["description"],
                    "questionItem": {
                        "question": {
                            "required": True,
                            "textQuestion": {}
                        }
                    }
                },
                "location": {
                    "index": idx
                }
            }
        })

    service.forms().batchUpdate(formId=form_id, body={"requests": requests}).execute()


    registration_url = f"https://docs.google.com/forms/d/{form_id}/viewform"

    return registration_url


def load_credentials():
    if not os.path.exists('token.json'):
        return None

    with open('token.json', 'r') as token_file:
        creds_data = json.load(token_file)
        creds = Credentials.from_authorized_user_info(creds_data)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open('token.json', 'w') as token_file:
                token_file.write(creds.to_json())
        return creds
