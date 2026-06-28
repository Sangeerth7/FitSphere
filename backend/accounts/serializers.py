from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Member, User
from .models import Trainer
from .models import MembershipPlan
from .models import MembershipEnrollment
from .models import Payment

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "password", "role"]
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            role=validated_data.get("role", "member")
        )
        return user
    
    from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["username"] = user.username
        token["role"] = user.role

        return token
    
    from django.contrib.auth import authenticate
from rest_framework import serializers

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            username=data["username"],
            password=data["password"]
        )

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        data["user"] = user
        return data
    
class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = "__all__"


class TrainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainer
        fields = "__all__"


class MembershipPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipPlan
        fields = "__all__"

from dateutil.relativedelta import relativedelta

class MembershipEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipEnrollment
        fields = "__all__"
        read_only_fields = ["end_date"]

    def create(self, validated_data):
        plan = validated_data["plan"]
        start_date = validated_data["start_date"]

        validated_data["end_date"] = (
            start_date + relativedelta(months=plan.duration_months)
        )

        return super().create(validated_data)
    class Meta:
        model = MembershipEnrollment
        fields = "__all__"

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["amount"]

    def create(self, validated_data):
        enrollment = validated_data["enrollment"]

        validated_data["amount"] = enrollment.plan.price

        return super().create(validated_data)