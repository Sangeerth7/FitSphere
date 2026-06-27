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