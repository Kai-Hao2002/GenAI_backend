from api.views.google_form_views import load_credentials, create_google_form
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import Event,EventEditor,Registration
from django.contrib.auth import get_user_model
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from api.serializers.RegistrationSerializer import RegistrationSerializer

User = get_user_model()


# Permission Tools
def has_role(user, event_id, roles):
    return EventEditor.objects.filter(event_id=event_id, user=user, role__in=roles).exists()

class GoogleFormCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        if not has_role(request.user, event_id, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            registration = Registration.objects.get(event=event)
        except Registration.DoesNotExist:
            return Response({"error": "Prompt data not found. Please generate it first."}, status=status.HTTP_404_NOT_FOUND)

        form_title = registration.form_title or f"Registration for {event.name}"
        form_fields = registration.form_fields or []
        form_description = registration.event_intro or event.description

        if not form_fields:
            return Response({"error": "form_fields is empty in prompt data"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            creds = load_credentials()
            if not creds:
                return Response({"error": "Google OAuth credentials missing"}, status=status.HTTP_401_UNAUTHORIZED)

            registration_url = create_google_form(creds, form_title, form_fields, form_description)

            registration.registration_url = registration_url
            registration.save()

            return Response({
                "registration_url": registration_url
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class RegistrationListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        if not has_role(request.user, event_id, ['owner', 'editor', 'viewer']):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        registrations = Registration.objects.filter(event_id=event_id)
        serializer = RegistrationSerializer(registrations, many=True)
        return Response(serializer.data)

class RegistrationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            reg = Registration.objects.get(pk=pk)
            if not has_role(user, reg.event_id, ['owner', 'editor', 'viewer']):
                return None
            return reg
        except Registration.DoesNotExist:
            return None

    def put(self, request, pk):
        reg = self.get_object(pk, request.user)
        if not reg:
            return Response({"error": "Not found or access denied"}, status=status.HTTP_404_NOT_FOUND)
        if not has_role(request.user, reg.event_id, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = RegistrationSerializer(reg, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        reg = self.get_object(pk, request.user)
        if not reg:
            return Response({"error": "Not found or access denied"}, status=status.HTTP_404_NOT_FOUND)
        if not has_role(request.user, reg.event_id, ['owner']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        reg.delete()
        return Response({"message": "Deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
