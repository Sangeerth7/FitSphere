import re

from django.db import transaction

from accounts.models import DietMeal, DietPlan


class RecommendationInputError(ValueError):
    """Raised when a member profile cannot support a safe recommendation."""


ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "high": 1.725,
    "very_high": 1.9,
}

GOAL_ADJUSTMENTS = {
    "weight_loss": -400,
    "muscle_gain": 250,
    "maintenance": 0,
    "general_fitness": 0,
}

FITNESS_PROTEIN_FACTORS = {
    "beginner": 1.4,
    "intermediate": 1.6,
    "advanced": 1.8,
}

RESTRICTION_ALIASES = {
    "dairy": {"dairy", "milk", "cheese", "paneer", "yogurt", "butter"},
    "eggs": {"egg", "eggs"},
    "gluten": {"gluten", "wheat", "bread", "chapati", "pasta"},
    "nuts": {"nut", "nuts", "peanut", "peanuts", "almond", "almonds"},
    "soy": {"soy", "tofu", "soybean"},
    "fish": {"fish", "salmon", "tuna"},
    "shellfish": {"shellfish", "shrimp", "prawn", "crab"},
    "chicken": {"chicken"},
    "meat": {"meat", "beef", "pork", "mutton"},
}

MEAL_TEMPLATES = {
    "vegetarian": [
        ("breakfast", "Oats with milk and banana", "1 serving", {"oats", "milk"}),
        ("mid_morning", "Seasonal fruit", "1 serving", {"fruit"}),
        ("lunch", "Rice, dal and vegetables", "1 plate", {"rice", "dal", "vegetables"}),
        ("evening_snack", "Roasted chickpeas", "1 serving", {"chickpeas"}),
        ("dinner", "Chapati with paneer and vegetables", "1 plate", {"chapati", "wheat", "paneer"}),
    ],
    "vegan": [
        ("breakfast", "Oats with soy milk and banana", "1 serving", {"oats", "soy", "banana"}),
        ("mid_morning", "Seasonal fruit", "1 serving", {"fruit"}),
        ("lunch", "Rice, lentils and vegetables", "1 plate", {"rice", "lentils", "vegetables"}),
        ("evening_snack", "Roasted chickpeas", "1 serving", {"chickpeas"}),
        ("dinner", "Quinoa with lentils and vegetables", "1 plate", {"quinoa", "lentils", "vegetables"}),
    ],
    "eggetarian": [
        ("breakfast", "Eggs with oats and banana", "1 serving", {"eggs", "oats"}),
        ("mid_morning", "Seasonal fruit", "1 serving", {"fruit"}),
        ("lunch", "Rice, dal and vegetables", "1 plate", {"rice", "dal", "vegetables"}),
        ("evening_snack", "Boiled eggs", "2 eggs", {"eggs"}),
        ("dinner", "Chapati with egg curry and vegetables", "1 plate", {"chapati", "wheat", "eggs"}),
    ],
    "non_vegetarian": [
        ("breakfast", "Eggs with oats and banana", "1 serving", {"eggs", "oats"}),
        ("mid_morning", "Seasonal fruit", "1 serving", {"fruit"}),
        ("lunch", "Rice, chicken and vegetables", "1 plate", {"rice", "chicken", "vegetables"}),
        ("evening_snack", "Boiled eggs", "2 eggs", {"eggs"}),
        ("dinner", "Rice with chicken and vegetables", "1 plate", {"rice", "chicken", "vegetables"}),
    ],
}


def _number(value, field_name):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise RecommendationInputError(f"A valid {field_name} is required.")

    if number <= 0:
        raise RecommendationInputError(f"A valid {field_name} is required.")
    return number


def _normalise_goal(value):
    goal = (value or "general_fitness").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "lose_weight": "weight_loss",
        "fat_loss": "weight_loss",
        "gain_muscle": "muscle_gain",
        "maintain": "maintenance",
    }
    return aliases.get(goal, goal if goal in GOAL_ADJUSTMENTS else "general_fitness")


