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
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="member_profile"
    )

    phone = models.CharField(max_length=15, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    goal = models.CharField(max_length=50, blank=True, null=True)

    join_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.user.username