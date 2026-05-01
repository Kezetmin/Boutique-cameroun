from django.contrib.auth.models import User
from rest_framework import serializers
from .models import ShopMember


class ShopMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = ShopMember
        fields = [
            'id',
            'user_id',
            'username',
            'email',
            'role',
            'role_display',
            'is_active',
            'created_at',
        ]


class CreateShopMemberSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    role = serializers.ChoiceField(
        choices=[
            ShopMember.MANAGER,
            ShopMember.SELLER,
        ]
    )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur existe déjà.")
        return value