# from rest_framework.views import APIView
# from rest_framework.response import Response
# from .prompts import build_event_prompt
# from .services import call_openai

# class GenerateEventView(APIView):
#     def post(self, request):
#         user_prompt = request.data.get("prompt")
#         full_prompt = build_event_prompt(user_prompt)
#         ai_response = call_openai(full_prompt)
#         return Response({"event": ai_response})
