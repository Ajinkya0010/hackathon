from rest_framework import serializers
from .models import Patient

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['patientId', 'name', 'age', 'emergencyContact', 'caretakerId', 'pincode']