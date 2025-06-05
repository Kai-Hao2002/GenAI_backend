from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from api.models import Event, EventVersion, EditLog
from api.serializers.EventSerializer import EventSerializer, EventVersionSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class EventListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = Event.objects.filter(created_by=request.user)
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)


class EventDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk, created_by=request.user)
        include_versions = request.query_params.get("include_versions") == "true"
        data = EventSerializer(event).data

        if include_versions:
            versions = EventVersion.objects.filter(event=event).order_by("-version_number")
            data["versions"] = EventVersionSerializer(versions, many=True).data

        return Response(data, status=status.HTTP_200_OK)


class EventUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        return self._update_event(request, pk, partial=True)

    def put(self, request, pk):
        return self._update_event(request, pk, partial=False)

    def _update_event(self, request, pk, partial):
        event = get_object_or_404(Event, pk=pk)
        
        # 確保是擁有者才能編輯
        if event.created_by != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        serializer = EventSerializer(event, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 檢查變更欄位，建立 edit_logs
        for field, new_value in serializer.validated_data.items():
            old_value = getattr(event, field, None)
            if old_value != new_value:
                EditLog.objects.create(
                    event=event,
                    edited_by=request.user,
                    edited_at=timezone.now(),
                    field_changed=field,
                    old_value=str(old_value),
                    new_value=str(new_value)
                )

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class EventDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        event = get_object_or_404(Event, pk=pk, created_by=request.user)

        # 先刪除所有 event_versions 和 edit_logs
        event.versions.all().delete()
        event.edit_logs.all().delete()

        # 再刪除主事件
        event.delete()

        return Response({"message": "Event deleted"}, status=204)


class SaveEventVersionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)

        if event.created_by != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        # 建立新的版本編號
        latest_version = event.versions.order_by("-version_number").first()
        next_version_number = 1 if not latest_version else latest_version.version_number + 1

        # 快照整個 Event 狀態
        snapshot = EventSerializer(event).data

        version = EventVersion.objects.create(
            event=event,
            version_number=next_version_number,
            changes_summary=request.data.get("changes_summary", ""),
            created_at=timezone.now(),
            created_by=request.user,
            event_snapshot=snapshot
        )

        # 更新 Event.latest_version_id
        event.latest_version_id = version.id
        event.save(update_fields=["latest_version_id"])

        return Response({"message": "Event version saved", "version_id": version.id}, status=status.HTTP_201_CREATED)
