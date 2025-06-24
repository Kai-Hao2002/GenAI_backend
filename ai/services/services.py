import os
import re
import json
from google import genai
from dotenv import load_dotenv
import openai
import google.generativeai as genai
from ai.prompt.promt import (
    get_event_generation_prompt,get_task_assignment_generation_prompt,
    get_venue_suggestion_generation_prompt,get_registration_form_generation_prompt,
    get_invitation_generation_prompt,get_social_post_generation_prompt,
    get_poster_copy_generation_prompt,get_poster_image_prompt
)

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
openai.api_key = os.getenv("OPENAI_API_KEY")  


# Remove possible Markdown code block
def parse_gemini_response(text: str) -> dict:
    cleaned_text = re.sub(r"^```json\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    return json.loads(cleaned_text)
    
def generate_event_from_gemini(event_data: dict) -> dict:
    prompt = get_event_generation_prompt(event_data)

    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)

    try:
        result = parse_gemini_response(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Response is not valid JSON:\n{response.text}\nError: {e}")

    return result

def generate_task_assignment_from_gemini(event_data: dict) -> dict:
    prompt = get_task_assignment_generation_prompt(event_data)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)

    try:
        return parse_gemini_response(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Response is not valid JSON:\n{response.text}\nError: {e}")
    

def generate_venue_suggestion_from_gemini(event_data: dict) -> dict:
    prompt = get_venue_suggestion_generation_prompt(event_data)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)

    try:
        return parse_gemini_response(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Response is not valid JSON:\n{response.text}\nError: {e}")

def generate_registration_form_from_gemini(event_data: dict) -> dict:
    prompt = get_registration_form_generation_prompt(event_data)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)

    try:
        return parse_gemini_response(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Response is not valid JSON:\n{response.text}\nError: {e}")
    
def generate_invitation_from_gemini(event_data: dict) -> dict:
    prompt = get_invitation_generation_prompt(event_data)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)

    try:
        return parse_gemini_response(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Response is not valid JSON:\n{response.text}\nError: {e}")
    

def generate_social_post_gemini(event_data: dict) -> dict:
    prompt = get_social_post_generation_prompt(event_data)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)

    try:
        return parse_gemini_response(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Response is not valid JSON:\n{response.text}\nError: {e}")
    

def generate_poster_text_gemini(event_data: dict) -> dict:
    prompt = get_poster_copy_generation_prompt(event_data)
    model = genai.GenerativeModel("gemini-2.0-flash") 
    response = model.generate_content(prompt)

    try:
        return parse_gemini_response(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Response is not valid JSON:\n{response.text}\nError: {e}")


def generate_poster_image_openai(event_data: dict) -> str:
    prompt = get_poster_image_prompt(event_data) 

    response = openai.Image.create(
        prompt=prompt,
        model="dall-e-3",
        n=1,
        size="1024x1024",
        response_format="b64_json"
    )

    return response['data'][0]['b64_json']