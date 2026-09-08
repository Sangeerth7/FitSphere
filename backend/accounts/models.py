from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator


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

    height = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.1)],
        blank=True,
        null=True
    )

    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.1)],
        blank=True,
        null=True
    )

address = models.TextField(blank=True, null=True)
goal = models.CharField(max_length=50, blank=True, null=True)

ACTIVITY_LEVEL_CHOICES = [
    ("sedentary", "Sedentary"),
    ("light", "Light"),
    ("moderate", "Moderate"),
    ("high", "High"),
    ("very_high", "Very High"),
]

FITNESS_LEVEL_CHOICES = [
    ("beginner", "Beginner"),
    ("intermediate", "Intermediate"),
    ("advanced", "Advanced"),
]

DIET_PREFERENCE_CHOICES = [
    ("vegetarian", "Vegetarian"),
    ("non_vegetarian", "Non-Vegetarian"),
    ("vegan", "Vegan"),
    ("eggetarian", "Eggetarian"),
]

activity_level = models.CharField(
    max_length=20,
    choices=ACTIVITY_LEVEL_CHOICES,
    default="moderate",
)

fitness_level = models.CharField(
    max_length=20,
    choices=FITNESS_LEVEL_CHOICES,
    default="beginner",
)

diet_preference = models.CharField(
    max_length=20,
    choices=DIET_PREFERENCE_CHOICES,
    default="non_vegetarian",
)

dietary_restrictions = models.TextField(
    blank=True,
    null=True,
)

join_date = models.DateField(auto_now_add=True)

created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)

def __str__(self):
     return self.user.username


class Trainer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="trainer_profile"
    )

    specialization = models.CharField(max_length=100)

    experience = models.PositiveIntegerField(
        help_text="Years of experience"
    )

    qualification = models.CharField(max_length=150)

    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    availability = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username


class MembershipPlan(models.Model):
    name = models.CharField(max_length=100)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(1)]
    )

    duration_months = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    description = models.TextField(blank=True, null=True)

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

    created_at = models.DateTimeField(auto_now_add=True)

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

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(1)]
    )

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

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.enrollment.member.user.username} - ₹{self.amount}"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
    ]

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

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="present"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["member", "date"],
                name="unique_member_attendance"
            )
        ]

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
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.member.user.username} - {self.title}"


class Exercise(models.Model):
    workout = models.ForeignKey(
        WorkoutPlan,
        on_delete=models.CASCADE,
        related_name="exercises"
    )

    name = models.CharField(max_length=100)

    sets = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    reps = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    rest_seconds = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(0)]
    )

    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name


class DietPlan(models.Model):
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="diet_plans"
    )

    name = models.CharField(max_length=100)

    goal = models.CharField(max_length=50)

    description = models.TextField(blank=True)

    calories_target = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.member.user.username} - {self.name}"


class DietMeal(models.Model):
    MEAL_TYPE_CHOICES = [
        ("breakfast", "Breakfast"),
        ("mid_morning", "Mid-Morning"),
        ("lunch", "Lunch"),
        ("evening_snack", "Evening Snack"),
        ("dinner", "Dinner"),
    ]

    diet_plan = models.ForeignKey(
        DietPlan,
        on_delete=models.CASCADE,
        related_name="meals"
    )

    meal_type = models.CharField(
        max_length=30,
        choices=MEAL_TYPE_CHOICES
    )

    food = models.CharField(max_length=200)

    quantity = models.CharField(
        max_length=100,
        blank=True
    )

    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.diet_plan.name} - {self.get_meal_type_display()}"