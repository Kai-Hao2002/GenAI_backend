def get_event_generation_prompt(event_data: dict) -> str:
    system_prompt = (
        "You are a skilled activities planner specializing in student events.\n"
        "Given an input JSON describing the event goal, type, date, budget, target audience, and atmosphere, "
        "brainstorm and generate exactly 5 creative event names as a list, and detailed event description, and five slogans,"
        "suggested event duration, suggested time, expected attendees.\n"
        "Event names must be imaginative and clearly connected to the event's goal, audience, type, and atmosphere.\n"
        "The description should cover the event's purpose, vibe, and benefits for attendees, and donot contains event name\n"
        "The slogans should base what the event goal is and atmosphere. \n"
        "Output the entire response strictly in JSON format ONLY, with these keys: "
        "'name' (list of 5 strings), "
        "'description' (string), "
        "'expected_attendees' (integer), "
        "'suggested_time' (string), "
        "'suggested_event_duration' (string), "
        "'slogan' (string).\n"
        "Do NOT include any explanations, extra text, or formatting beyond the JSON response.\n"
    )
    #slogan 產出幾乎一樣


    user_prompt = (
        f"Event goal: {event_data.get('goal')}\n"
        f"Type: {event_data.get('type')}\n"
        f"Date: {event_data.get('date')}\n"
        f"Budget: {event_data.get('budget')}\n"
        f"Audience: {event_data.get('target_audience')}\n"
        f"Event atmosphere: {event_data.get('atmosphere')}\n"
    )

    return system_prompt + "\n" + user_prompt

def get_task_assignment_generation_prompt(event_data: dict) -> str:
    event = event_data.get("event", {})

    system_prompt = (
        "You are a professional event task planning assistant. Based on the provided event data and task assignment preferences, "
        "generate a list of recommended roles (tasks) for the event.\n\n"
        "You must infer appropriate roles and estimated staff counts depending on the **event type** and **expected number of attendees**. "
        "Use the specified **timeline type** to format time fields. Return the result in **pure JSON format only**, with no explanations or extra text.\n\n"

        "-----------------------------------------\n"
        "ROLE ASSIGNMENT LOGIC:\n"
        "1. Use the following role sets depending on the event type:\n"
        "- \"Workshop / Training\": [\"facilitator\", \"assistant\", \"tech_support\", \"material_handler\", \"time_keeper\"]\n"
        "- \"Social / Networking\": [\"host\", \"greeter\", \"logistics\", \"photographer\", \"music_dj\"]\n"
        "- \"Performance / Showcase\": [\"stage_manager\", \"lighting\", \"sound_engineer\", \"usher\", \"safety_officer\"]\n"
        "- \"Speech / Seminar\": [\"emcee\", \"speaker_handler\", \"registration_staff\", \"audiovisual_support\", \"time_keeper\"]\n"
        "- \"Recreational / Entertainment\": [\"activity_leader\", \"crowd_control\", \"logistics\", \"vendor_liaison\", \"security\"]\n"
        "- \"Market / Exhibition\": [\"booth_coordinator\", \"vendor_helper\", \"floor_manager\", \"map_distributor\", \"ticketing\"]\n"
        "- \"Competition / Challenge\": [\"referee\", \"score_keeper\", \"participant_handler\", \"tech_support\", \"logistics\"]\n\n"

        "2. Estimate staff count based on expected_attendees:\n"
        "- Usually 1 staff per 50 attendees for general roles.\n"
        "- Technical roles and hosts may have fixed counts (e.g. 1 or 2).\n"
        "- Use reasonable judgment.\n\n"

        "3. Time format:\n"
        "- If \"timeline_type\" is \"absolute\", use \"start_time\" and \"end_time\" in ISO 8601 format.\n"
        "- If no start time is provided, omit time fields and add a top-level key:\n"
        "  \"note\": \"Start time missing\"\n\n"

        "-----------------------------------------\n"
        "OUTPUT FORMAT (always JSON):\n"
        "{\n"
        "  \"event_id\": <event id>,\n"
        "  \"task_summary_by_role\": [\n"
        "    {\n"
        "      \"role\": \"<role_code>\",\n"
        "      \"description\": \"<short English task description>\",\n"
        "      \"count\": <estimated_staff_count>,\n"
        "      \"start_time\": \"...\",  // optional\n"
        "      \"end_time\": \"...\"      // optional\n"
        "    }\n"
        "  ],\n"
        "  \"note\": \"Start time missing\"  // if applicable\n"
        "}\n"
    )

    user_prompt = (
        f"event_id: {event.get('event_id')}\n"
        f"event_name: {event.get('event_name')}\n"
        f"type: {event.get('type')}\n"
        f"start_time: {event.get('start_time')}\n"
        f"end_time: {event.get('end_time')}\n"
        f"expected_attendees: {event.get('expected_attendees')}\n"
    )

    return system_prompt + "\n\n" + user_prompt

