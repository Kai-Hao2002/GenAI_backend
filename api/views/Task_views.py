from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from api.models import TaskAssignment, Event , EventEditor
from api.serializers.TaskSerializer import TaskAssignmentSerializer


# Permission Tools
def has_role(user, event, roles):
    return EventEditor.objects.filter(event=event, user=user, role__in=roles).exists()

class TaskAssignmentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        if not has_role(request.user, event_id, ['owner', 'editor', 'viewer']):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        assignments = TaskAssignment.objects.filter(event_id=event_id)
        serializer = TaskAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

    def post(self, request, event_id):
        if not has_role(request.user, event_id, ['owner', 'editor']):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data['event'] = event_id
        serializer = TaskAssignmentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskAssignmentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            assignment = TaskAssignment.objects.get(pk=pk)
            if not has_role(user, assignment.event_id, ['owner', 'editor', 'viewer']):
                return None
            return assignment
        except TaskAssignment.DoesNotExist:
            return None

    def get(self, request, pk):
        assignment = self.get_object(pk, request.user)
        if not assignment:
            return Response({"error": "Not found or access denied"}, status=status.HTTP_404_NOT_FOUND)
        serializer = TaskAssignmentSerializer(assignment)
        return Response(serializer.data)

    def put(self, request, pk):
        assignment = self.get_object(pk, request.user)
        if not assignment:
            return Response({"error": "Not found or access denied"}, status=status.HTTP_404_NOT_FOUND)

        # only owner or editor can edit
        if not has_role(request.user, assignment.event.id, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = TaskAssignmentSerializer(assignment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
        assignment = self.get_object(pk, request.user)
        if not assignment:
            return Response({"error": "Not found or access denied"}, status=status.HTTP_404_NOT_FOUND)

        # only owner can delete
        if not has_role(request.user, assignment.event.id, ['owner']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        assignment.delete()
        return Response({"message": "delete successfully !"}, status=status.HTTP_204_NO_CONTENT)

