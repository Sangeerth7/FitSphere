import json
from django.conf import settings
from django.db import transaction

from accounts.models import DietMeal, DietPlan, Exercise, Trainer, WorkoutPlan
from accounts.services.diet_recommender import (
    _profile_values,
    recommend_diet,
)
from accounts.services.ollama_client import OllamaError, generate_json
from accounts.services.recommendation_schemas import (
    RecommendationValidationError,
    validate_diet_recommendation,
    validate_workout_recommendation,
)
from accounts.services.workout_recommender import (
    _validate_member,
    recommend_workout,
)


class AIRecommendationError(RuntimeError):
    """Raised only when AI and the configured fallback both cannot recommend."""


def _enabled():
    return getattr(settings, "AI_RECOMMENDATIONS_ENABLED", False)


def _diet_profile(member):
    age, height, weight, gender, _activity_factor = _profile_values(member)
    return {
        "age": int(age),
        "height_cm": height,
        "weight_kg": weight,
        "gender": gender,
        "goal": (member.goal or "general_fitness").strip().lower(),
        "activity_level": (member.activity_level or "moderate").lower(),
        "fitness_level": (member.fitness_level or "beginner").lower(),
        "diet_preference": (member.diet_preference or "non_vegetarian").lower(),
        "dietary_restrictions": [item.strip() for item in (member.dietary_restrictions or "").split(",") if item.strip()],
    }


def _workout_profile(member):
    age, height, weight, gender, _goal, activity, fitness = _validate_member(member)
    return {
        "age": int(age),
        "height_cm": height,
        "weight_kg": weight,
        "gender": gender,
        "goal": (member.goal or "general_fitness").strip().lower().replace("-", "_").replace(" ", "_"),
        "activity_level": activity,
        "fitness_level": fitness,
    }


def _prompt(kind, profile):
    if kind == "diet":
        output = {
            "type": "diet",
            "goal": "weight_loss|muscle_gain|maintenance|general_fitness",
            "calories_target": 2000,
            "meals": [{
                "meal_type": "breakfast|mid_morning|lunch|evening_snack|dinner",
                "food": "food description",
                "quantity": "serving size",
                "notes": "optional note",
            }],
        }
    else:
        output = {
            "type": "workout",
            "goal": "weight_loss|muscle_gain|maintenance|general_fitness",
            "weekly_days": 4,
            "exercises": [{
                "day": 1,
                "name": "exercise name",
                "sets": 3,
                "reps": 10,
                "rest_seconds": 60,
                "notes": "optional note",
            }],
        }
    return (
        "You are FitSphere's recommendation assistant. Return only valid JSON, with no markdown. "
        "Give practical, non-medical fitness guidance. Do not include identity, credentials, or database fields. "
        f"Recommendation type: {kind}. Member profile: {json.dumps(profile)}. "
        f"Required JSON shape: {json.dumps(output)}."
    )


def _try_ai(kind, profile):
    payload = generate_json(_prompt(kind, profile))
    if kind == "diet":
        return validate_diet_recommendation(payload, profile)
    return validate_workout_recommendation(payload)


def recommend_diet_with_ai(member):
    """Use validated Ollama output or the existing deterministic diet fallback."""
    _diet_profile(member)
    if not _enabled():
        return recommend_diet(member), "rule_based"
    try:
        profile = _diet_profile(member)
        recommendation = _try_ai("diet", profile)
        with transaction.atomic():
            plan = DietPlan.objects.create(
                member=member,
                name=f"AI {recommendation['goal'].replace('_', ' ').title()} Diet Plan",
                goal=recommendation["goal"],
                description="AI-assisted recommendation validated by FitSphere.",
                calories_target=recommendation["calories_target"],
            )
            DietMeal.objects.bulk_create([
                DietMeal(
                    diet_plan=plan,
                    meal_type=meal["meal_type"],
                    food=meal["food"],
                    quantity=meal["quantity"],
                    notes=meal["notes"],
                )
                for meal in recommendation["meals"]
            ])
        return plan, "ollama"
    except (OllamaError, RecommendationValidationError, ValueError, TypeError, json.JSONDecodeError):
        return recommend_diet(member), "rule_based"


def recommend_workout_with_ai(member):
    """Use validated Ollama output or the existing deterministic workout fallback."""
    _workout_profile(member)
    if not _enabled():
        return recommend_workout(member), "rule_based"
    try:
        profile = _workout_profile(member)
        recommendation = _try_ai("workout", profile)
        trainer = Trainer.objects.order_by("id").first()
        if trainer is None:
            return recommend_workout(member), "rule_based"
        with transaction.atomic():
            plan = WorkoutPlan.objects.create(
                trainer=trainer,
                member=member,
                title=f"AI {recommendation['goal'].replace('_', ' ').title()} Workout Plan",
                description=(
                    f"{recommendation['weekly_days']}-day AI-assisted plan validated by FitSphere."
                ),
            )
            Exercise.objects.bulk_create([
                Exercise(
                    workout=plan,
                    name=exercise["name"],
                    sets=exercise["sets"],
                    reps=exercise["reps"],
                    rest_seconds=exercise["rest_seconds"],
                    notes=f"Day {exercise['day']}: {exercise['notes']}",
                )
                for exercise in recommendation["exercises"]
            ])
        return plan, "ollama"
    except (OllamaError, RecommendationValidationError, ValueError, TypeError, json.JSONDecodeError):
        return recommend_workout(member), "rule_based"
