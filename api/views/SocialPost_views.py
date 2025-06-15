from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from api.models import SocialPost, EventEditor
from api.serializers.SocialPostSerializer import SocialPostSerializer

# Permission Tools
def has_role(user, event, roles):
    return EventEditor.objects.filter(event=event, user=user, role__in=roles).exists()

class SocialPostListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        if not has_role(request.user, event_id, ['owner', 'editor', 'viewer']):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        posts = SocialPost.objects.filter(event_id=event_id)
        serializer = SocialPostSerializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request, event_id):
        if not has_role(request.user, event_id, ['owner', 'editor']):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data['event'] = event_id
        serializer = SocialPostSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SocialPostDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            post = SocialPost.objects.get(pk=pk)
            if not has_role(user, post.event_id, ['owner', 'editor', 'viewer']):
                return None
            return post
        except SocialPost.DoesNotExist:
            return None

    def get(self, request, pk):
        post = self.get_object(pk, request.user)
        if not post:
            return Response({"error": "Not found or access denied"}, status=status.HTTP_404_NOT_FOUND)
        serializer = SocialPostSerializer(post)
        return Response(serializer.data)

    def put(self, request, pk):
        post = self.get_object(pk, request.user)
        if not post:
            return Response({"error": "Not found or access denied"}, status=status.HTTP_404_NOT_FOUND)

        if not has_role(request.user, post.event.id, ['owner', 'editor']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = SocialPostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        post = self.get_object(pk, request.user)
        if not post:
            return Response({"error": "Not found or access denied"}, status=status.HTTP_404_NOT_FOUND)

        if not has_role(request.user, post.event.id, ['owner']):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        post.delete()
        return Response({"message": "Delete successfully!"}, status=status.HTTP_204_NO_CONTENT)
