import os
import re
import json
from dotenv import load_dotenv
import google.generativeai as genai
from ai.prompt.promt import get_event_generation_prompt,get_task_assignment_generation_prompt

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def parse_gemini_response(text: str) -> dict:
    # 去除可能的 ```json ... ``` Markdown 包裹，只保留純 JSON 字串
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