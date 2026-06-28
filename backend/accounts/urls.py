from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    RegisterView,
    LoginView,
    MemberViewSet,
    TrainerListCreateView,
    TrainerDetailView,
    MembershipPlanViewSet,
    MembershipEnrollmentViewSet,
    PaymentViewSet
)

router = DefaultRouter()
router.register(r"plans", MembershipPlanViewSet, basename="plans")
router.register(r"enrollments", MembershipEnrollmentViewSet, basename="enrollments")
router.register(r"payments", PaymentViewSet, basename="payments")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),

    # Member CRUD
    path("", include(router.urls)),

    # Trainer CRUD
    path("trainers/", TrainerListCreateView.as_view(), name="trainer-list"),
    path("trainers/<int:pk>/", TrainerDetailView.as_view(), name="trainer-detail"),
]