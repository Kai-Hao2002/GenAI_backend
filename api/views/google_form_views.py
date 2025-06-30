import os
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from api.models import GoogleCredentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


# Start the OAuth authorization process
def google_auth_init(request):
    flow = Flow.from_client_secrets_file(
        '/etc/secrets/credentials.json',  # Render Secret File 
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


# Receive the code returned by Google OAuth, obtain and store the token in DB (only one record)
def google_auth_callback(request):
    state = request.session.get('state')
    if not state:
        return HttpResponse("⚠️ State not found in session.", status=400)

    flow = Flow.from_client_secrets_file(
        '/etc/secrets/credentials.json',
        scopes=[
            'https://www.googleapis.com/auth/forms.body',
            'https://www.googleapis.com/auth/forms.responses.readonly'
        ],
        state=state,
        redirect_uri=request.build_absolute_uri(reverse('google_auth_callback'))
    )
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    credentials = flow.credentials

    # 存資料庫，不綁 user，固定存一筆 id=1
    obj, created = GoogleCredentials.objects.get_or_create(id=1)
    obj.token_json = credentials.to_json()
    obj.save()

    return HttpResponse("✅ Authorization successful, token saved in DB.")


# Load credentials from DB, refresh if expired
def load_credentials():
    try:
        obj = GoogleCredentials.objects.get(id=1)
    except GoogleCredentials.DoesNotExist:
        return None

    creds_data = json.loads(obj.token_json)
    creds = Credentials.from_authorized_user_info(creds_data)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        obj.token_json = creds.to_json()
        obj.save()

    return creds


# Create Google Form with credentials
def create_google_form(form_title, form_fields, form_description):
    creds = load_credentials()
    if not creds:
        return HttpResponse("⚠️ Missing or invalid credentials.", status=401)

    print(f"[create_google_form] Using credentials: {creds}")

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
