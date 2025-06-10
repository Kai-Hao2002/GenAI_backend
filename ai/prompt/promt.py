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
    assignment = event_data.get("task_assignments", {})

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
        f"group_by_role: {assignment.get('group_by_role')}\n"
        f"include_count: {assignment.get('include_count')}\n"
        f"timeline_type: {assignment.get('timeline_type')}\n"
        f"output_format: {assignment.get('output_format')}\n"
    )

    return system_prompt + "\n\n" + user_prompt
