from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0015_dietplan_dietmeal"),
    ]

    operations = [
        migrations.AddField(
            model_name="member",
            name="address",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="member",
            name="goal",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="member",
            name="activity_level",
            field=models.CharField(
                choices=[
                    ("sedentary", "Sedentary"),
                    ("light", "Light"),
                    ("moderate", "Moderate"),
                    ("high", "High"),
                    ("very_high", "Very High"),
                ],
                default="moderate",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="member",
            name="fitness_level",
            field=models.CharField(
                choices=[
                    ("beginner", "Beginner"),
                    ("intermediate", "Intermediate"),
                    ("advanced", "Advanced"),
                ],
                default="beginner",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="member",
            name="diet_preference",
            field=models.CharField(
                choices=[
                    ("vegetarian", "Vegetarian"),
                    ("non_vegetarian", "Non-Vegetarian"),
                    ("vegan", "Vegan"),
                    ("eggetarian", "Eggetarian"),
                ],
                default="non_vegetarian",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="member",
            name="dietary_restrictions",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="member",
            name="join_date",
            field=models.DateField(
                auto_now_add=True,
                default=django.utils.timezone.now,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="member",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="member",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
