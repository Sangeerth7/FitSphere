from rest_framework import generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .services.diet_recommender import recommend_diet

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
    DietMeal
)
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    MemberSerializer,
    TrainerSerializer,
    MembershipPlanSerializer,
    MembershipEnrollmentSerializer,
    PaymentSerializer,
    ExerciseSerializer,
    WorkoutPlanSerializer,
    AttendanceSerializer
)
from .permissions import (
    IsAdmin,
    IsTrainer,
    IsMember,
)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "role": user.role,
            "username": user.username,
        })
    

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

class TrainerListCreateView(generics.ListCreateAPIView):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer


class TrainerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer

class MembershipPlanViewSet(viewsets.ModelViewSet):
    queryset = MembershipPlan.objects.all()
    serializer_class = MembershipPlanSerializer
    permission_classes = [IsAdmin]

class MembershipEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = MembershipEnrollment.objects.all()
    serializer_class = MembershipEnrollmentSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer

class WorkoutPlanViewSet(viewsets.ModelViewSet):
    queryset = WorkoutPlan.objects.all()
    serializer_class = WorkoutPlanSerializer

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        "user__username",
        "phone",
        "goal",
    ]

    ordering_fields = [
        "age",
        "weight",
        "join_date",
    ]

    filterset_fields = [
        "gender",
        "goal",
    ]

class GenerateDietPlanView(APIView):
    def post(self, request, member_id):
        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            return Response(
                {"error": "Member not found"},
                status=404
            )

        diet_plan = recommend_diet(member)

        return Response({
            "message": "Diet plan generated successfully",
            "diet_plan_id": diet_plan.id,
            "member": member.user.username,
            "plan_name": diet_plan.name,
            "goal": diet_plan.goal,
        })