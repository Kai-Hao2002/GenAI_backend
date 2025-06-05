def get_event_generation_prompt(event_data: dict) -> str:
    system_prompt = (
        "You are a skilled activities planner specializing in student events.\n"
        "Given an input JSON describing the event goal, type, date, budget, target audience, and atmosphere, "
        "brainstorm and generate exactly 5 creative event names as a list, and five detailed event description, "
        "suggested event duration, suggested time, expected attendees, and a catchy slogan.\n"
        "Event names must be imaginative and clearly connected to the event's goal, audience, type, and atmosphere.\n"
        "The description should cover the event's purpose, vibe, and benefits for attendees.\n"
        "Output the entire response strictly in JSON format ONLY, with these keys: "
        "'name' (list of 5 strings), "
        "'description' (list of 5 strings), "
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
