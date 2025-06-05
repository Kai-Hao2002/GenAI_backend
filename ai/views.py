from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, time
from ai.serializers import EventPreferenceSerializer
from api.models import Event  
from django.contrib.auth import get_user_model
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from ai.services.event_services import generate_event_from_gemini

User = get_user_model()

class GenerateEventAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EventPreferenceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            ai_response = generate_event_from_gemini(data)

            # 解析日期字串並轉成當天 00:00 跟 23:59:59
            date_str = data.get("date")
            event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_time = datetime.combine(event_date, time(00, 00, 00))  # 00:00:00
            end_time = datetime.combine(event_date, time(23, 59, 59))  # 23:59:59

            event = Event.objects.create(
                name=ai_response["name"][0],  # 取第一個建議的名稱
                description=ai_response["description"][0],
                slogan=ai_response["slogan"],
                target_audience=data.get("target_audience"),
                expected_attendees=ai_response["expected_attendees"],
                start_time=start_time,
                end_time=end_time,
                type=data.get("type"),
                budget=data.get("budget"),
                status="draft",
                created_by=request.user
            )

             # 把 event.id 加入回傳資料
            response_data = ai_response.copy()
            response_data["event_id"] = event.id

            # 回傳全部 AI 建議（前端選擇後再呼叫另存API）
            return Response(response_data , status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": f"Failed to generate or save event: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
