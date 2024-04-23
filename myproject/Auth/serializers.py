from rest_framework import serializers
from .models import BSUser

# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CustomUser
#         fields = ['id', 'username', 'phone_number', 'password', 'is_admin']
#         extra_kwargs = {'password': {'write_only': True}}

#     def create(self, validated_data):
#         user = CustomUser.objects.create_user(**validated_data)
#         return user


class BSUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BSUser
        fields = ('_id', 'username', 'first_name', 'last_name', 'phone_number', 'password',
                  'is_superuser', 'date_joined', 'updated_at', 'last_login_at', 'is_active')

        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': False},
            'last_name': {'required': False}
        }

    def create(self, validated_data):
        user = BSUser.objects.create_user(**validated_data)
        return user
    
    