def get_venue_suggestion_generation_prompt(event_data: dict) -> str:
    event = event_data.get("event", {})
    venue = event_data.get("venue_suggestion", {})

    system_prompt = system_prompt = """
                                    You are an expert venue recommendation assistant for events.

                                    You will receive:
                                    - An event object: name, type, expected attendees, time, budget, and audience.
                                    - A specific user-defined address (center location), search radius (in kilometers), and the location's latitude/longitude.

                                    Your task:
                                    1. Suggest up to 5 realistic venues within the radius from the provided coordinates that are suitable for the event.
                                    2. Return results strictly as JSON with a `venue_suggestions` list.
                                    3. Each venue must include:
                                        - name
                                        - capacity
                                        - transportation_score (1 to 5, based on ease of public access)
                                        - is_outdoor (true/false)

                                    Important Notes:
                                    - The venue name must exactly match the official name used on Google Maps to ensure accurate geolocation.
                                    - Avoid abbreviations or alternative names; use the full official venue name as found on Google Maps.
                                    - Prefer real-world, well-known, or publicly accessible venues, and also match event type
                                    - remember to create 5 venues!
                                    - Rental cost and capacity must reflect reality: if no rental service or information is available, leave the rental_cost blank.
                                    - Venue type should match the event type:

                                        | Event Type                     | Suitable Venues Examples                        |
                                        |-------------------------------|--------------------------------------------------|
                                        | Workshop / Training           | Classrooms, co-working spaces, meeting rooms    |
                                        | Social / Networking           | Cafés, lounges, rooftop spaces, bars            |
                                        | Performance / Showcase        | Theaters, plazas, stages, exhibition centers    |
                                        | Speech / Seminar              | Auditoriums, conference halls, libraries        |
                                        | Recreational / Entertainment  | Parks, entertainment venues, amusement areas    |
                                        | Market / Exhibition           | Exhibition halls, gymnasiums, open plazas       |
                                        | Competition / Challenge       | Gyms, courts, outdoor spaces, arenas            |

                                    - Make sure the venue can realistically accommodate the expected number of attendees.
                                    - Prioritize venues with high transportation access and matching audience profiles.
                                    """


    user_prompt = (
        f"Event data:\n"
        f"Name: {event.get('name')}\n"
        f"Type: {event.get('type')}\n"
        f"Expected Attendees: {event.get('expected_attendees')}\n"
        f"Start Time: {event.get('start_time')}\n"
        f"End Time: {event.get('end_time')}\n"
        f"Budget: {event.get('budget')}\n"
        f"Target Audience: {event.get('target_audience')}\n\n"
        f"User-defined center location: {venue.get('name')}\n"
        f"Search radius: {venue.get('radius_km')} km\n"
    )

    return system_prompt.strip() + "\n\n" + user_prompt.strip()


