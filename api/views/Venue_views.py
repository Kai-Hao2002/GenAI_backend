from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from api.models import VenueSuggestion, Event, EventEditor
from api.serializers.VenueSerializer import VenueSuggestionSerializer

# Permission Tools
def has_role(user, event, roles):
    return EventEditor.objects.filter(event=event, user=user, role__in=roles).exists()

class VenueSuggestionListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        if not has_role(request.user, event_id, ['owner', 'editor', 'viewer']):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        suggestions = VenueSuggestion.objects.filter(event_id=event_id)
        serializer = VenueSuggestionSerializer(suggestions, many=True)
        return Response(serializer.data)


class VenueSuggestionDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            suggestion = VenueSuggestion.objects.get(pk=pk)
            if not has_role(user, suggestion.event_id, ['owner', 'editor', 'viewer']):
                return None
            return suggestion
        except VenueSuggestion.DoesNotExist:
            return None

    def put(self, request, pk):
        suggestion = self.get_object(pk, request.user)
        if not suggestion:
            return Response({"error": "Not found or access denied"}, status=status.HTTP_404_NOT_FOUND)

        if not has_role(request.user, suggestion.event.id, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = VenueSuggestionSerializer(suggestion, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        suggestion = self.get_object(pk, request.user)
        if not suggestion:
            return Response({"error": "Not found or access denied"}, status=status.HTTP_404_NOT_FOUND)

        if not has_role(request.user, suggestion.event.id, ['owner']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        suggestion.delete()
        return Response({"message": "delete successfully !"}, status=status.HTTP_204_NO_CONTENT)
