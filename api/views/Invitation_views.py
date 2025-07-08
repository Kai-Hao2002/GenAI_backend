from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from api.models import EmailLog, EventEditor
from api.serializers.EmailLogSerializer import EmailLogSerializer

# Permission Tools
def has_role(user, event, roles):
    return EventEditor.objects.filter(event=event, user=user, role__in=roles).exists()

class EmailLogListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        if not has_role(request.user, event_id, ['owner', 'editor', 'viewer']):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        logs = EmailLog.objects.filter(event_id=event_id)
        serializer = EmailLogSerializer(logs, many=True)
        return Response(serializer.data)

    def post(self, request, event_id):
        if not has_role(request.user, event_id, ['owner', 'editor']):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data['event'] = event_id
        serializer = EmailLogSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailLogDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            log = EmailLog.objects.get(pk=pk)
            if not has_role(user, log.event_id, ['owner', 'editor', 'viewer']):
                return None
            return log
        except EmailLog.DoesNotExist:
            return None

    def get(self, request, pk):
        log = self.get_object(pk, request.user)
        if not log:
            return Response({"error": "Not found or access denied"}, status=status.HTTP_404_NOT_FOUND)
        serializer = EmailLogSerializer(log)
        return Response(serializer.data)

    def put(self, request, pk):
        log = self.get_object(pk, request.user)
        if not log:
            return Response({"error": "Not found or access denied"}, status=status.HTTP_404_NOT_FOUND)

        if not has_role(request.user, log.event.id, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = EmailLogSerializer(log, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        log = self.get_object(pk, request.user)
        if not log:
            return Response({"error": "Not found or access denied"}, status=status.HTTP_404_NOT_FOUND)

        if not has_role(request.user, log.event.id, ['owner']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        log.delete()
        return Response({"message": "Deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)

#auto mail
class EmailLogAutoSendAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        if not has_role(request.user, event_id, ['owner', 'editor']):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        email_logs = EmailLog.objects.filter(event_id=event_id).exclude(status='sent')

        if not email_logs.exists():
            return Response({"message": "No unsent emails found."}, status=status.HTTP_200_OK)

        sent_count = 0
        failed_count = 0

        for email in email_logs:
            try:
                subject = email.subject
                message = f"{email.body}"
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [email.recipient_email]

                send_mail(subject, message, from_email, recipient_list, fail_silently=False)

                email.status = 'sent'
                email.sent_at = timezone.now()
                email.save()
                sent_count += 1
            except Exception as e:
                email.status = 'failed'
                email.save()
                failed_count += 1
                print(f"❌ Email sending failed for {email.recipient_email}: {e}")

        return Response({
            "message": "Auto email send completed.",
            "sent_count": sent_count,
            "failed_count": failed_count,
        }, status=status.HTTP_200_OK)

class SingleInvitationSendAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            email = EmailLog.objects.get(pk=pk)

            if not has_role(request.user, email.event_id, ['owner', 'editor']):
                return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

            if email.status == 'sent':
                return Response({"message": "Email already sent."}, status=status.HTTP_200_OK)

            send_mail(
                subject=email.subject,
                message=email.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email.recipient_email],
                fail_silently=False,
            )

            email.status = 'sent'
            email.sent_at = timezone.now()
            email.save()

            return Response({"message": "Email sent successfully."}, status=status.HTTP_200_OK)

        except EmailLog.DoesNotExist:
            return Response({"error": "EmailLog not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            email.status = 'failed'
            email.save()
            return Response({"error": f"Failed to send email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
