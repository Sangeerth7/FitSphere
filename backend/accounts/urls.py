from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, LoginView, MemberViewSet

router = DefaultRouter()
router.register("members", MemberViewSet)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("", include(router.urls)),
]


from .views import (
    RegisterView,
    LoginView,
    TrainerListCreateView,
    TrainerDetailView,
)

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),

    path("trainers/", TrainerListCreateView.as_view()),
    path("trainers/<int:pk>/", TrainerDetailView.as_view()),
]