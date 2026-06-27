from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("trainer", "Trainer"),
        ("member", "Member"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_image = models.ImageField(upload_to="profile_images/", blank=True, null=True)

    def __str__(self):
        return self.username


class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10)
    height = models.FloatField()
    weight = models.FloatField()
    goal = models.CharField(max_length=50)

    def __str__(self):
        return self.user.username