def _profile_values(member):
    age = _number(getattr(member, "age", None), "age")
    height = _number(getattr(member, "height", None), "height")
    weight = _number(getattr(member, "weight", None), "weight")

    if not 13 <= age <= 100:
        raise RecommendationInputError("Age must be between 13 and 100.")
    if not 100 <= height <= 250:
        raise RecommendationInputError("Height must be between 100 and 250 cm.")
    if not 25 <= weight <= 350:
        raise RecommendationInputError("Weight must be between 25 and 350 kg.")

    gender = (getattr(member, "gender", "") or "").strip().lower()
    if gender in {"m", "male", "man"}:
        gender = "male"
    elif gender in {"f", "female", "woman"}:
        gender = "female"
    else:
        raise RecommendationInputError("Gender must be male or female for calorie estimation.")

    activity = (getattr(member, "activity_level", "moderate") or "moderate").lower()
    return age, height, weight, gender, ACTIVITY_FACTORS.get(activity, ACTIVITY_FACTORS["moderate"])


def calculate_calorie_target(member):
    """Estimate daily calories using BMR, activity, and goal adjustment."""
    age, height, weight, gender, activity_factor = _profile_values(member)
    bmr = (10 * weight) + (6.25 * height) - (5 * age)
    bmr += 5 if gender == "male" else -161
    maintenance = bmr * activity_factor
    target = maintenance + GOAL_ADJUSTMENTS[_normalise_goal(getattr(member, "goal", None))]
    return max(1200, min(5000, int(round(target / 50) * 50)))


def _blocked_ingredients(restrictions):
    values = re.split(r"[,;\n]+", (restrictions or "").lower())
    blocked = set()
    for value in values:
        token = value.strip()
        if not token:
            continue
        matched = False
        for aliases in RESTRICTION_ALIASES.values():
            if token in aliases or any(alias in token for alias in aliases):
                blocked.update(aliases)
                matched = True
        if not matched:
            blocked.add(token)
    return blocked


def _safe_meals(member):
    preference = getattr(member, "diet_preference", "non_vegetarian") or "non_vegetarian"
    templates = MEAL_TEMPLATES.get(preference, MEAL_TEMPLATES["non_vegetarian"])
    blocked = _blocked_ingredients(getattr(member, "dietary_restrictions", None))
    meals = [meal for meal in templates if not meal[3].intersection(blocked)]
    fallback_options = [
        ("meal", "Plain quinoa", "1 serving", {"quinoa"}),
        ("meal", "Plain rice", "1 serving", {"rice"}),
        ("meal", "Plain potatoes", "1 serving", {"potatoes"}),
        ("meal", "Seasonal fruit", "1 serving", {"fruit"}),
        ("meal", "Lentils with vegetables", "1 serving", {"lentils", "vegetables"}),
    ]
    safe_fallbacks = [meal for meal in fallback_options if not meal[3].intersection(blocked)]
    meals.extend(safe_fallbacks[: max(0, 5 - len(meals))])
    if len(meals) < 5:
        raise RecommendationInputError("Dietary restrictions leave no safe meal recommendations.")
    return meals[:5]


@transaction.atomic
def recommend_diet(member):
    """Create a safe, explainable diet recommendation for a member."""
    calories = calculate_calorie_target(member)
    goal = _normalise_goal(getattr(member, "goal", None))
    fitness_level = getattr(member, "fitness_level", "beginner") or "beginner"
    protein_factor = FITNESS_PROTEIN_FACTORS.get(fitness_level, FITNESS_PROTEIN_FACTORS["beginner"])
    protein_target = round(_number(getattr(member, "weight", None), "weight") * protein_factor)
    plan_names = {
        "weight_loss": "Weight Loss Diet Plan",
        "muscle_gain": "Muscle Gain Diet Plan",
        "maintenance": "Maintenance Diet Plan",
        "general_fitness": "Balanced Fitness Diet Plan",
    }
    description = (
        f"Rule-based plan targeting approximately {calories} calories per day "
        f"and {protein_target} g protein for a {fitness_level} fitness level."
    )
    diet_plan = DietPlan.objects.create(
        member=member,
        name=plan_names[goal],
        goal=goal,
        description=description,
        calories_target=calories,
    )
    for meal_type, food, quantity, _ingredients in _safe_meals(member):
        DietMeal.objects.create(
            diet_plan=diet_plan,
            meal_type=meal_type if meal_type != "meal" else "evening_snack",
            food=food,
            quantity=quantity,
        )
    return diet_plan