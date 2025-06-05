from rest_framework import serializers

class EventPreferenceSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=255)
    date = serializers.CharField(max_length=100)
    budget = serializers.IntegerField()
    target_audience = serializers.CharField(max_length=255)
