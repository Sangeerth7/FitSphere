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
    
class Trainer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="trainer_profile"
    )

    specialization = models.CharField(max_length=100)
    experience = models.PositiveIntegerField(help_text="Years of experience")
    qualification = models.CharField(max_length=150)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    availability = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username
    
class MembershipPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_months = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class MembershipEnrollment(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )

    plan = models.ForeignKey(
        MembershipPlan,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )

    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active"
    )

    def __str__(self):
        return f"{self.member.user.username} - {self.plan.name}"
    

class Payment(models.Model):
    PAYMENT_METHODS = [
        ("cash", "Cash"),
        ("upi", "UPI"),
        ("card", "Card"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]

    enrollment = models.ForeignKey(
        MembershipEnrollment,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    payment_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.enrollment.member.user.username} - ₹{self.amount}"
    

class Attendance(models.Model):
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="attendance_records"
    )

    date = models.DateField(auto_now_add=True)

    check_in = models.TimeField()

    check_out = models.TimeField(
        blank=True,
        null=True
    )

    STATUS_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="present"
    )

    def __str__(self):
        return f"{self.member.user.username} - {self.date}"
    

class WorkoutPlan(models.Model):
    trainer = models.ForeignKey(
        Trainer,
        on_delete=models.CASCADE,
        related_name="workout_plans"
    )

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="workout_plans"
    )

    title = models.CharField(max_length=100)

    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member.user.username} - {self.title}"
    

class Exercise(models.Model):
    workout = models.ForeignKey(
        WorkoutPlan,
        on_delete=models.CASCADE,
        related_name="exercises"
    )

    name = models.CharField(max_length=100)

    sets = models.PositiveIntegerField()

    reps = models.PositiveIntegerField()

    rest_seconds = models.PositiveIntegerField(default=60)

    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name