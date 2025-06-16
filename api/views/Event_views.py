from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from api.models import Event, EventVersion, EditLog, EventEditor
from api.serializers.EventSerializer import EventSerializer, EventVersionSerializer, EditLogSerializer, EventEditorSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

# Permission Tools
def has_role(user, event, roles):
    return EventEditor.objects.filter(event=event, user=user, role__in=roles).exists()


class EventListAPIView(APIView): # Get all activities in which the user participates
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = Event.objects.filter(editors__user=request.user).distinct()
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)


class EventDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        if not has_role(request.user, event, ['owner', 'editor', 'viewer']):
            return Response({"error": "Access denied"}, status=403)

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

        if not has_role(request.user, event, ['owner', 'editor']):
            return Response({"error": "Permission denied."}, status=403)

        serializer = EventSerializer(event, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        for field, new_value in serializer.validated_data.items():
            old_value = getattr(event, field, None)
            if old_value != new_value:
                EditLog.objects.create(
                    event=event,
                    edited_by=request.user,
                    field_changed=field,
                    old_value=str(old_value),
                    new_value=str(new_value)
                )

        serializer.save()
        return Response(serializer.data, status=200)


class EventDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        event = get_object_or_404(Event, pk=pk)

        if not has_role(request.user, event, ['owner']):
            return Response({"error": "Only owners can delete the event."}, status=403)

        event.versions.all().delete()
        event.edit_logs.all().delete()
        event.task_assignments.all().delete()
        event.visual_assets.all().delete()
        event.social_posts.all().delete()
        event.venue_suggestions.all().delete()
        event.email.all().delete()
        event.registrations.all().delete()
        event.editors.all().delete()
        event.delete()

        return Response({"message": "Event deleted"}, status=204)


class SaveEventVersionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)

        if not has_role(request.user, event, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=403)

        latest_version = event.versions.order_by("-version_number").first()
        next_version_number = 1 if not latest_version else latest_version.version_number + 1

        snapshot = EventSerializer(event).data

        version = EventVersion.objects.create(
            event=event,
            version_number=next_version_number,
            created_by=request.user,
            event_snapshot=snapshot
        )

        event.latest_version = version
        event.save(update_fields=["latest_version"])

        return Response({"message": "Event version saved", "version_id": version.id}, status=201)


class EventRevertAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id, version_id):
        event = get_object_or_404(Event, pk=event_id)
        version = get_object_or_404(EventVersion, pk=version_id, event=event)

        if not has_role(request.user, event, ['owner']):
            return Response({"error": "Only owner can revert version"}, status=403)

        snapshot = version.event_snapshot

        for field in [
            "name", "description", "slogan", "target_audience", "expected_attendees",
            "start_time", "end_time", "type", "budget", "status"
        ]:
            setattr(event, field, snapshot.get(field))

        event.latest_version = version
        event.save()
        serializer = EventSerializer(event)

        return Response({"message": "Reverted successfully","event": serializer.data}, status=200)



class EventVersionDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id, version_id):
        event = get_object_or_404(Event, pk=event_id)

        if not has_role(request.user, event, ['owner', 'editor', 'viewer']):
            return Response({"error": "Access denied"}, status=403)

        version = get_object_or_404(EventVersion, pk=version_id, event=event)
        serializer = EventVersionSerializer(version)
        return Response(serializer.data, status=200)


class EditLogListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)

        if not has_role(request.user, event, ['owner', 'editor', 'viewer']):
            return Response({"error": "Not authorized to view edit logs."}, status=403)

        logs = EditLog.objects.filter(event=event).order_by("-edited_at")
        serializer = EditLogSerializer(logs, many=True)
        return Response(serializer.data, status=200)

class EventEditorListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)

        # Only the owner can query the editor list
        if not has_role(request.user, event, ['owner']):
            return Response({'error': 'Permission denied'}, status=403)

        editors = EventEditor.objects.filter(event=event).select_related('user')
        serializer = EventEditorSerializer(editors, many=True)
        return Response(serializer.data, status=200)

    def post(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)

        # Only owner can add
        if not has_role(request.user, event, ['owner']):
            return Response({'error': 'Permission denied'}, status=403)

        serializer = EventEditorSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            if EventEditor.objects.filter(event=event, user=user).exists():
                return Response({'error': 'User is already an editor'}, status=400)

            EventEditor.objects.create(
                event=event,
                user=user,
                role=serializer.validated_data['role']
            )
            return Response({'message': 'Editor added'}, status=201)

        return Response(serializer.errors, status=400)


class EventEditorDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, event_id, user_id):
        event = get_object_or_404(Event, pk=event_id)
        if not has_role(request.user, event, ['owner']):
            return Response({'error': 'Permission denied'}, status=403)

        editor = get_object_or_404(EventEditor, event=event, user__id=user_id)
        serializer = EventEditorSerializer(editor, data=request.data, partial=True)
        if serializer.is_valid():
            editor.role = serializer.validated_data['role']
            editor.save()
            return Response({'message': 'Editor updated'}, status=200)
        return Response(serializer.errors, status=400)

    def delete(self, request, event_id, user_id):
        event = get_object_or_404(Event, pk=event_id)
        if not has_role(request.user, event, ['owner']):
            return Response({'error': 'Permission denied'}, status=403)

        editor = get_object_or_404(EventEditor, event=event, user__id=user_id)
        editor.delete()
        return Response({'message': 'Editor removed'}, status=204)
