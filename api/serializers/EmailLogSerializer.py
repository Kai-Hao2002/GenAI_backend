from rest_framework import serializers
from api.models import EmailLog

class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = '__all__'