def get_registration_form_generation_prompt(event_data: dict) -> str:

    event = event_data.get("event", {})
    venue = event_data.get("venue", {})

    system_prompt = (
            "You are a professional event registration form designer.\n"
            "Based on the provided event information, generate a structured JSON object that includes:\n\n"
            "1. An event_intro: a short and engaging summary (max 2 sentences) that appears at the top of the form to explain why the user should register.\n"
            "2. A form_title: a concise, action-oriented title for the form (e.g., \"Register for the AI Hackathon!\").\n"
            "3. A form_fields list: expected input fields that attendees need to fill in. Each field must include:\n"
            "   - registration_name: a lowercase slug in English (e.g., \"email\", \"team_name\")\n"
            "   - description: a short user-facing label (can be in the event's language)\n\n"
            "Guidelines:\n"
            "- Always include basic fields like name and email.\n"
            "- Infer additional fields based on the event type, target audience.\n"
            "- If the event involves teams, consider adding \"team_name\".\n"
            "- If relevant, include fields like \"school\", \"tshirt_size\", or \"dietary_preferences\".\n\n"
            "Output must be in **pure JSON** format with no extra explanations or markdown.\n"
            "OUTPUT FORMAT (always JSON):\n"
            "{\n"
            "  \"registration-list\": [\n"
            "    {\n"
            "      \"event_intro\": \"string\",\n"
            "      \"form_title\": \"string\",\n"
            "      \"form_fields\": [\n"
            "        { \"registration_name\": \"string\", \"description\": \"string\" },\n"
            "        ...\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}\n"

    )

    user_prompt = (

        f"event_name: {event.get('event_name')}\n"
        f"event_type: {event.get('event_type')}\n"
        f"event_start_time: {event.get('start_time')}\n"
        f"event_end_time: {event.get('end_time')}\n"
        f"event_description: {event.get('event_description')}\n"
        f"expected_attendees: {event.get('expected_attendees')}\n"
        f"targeted_audiences: {event.get('targeted_audiences')}\n"
        f"event_slogan: {event.get('event_slogan')}\n"
        f"event_address_name: {venue.get('name')}\n"
        f"event_address: {venue.get('address')}\n"
    )


    return system_prompt + "\n\n" + user_prompt


def get_invitation_generation_prompt(event_data: dict) -> str:

    event = event_data.get("event", {})
    venue = event_data.get("venue", {})
    invitation = event_data.get("invitation", {})
    registration = event_data.get("registration", {})


    system_prompt = (
                    "You are an expert email invitation writer.\n"
                    "Your task is to generate a personalized, emotionally compelling invitation "
                    "email subject and body for each recipient based on the provided event, recipient information and also wirite the registration link.\n\n"

                    "Input:\n"
                    "- Event information: event_id, event_name, event_description, event_slogan, event_type, "
                    "event_start_time, event_end_time, event_address_name, event_address\n"
                    "- A list of recipients with their names\n"
                    "- Writing constraints: words_limit, tone, language\n\n"

                    "Your Goal:\n"
                    "Write a short email subject and a complete invitation email body for each recipient, "
                    "using the appropriate tone and language, and respecting the word limit.\n\n"

                    "Guidelines:\n"
                    "- Personalize each message with the receiver_name in the greeting.\n"
                    "- Clearly convey what the event is, why it matters, when and where it takes place.\n"
                    "- Creatively include the slogan if provided.\n"
                    "- Match the tone: e.g., formal, warm, cheerful, inspirational, or neutral.\n"
                    "- Use the specified language and invitation style appropriate to it.\n"
                    "- Body content should fit within the words_limit.\n"
                    "- Do not include markdown, HTML, or explanations — plain text only.\n\n"

                    "OUTPUT FORMAT (always JSON):\n"
                    "{\n"
                    '  "invitation_list": [\n'
                    "    {\n"
                    '      "invitation_letter_subject": "string",\n'
                    '      "invitation_letter_body": "string"\n'
                    "    },\n"
                    "    ... (one per recipient)\n"
                    "  ]\n"
                    "}\n"
                )



    user_prompt = (

        f"event_name: {event.get('event_name')}\n"
        f"event_description: {event.get('event_description')}\n"
        f"event_slogan: {event.get('event_slogan')}\n"
        f"event_type: {event.get('event_type')}\n"
        f"event_start_time: {event.get('start_time')}\n"
        f"event_end_time: {event.get('end_time')}\n"
        f"event_location: {venue.get('name')}\n"
        f"event_address: {venue.get('address')}\n"
        f"event_registration_link: {registration.get('registration_url')}\n"
        f"receiver_name: {invitation.get('receiver_name')}\n"
        f"words_limit: {invitation.get('words_limit')}\n"
        f"tone: {invitation.get('tone')}\n"
        f"language: {invitation.get('language')}\n"
        

    )


    return system_prompt + "\n\n" + user_prompt


