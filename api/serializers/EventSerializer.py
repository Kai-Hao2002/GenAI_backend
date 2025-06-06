from rest_framework import serializers
from api.models import Event,EventVersion,EditLog,EventEditor
from django.contrib.auth import get_user_model

User = get_user_model()

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'


class EventVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventVersion
        fields = '__all__'

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class EditLogSerializer(serializers.ModelSerializer):
    edited_by = UserMiniSerializer()

    class Meta:
        model = EditLog
        fields = ['id', 'event', 'edited_by', 'edited_at', 'field_changed', 'old_value', 'new_value']


class EventEditorSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = EventEditor
        fields = ['user', 'username', 'role', 'added_at']
        read_only_fields = ['added_at']