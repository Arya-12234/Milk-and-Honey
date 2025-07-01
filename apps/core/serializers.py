from django.contrib.auth.hashers import make_password
from rest_framework.serializers import ModelSerializer
from .models import User, Growth

class GrowthSerializer(ModelSerializer):
    class Meta:
        model = Growth
        fields = '__all__'

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"

    def create(self, validated_data):
        request = self.context.get("request")
        password = validated_data.pop("password")
        validated_data["password"] = make_password(password)

        return super().create(validated_data)