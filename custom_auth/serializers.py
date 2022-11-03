import random

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.validators import UniqueValidator

from .models import UserAccount


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.CharField()

    class Meta:
        model = UserAccount
        fields = ("email", "password")


def check(data):
    return authenticate(email=data["email"], password=data["password"])


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=500)


def checkYears(value):
    valid_set = ["ONE", "TWO", "THREE", "FOUR"]
    if value in valid_set:
        return True
    raise ValidationError("Please enter a valid year.")


def checkCode(value):
    user = UserAccount.objects.filter(user_referral_code=value)
    if len(user) == 0:
        raise ValidationError("Please enter a valid referral code.")
    return True


class RegisterSerializer(serializers.Serializer):


    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=UserAccount.objects.all(),
                message=("Email is already registered with us. Please login!"),
            )
        ],
    )
    password = serializers.CharField(write_only=True, required=True)
    name = serializers.CharField(required=True)
    year = serializers.CharField(required=True, validators=[checkYears])
    college_name = serializers.CharField(required=True)
    referral_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, validators=[checkCode]
    )

    class Meta:
        model = UserAccount
        fields = "__all__"

    def create(self, validated_data):
        user = UserAccount.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
        )
        user.name = validated_data["name"]
        user.year = validated_data["year"]
        user.college_name = validated_data["college_name"]
        user.referral_code = validated_data["referral_code"]
        name = (user.name).replace(" ", "").lower()
        user.user_referral_code = name[: min(len(user.name), 5)]
        user.user_referral_code += str(random.randint(10001, 99999))
        user.save()
        return user


class UserSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    year = serializers.CharField(required=True)
    college_name = serializers.CharField(required=True)

    class Meta:
        model = UserAccount
        fields = "__all__"

    def create(self, validated_data):
        user = UserAccount.objects.get(
            email=validated_data["email"],
        )
        user.name = validated_data["name"]
        user.year = validated_data["year"]
        user.college_name = validated_data["college_name"]
        user.save()
        return user
