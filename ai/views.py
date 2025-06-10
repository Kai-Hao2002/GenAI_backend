from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, time
from ai.serializers import EventPreferenceSerializer
from api.models import Event,EventEditor,TaskAssignment
from django.contrib.auth import get_user_model
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from ai.services.event_services import generate_event_from_gemini,generate_task_assignment_from_gemini

User = get_user_model()


# Permission Tools
def has_role(user, event_id, roles):
    return EventEditor.objects.filter(event_id=event_id, user=user, role__in=roles).exists()

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
                description=ai_response["description"],
                slogan=ai_response["slogan"][0],
                target_audience=data.get("target_audience"),
                expected_attendees=ai_response["expected_attendees"],
                start_time=start_time,
                end_time=end_time,
                type=data.get("type"),
                budget=data.get("budget"),
                status="draft",
                created_by=request.user
            )
            EventEditor.objects.create(
                event=event,
                user=request.user,
                role='owner'
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

class TaskAssignmentGenerationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        # 權限檢查
        if not has_role(request.user, event_id, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        event_data = request.data.get("event")
        if not event_data:
            return Response({"error": "Missing event data"}, status=status.HTTP_400_BAD_REQUEST)

        if event_data.get("event_id") and event_data.get("event_id") != event_id:
            return Response({"error": "event_id in body does not match URL"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        # 確保 event_id 被設好
        event_data["event_id"] = event_id

        try:
            # 丟給 Gemini 產生任務
            result = generate_task_assignment_from_gemini(request.data)

            # 儲存到資料庫
            task_data_list = result.get("task_summary_by_role", [])
            TaskAssignment.objects.filter(event=event).delete()  # 清除原本的（可選）
            for task in task_data_list:
                TaskAssignment.objects.create(
                    event=event,
                    role=task.get("role"),
                    description=task.get("description", ""),
                    count=task.get("count", 0),
                    start_time=task.get("start_time"),
                    end_time=task.get("end_time"),
                )

            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)