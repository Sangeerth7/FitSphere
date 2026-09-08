from django.contrib.auth import authenticate
from rest_framework import serializers
from dateutil.relativedelta import relativedelta

from .models import (
    User,
    Member,
    Trainer,
    MembershipPlan,
    MembershipEnrollment,
    Payment,
    Exercise,
    WorkoutPlan,
    Attendance,
    DietPlan,
    DietMeal,
)


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


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            username=data["username"],
            password=data["password"]
        )

        if not user:
            raise serializers.ValidationError(
                "Invalid username or password"
            )

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


class MembershipEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipEnrollment
        fields = "__all__"
        read_only_fields = ["end_date"]

    def create(self, validated_data):
        plan = validated_data["plan"]
        start_date = validated_data["start_date"]

        validated_data["end_date"] = (
            start_date + relativedelta(
                months=plan.duration_months
            )
        )

        return super().create(validated_data)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["amount"]

    def create(self, validated_data):
        enrollment = validated_data["enrollment"]

        validated_data["amount"] = enrollment.plan.price

        return super().create(validated_data)


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = "__all__"


class WorkoutPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutPlan
        fields = "__all__"


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = "__all__"


class DietMealSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietMeal
        fields = ["id", "meal_type", "food", "quantity", "notes"]


class DietPlanSerializer(serializers.ModelSerializer):
    meals = DietMealSerializer(many=True, read_only=True)

    class Meta:
        model = DietPlan
        fields = [
            "id",
            "member",
            "name",
            "goal",
            "description",
            "calories_target",
            "created_at",
            "updated_at",
            "meals",
        ]
        read_only_fields = ["created_at", "updated_at", "meals"]