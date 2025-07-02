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
    email = serializers.EmailField(write_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = EventEditor
        fields = ['email', 'username', 'role', 'added_at']
        read_only_fields = ['username', 'added_at']

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        self.context['user'] = user
        return value

    def create(self, validated_data):
        user = self.context['user']
        event = self.context.get('event')
        role = validated_data['role']

        if EventEditor.objects.filter(event=event, user=user).exists():
            raise serializers.ValidationError("This user is already an editor for the event.")

        return EventEditor.objects.create(user=user, event=event, role=role)