def get_social_post_generation_prompt(event_data: dict) -> str:

    event = event_data.get("event", {})
    venue = event_data.get("venue", {})
    registration = event_data.get("registration", {})
    social_post = event_data.get("social_post", {})
    


    system_prompt = (
                    "You are a professional social media copywriting assistant." 
                    "Your task is to generate creative, engaging, and platform-tailored social media posts based on the provided event details and content strategy preferences.\n\n"
                    "Your response must follow these guidelines:\n"
                    "- Return a JSON object in the following format: {\"post_list\": [...]}\n"
                    "- Each item in post_list should be a post object containing:\n"
                    "  - \"content\": A social media caption that includes relevant event details (such as event name, date/time, location, and registration link), uses a compelling hook based on the given hook_type, matches the tone, and ends with a clear call to action.\n"
                    "  - \"hashtag\": A list of custom, relevant hashtags that reflect the event's theme, location, and target audience. Avoid generic or unrelated trending tags.\n\n"
                    "Other rules to follow:\n"
                    "- The writing style should adapt to the platform (e.g., Instagram, Facebook, LinkedIn) and tone (e.g., fun, professional, inspirational).\n"
                    "- If include_emoji is true, use emojis according to the specified emoji_level (low, medium, high) to enhance but not overwhelm the message.\n"
                    "- Use any provided power_words and hashtag_seeds creatively and naturally in the post.\n"
                    "- Incorporate all essential event info without sounding robotic or repetitive.\n"
                    "- Avoid repeating post content across the list.\n\n"
                    "Output only the final JSON, without any explanation or extra text. For example:\n"
                    "{\n"
                    "  \"post_list\": [\n"
                    "    {\n"
                    "      \"content\": \"🚀 Ready to unleash your AI potential? Join the AI Hackathon on July 20th at National Taiwan University! 24 hours of coding, creativity, and innovation await. Sign up now 👉 https://example.com/hackathon\",\n"
                    "      \"hashtag\": [\"#AIHackathon\", \"#CreativeChallenge\", \"#NTU\", \"#Hackathon2025\"]\n"
                    "    }\n"
                    "  ]\n"
                    "}"
                )




    user_prompt = (

        f"event_name: {event.get('event_name')}\n"
        f"event_description: {event.get('event_description')}\n"
        f"event_slogan: {event.get('event_slogan')}\n"
        f"event_type: {event.get('event_type')}\n"
        f"event_target_audience: {event.get('target_audience')}\n"
        f"event_start_time: {event.get('start_time')}\n"
        f"event_end_time: {event.get('end_time')}\n"
        f"event_location: {venue.get('name')}\n"
        f"event_address: {venue.get('address')}\n"
        f"event_registration_link: {registration.get('registration_url')}\n"
        f"platform: {social_post.get('platform')}\n"
        f"tone: {social_post.get('tone')}\n"
        f"hook_type: {social_post.get('hook_type')}\n"
        f"words_limit: {social_post.get('words_limit')}\n"
        f"include_emoji: {social_post.get('include_emoji')}\n"
        f"emoji_level: {social_post.get('emoji_level')}\n"
        f"power_words: {social_post.get('power_words')}\n"
        f"hsashtag_seeds: {social_post.get('hsashtag_seeds')}\n"
        f"language: {social_post.get('language')}\n"
        

    )


    return system_prompt + "\n\n" + user_prompt
