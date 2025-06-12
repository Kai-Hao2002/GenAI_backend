from rest_framework import serializers
from api.models import VenueSuggestion

class VenueSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VenueSuggestion
        fields = '__all__'
