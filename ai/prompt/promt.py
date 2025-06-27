#Functions contains system prompt and user prompt
def get_event_generation_prompt(event_data: dict) -> str:
    system_prompt = (
                    """
                    You are a skilled activities planner.

                    Given an input JSON describing the event goal, type, date, budget, audience, and atmosphere, generate the following items strictly as a JSON object:

                    - "name": a list of exactly 5 creative and imaginative event names, each clearly connected to the event's goal, audience, type, and atmosphere.
                    - "description": a detailed event description as a single string that covers the event's purpose, vibe, and benefits for attendees. Do NOT include or mention any event names in this description.
                    - "expected_attendees": an integer representing the expected number of attendees.
                    - "suggested_time": a string specifying the suggested event start and end time in "HH:MM - HH:MM" format.
                    - "suggested_event_duration": a string describing the duration of the event, e.g. "3 hours".
                    - "slogan": a list of exactly 5 slogans, each based on the event goal and atmosphere.

                    Output ONLY the JSON object exactly in the described structure. Do NOT include any explanations, additional text, or formatting outside the JSON.

                    """
                    )

    user_prompt = (
        f"Event goal: {event_data.get('goal')}\n"
        f"Type: {event_data.get('type')}\n"
        f"Date: {event_data.get('date')}\n"
        f"Budget: {event_data.get('budget')}\n"
        f"Audience: {event_data.get('target_audience')}\n"
        f"Atmosphere: {event_data.get('atmosphere')}\n"
    )

    return system_prompt + "\n" + user_prompt

