from rest_framework import serializers

class EventPreferenceSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=255)
    date = serializers.CharField(max_length=100)
    budget = serializers.IntegerField()
    target_audience = serializers.CharField(max_length=255)
    goal = serializers.CharField(max_length=255)
    atmosphere = serializers.CharField(max_length=255)

class InvitationRequestSerializer(serializers.Serializer):
    receiver_name = serializers.CharField()
    recipient_email = serializers.EmailField()
    words_limit = serializers.IntegerField()
    tone = serializers.CharField()
    language = serializers.CharField()