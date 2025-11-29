from rest_framework import serializers

class TaskSerializer(serializers.Serializer):
    title = serializers.CharField()
    due_date = serializers.DateField(required=False)
    estimated_hours = serializers.FloatField(required=False)
    importance = serializers.IntegerField(required=False, min_value=1, max_value=10)
    dependencies = serializers.ListField(child=serializers.CharField(), required=False)
