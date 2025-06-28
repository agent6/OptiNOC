from rest_framework import serializers
from .models import MetricRecord


class MetricRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetricRecord
        fields = ['timestamp', 'value']
