from rest_framework import serializers
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer pour les clients d'une boutique.
    """

    class Meta:
        model = Customer
        fields = [
            'id',
            'name',
            'phone',
            'address',
            'note',
            'created_at',
        ]

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Le nom du client est obligatoire.")
        return value.strip()