def get_task_assignment_generation_prompt(event_data: dict) -> str:
    event = event_data.get("event", {})

    system_prompt = (
        """
            You are a professional event task planning assistant.

            Given event data including event_id, event_name, type, start_time, end_time, expected_attendees, and timeline_type, generate a JSON object recommending event roles and staffing counts.

            - Assign roles based on event type, using these predefined sets:
            * Workshop / Training: ["facilitator", "assistant", "tech_support", "material_handler", "time_keeper"]
            * Social / Networking: ["host", "greeter", "logistics", "photographer", "music_dj"]
            * Performance / Showcase: ["stage_manager", "lighting", "sound_engineer", "usher", "safety_officer"]
            * Speech / Seminar: ["emcee", "speaker_handler", "registration_staff", "audiovisual_support", "time_keeper"]
            * Recreational / Entertainment: ["activity_leader", "crowd_control", "logistics", "vendor_liaison", "security"]
            * Market / Exhibition: ["booth_coordinator", "vendor_helper", "floor_manager", "map_distributor", "ticketing"]
            * Competition / Challenge: ["referee", "score_keeper", "participant_handler", "tech_support", "logistics"]

            - Estimate staff counts based on expected_attendees:
            * General roles: approximately 1 staff per 50 attendees, rounded sensibly.
            * Technical and host roles: fixed small counts (1-3 staff).
            
            - For each role, assign "start_time" and "end_time" as the event's overall start_time and end_time, indicating the time period each staff member is expected to work.

            - If the timeline_type is "absolute", use ISO 8601 format for all time fields.

            - If start_time is missing, omit all time fields in each role and add a top-level key "note" with value "Start time missing".

            OUTPUT FORMAT:

            Return exactly one JSON object with the following structure:

            {
            "task_summary_by_role": [
                {
                "role": "<role_code>",
                "description": "<short English task description>",
                "count": <integer>,
                "start_time": "<ISO 8601 timestamp>",  // omit if start_time missing
                "end_time": "<ISO 8601 timestamp>"     // omit if start_time missing
                },
                ...
            ],
            "note": "Start time missing"  // include only if start_time is missing
            }

            Do NOT include any explanations, comments, or text outside this JSON object. Do NOT include JSON comments or invalid JSON syntax.

        """
        )

    user_prompt = (
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

    system_prompt =                 """
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

    system_prompt = """
                    You are a professional event registration form designer.

                    Your task is to generate a structured JSON object representing a registration form, based on the provided event information.

                    The output JSON object must contain:

                    1. "event_intro": A short, engaging summary (maximum 2 sentences) that appears at the top of the form to encourage registration.
                    2. "form_title": A concise, action-oriented title that includes the event name (e.g., "Register for the AI Hackathon!").
                    3. "form_fields": A list of fields that attendees must fill in. Each field is an object with the following keys:
                    - "registration_name": a lowercase English slug using only letters and underscores (e.g., "email", "team_name").
                    - "description": a short, user-facing label (can be in the event’s language).
                    - "type": the input type, such as "text", "email", "number", or "select".
                    - "required": a boolean indicating whether the field is mandatory.

                    Field generation rules:
                    - Always include the basic required fields: "first_name", "last_name", and "email".
                    - Infer other relevant fields based on the event_type and target audience.
                    * For team-based events, include "team_name".
                    * For student-focused events, include "school", "major", and "graduation_year".
                    * For outdoor or merchandise-based events, include "tshirt_size".
                    * For food or accessibility-related contexts, include "dietary_preferences" and "accessibility_needs" if applicable.

                    Output Rules:
                    - Return **only** a valid JSON object in the following format.
                    - Do NOT include any extra explanation, markdown, comments, or text.

                    OUTPUT FORMAT (pure JSON):

                    {
                    "registration-list": [
                        {
                        "event_intro": "string",
                        "form_title": "string",
                        "form_fields": [
                            {
                            "registration_name": "string",
                            "description": "string"
                            },
                            ...
                        ]
                        }
                    ]
                    }
                    """


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


    system_prompt = """
                    You are an expert email invitation writer.
                    Your task is to generate a personalized, emotionally compelling invitation email subject and body for each recipient.

                    Input includes:
                    - Event information: event_name, event_description, event_slogan, event_type, event_start_time, event_end_time, event_location, event_address, event_registration_link
                    - A list of recipients, each with their name
                    - Writing constraints: words_limit, tone, and language

                    Your Goal:
                    - For each recipient, write:
                    • An engaging subject line.
                    • A personalized email body with their name.
                    - The body must clearly explain what the event is, why it matters, when and where it happens.
                    - Use the event slogan creatively within the message if provided.
                    - Include the registration link in the email body in a natural way.
                    - Match the specified tone (e.g., Formal, Semi-formal, Friendly, Casual, Persuasive).
                    - Write in the given language.
                    - Keep the email body within the specified words_limit.
                    - The email must:
                    • Begin with a greeting using the recipient's name.
                    • End with a signature from the Event Organizer or event team.
                    - Do NOT include any markdown, HTML, bullet points, or explanations — plain text only.

                    OUTPUT FORMAT (always JSON):
                    {
                    "invitation_list": [
                        {
                        "invitation_letter_subject": "string",
                        "invitation_letter_body": "string"
                        },
                        ... (one per recipient)
                    ]
                    }
                    """




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
    


    system_prompt = """
                    You are a professional social media copywriting assistant.

                    Your task is to generate creative, engaging, and platform-tailored social media posts based on the provided event details and content strategy preferences.

                    You must strictly follow these rules:

                    FORMAT:
                    - Return a JSON object: { "post_list": [...] }
                    - Each item in "post_list" must be an object with:
                    - "content": A full social media caption. It must:
                        • Include essential event details (event name, date/time, location, and registration link).
                        • Start with a compelling hook based on the provided hook_type.
                        • Match the given tone and platform style.
                        • End with a clear call to action.
                    - "hashtag": A list of 3-6 custom, relevant hashtags that reflect the event's theme, location, and target audience.
                        • Avoid generic or unrelated trending tags.

                    STYLE RULES:
                    - Match tone and writing style to the platform (e.g., Instagram: informal, Facebook: conversational, LinkedIn: professional).
                    - If include_emoji is true, use emojis based on emoji_level:
                    • low: 1-2 emojis max, sparing use.
                    • medium: 3-5 emojis, balanced and expressive.
                    • high: 6-8 max, energetic but not chaotic.
                    - Incorporate provided power_words and hashtag_seeds creatively and naturally.
                    - Each post must be unique — avoid rephrased duplicates.
                    - Keep each post within the specified words_limit.
                    - Write in the specified language.
                    - Do NOT use markdown, HTML, or explanations. Return only the JSON object.

                    EXAMPLE OUTPUT:
                    {
                    "post_list": [
                        {
                        "content": "🚀 Ready to unleash your AI potential? Join the AI Hackathon on July 20th at National Taiwan University! 24 hours of coding, creativity, and innovation await. Sign up now 👉 https://example.com/hackathon",
                        "hashtag": ["#AIHackathon", "#CreativeChallenge", "#NTU", "#Hackathon2025"]
                        }
                    ]
                    }
                    """

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
        f"hashtag_seeds: {social_post.get('hashtag_seeds')}\n"
        f"language: {social_post.get('language')}\n"
        

    )


    return system_prompt + "\n\n" + user_prompt


def get_poster_copy_generation_prompt(event_data: dict) -> str:
    event = event_data.get("event", {})
    poster = event_data.get("poster", {})

    system_prompt = (
        "You are a professional marketing copywriter for posters. Your goal is to generate engaging and polished text.\n"
        "Output must be a valid JSON object like: {\"headline\": \"...\", \"subheadline\": \"...\"}\n"
        "Instructions:\n"
        "- Headline: short, bold, emotional, no more than 8 words\n"
        "- Subheadline: one sentence only, clear and under 100 characters\n"
        "- Language: MUST match the event language precisely (e.g., Traditional Chinese if requested)\n"
        "- Avoid generic or vague expressions like 'Join us today!'\n"
        "- Do NOT use emojis, hashtags, or filler words\n"
        "- Subheadline must add information beyond the headline"
    )


    user_prompt = (
        f"Event name: {event.get('event_name')}\n"
        f"Description: {event.get('event_description')}\n"
        f"Event type: {event.get('event_type')}\n"
        f"Slogan: {event.get('event_slogan')}\n"
        f"Audience: {event.get('target_audience')}\n"
        f"language: {poster.get('language')}\n"
    )

    return system_prompt + "\n\n" + user_prompt

def get_poster_image_prompt(event_data: dict) -> str:
    event = event_data.get("event", {})
    venue = event_data.get("venue", {})
    poster = event_data.get("poster", {})
    poster_text = event_data.get("poster_text", {})

    system_prompt = (
        "You are a visual AI agent specialized in creating poster images that combine "
        "both text and background visuals in a harmonious way.\n"
        "Generate a poster image as a PNG that includes the following text elements clearly and aesthetically:\n"
        "- Event headline\n"
        "- Event subheadline\n"
        "- Event start and end time\n"
        "- Event location\n"
        "Leave a blank space in the bottom-right corner reserved for a QR code.\n\n"
        "Use the following style guidelines to design the poster:\n"
        "- Mood: match the tone of the event\n"
        "- Color scheme: use the specified colors\n"
        "- Layout style: follow the given layout style\n"
        "- Font style: apply the given font style\n\n"
        "Base64-encode the resulting PNG image.\n"
        "Return ONLY a JSON object exactly in this format:\n"
        "{\"image_base64\": \"<base64_encoded_png_image>\"}"
    )


    user_prompt = (
        f"Headline (for reference): {poster_text.get('headline')}\n"
        f"Subheadline (for reference): {poster_text.get('subheadline')}\n"
        f"Target Audience: {event.get('event_target_audience')}\n"
        f"Mood: {poster.get('tone')}\n"
        f"Color scheme: {poster.get('color_scheme')}\n"
        f"Layout style: {poster.get('layout_style')}\n"
        f"Font style: {poster.get('font_style')}\n"
        f"Start time: {event.get('start_time')}\n"
        f"End time: {event.get('end_time')}\n"
        f"Location: {venue.get('name')}\n"
        f"Address: {venue.get('address')}\n"
        "Focus on a harmonious visual design that supports text overlay."
    )

    return system_prompt + "\n\n" + user_prompt
