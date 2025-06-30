
To start the environment you should connect with DBeaver with postgres,
and add .env file and fill these infomations:

GEMINI_API_KEY=
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = '' 
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432

email host get from https://support.google.com/accounts/answer/185833?hl=zh-Hant

You should also add credentials.json from https://console.cloud.google.com/auth/clients?hl=zh-tw&inv=1&invt=Ab0_ow&project=gen-lang-client-0631005725

======================= windows command ======================= 

cd GENAI_BACKEND

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate


------------install----------
pip install django
pip install django psycopg2-binary
pip install djangorestframework
pip install python-dotenv
pip install google-generativeai
pip install geopy
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install python-decouple
pip install django-cors-headers
pip install pillow qrcode requests
pip install qrcode[pil] pillow
pip install google Pillow
pip install google-genai pillow 

$env:OAUTHLIB_INSECURE_TRANSPORT = "1" 
----------run server-------------------
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 8000


------------createsuperuser-------------
python manage.py createsuperuser



=======================================mac command ==================================
cd Desktop/GenAI_backend-main

python3 -m venv venv 

source venv/bin/activate

------install----------
pip install django psycopg2-binary djangorestframework  python-dotenv google-generativeai
pip install geopy
pip install google_auth_oauthlib
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install python-decouple
pip install django-cors-headers
pip install pillow qrcode requests
pip install qrcode[pil] pillow
export OAUTHLIB_INSECURE_TRANSPORT=1 

----------run server-------------------
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 8000




