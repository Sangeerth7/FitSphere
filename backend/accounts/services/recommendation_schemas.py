from accounts.services.diet_recommender import RESTRICTION_ALIASES


class RecommendationValidationError(ValueError):
    """Raised when an AI recommendation is not safe to persist."""


VALID_GOALS = {"weight_loss", "muscle_gain", "maintenance", "general_fitness"}
VALID_MEAL_TYPES = {"breakfast", "mid_morning", "lunch", "evening_snack", "dinner"}
VALID_DIET_PREFERENCES = {"vegetarian", "vegan", "eggetarian", "non_vegetarian"}


def _required_dict(value, name):
    if not isinstance(value, dict):
        raise RecommendationValidationError(f"{name} must be an object.")
    return value


def _positive_int(value, name, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise RecommendationValidationError(f"{name} must be an integer from {minimum} to {maximum}.")
    return value


def _goal(value):
    if value not in VALID_GOALS:
        raise RecommendationValidationError("Recommendation contains an invalid goal.")
    return value


def _restriction_tokens(restrictions):
    tokens = set()
    for restriction in restrictions or []:
        token = str(restriction).strip().lower()
        if not token:
            continue
        matched = False
        for aliases in RESTRICTION_ALIASES.values():
            if token in aliases or any(alias in token for alias in aliases):
                tokens.update(aliases)
                matched = True
        if not matched:
            tokens.add(token)
    return tokens


def validate_diet_recommendation(payload, member_profile):
    payload = _required_dict(payload, "Diet recommendation")
    if payload.get("type") != "diet":
        raise RecommendationValidationError("Recommendation type must be diet.")
    goal = _goal(payload.get("goal"))
    calories = _positive_int(payload.get("calories_target"), "calories_target", 1200, 5000)
    meals = payload.get("meals")
    if not isinstance(meals, list) or not 1 <= len(meals) <= 5:
        raise RecommendationValidationError("Diet recommendation must contain one to five meals.")

    restrictions = _restriction_tokens(member_profile.get("dietary_restrictions"))
    validated_meals = []
    seen_types = set()
    for meal in meals:
        meal = _required_dict(meal, "Meal")
        meal_type = meal.get("meal_type")
        food = meal.get("food")
        quantity = meal.get("quantity")
        if meal_type not in VALID_MEAL_TYPES or meal_type in seen_types:
            raise RecommendationValidationError("Meal types must be valid and unique.")
        if not isinstance(food, str) or not food.strip() or len(food) > 200:
            raise RecommendationValidationError("Each meal must have a valid food description.")
        if not isinstance(quantity, str) or not quantity.strip() or len(quantity) > 100:
            raise RecommendationValidationError("Each meal must have a valid quantity.")
        food_lower = food.lower()
        if any(restriction in food_lower for restriction in restrictions):
            raise RecommendationValidationError("Recommendation contains a restricted food.")
        seen_types.add(meal_type)
        validated_meals.append({
            "meal_type": meal_type,
            "food": food.strip(),
            "quantity": quantity.strip(),
            "notes": str(meal.get("notes", ""))[:500],
        })
    return {"type": "diet", "goal": goal, "calories_target": calories, "meals": validated_meals}


def validate_workout_recommendation(payload):
    payload = _required_dict(payload, "Workout recommendation")
    if payload.get("type") != "workout":
        raise RecommendationValidationError("Recommendation type must be workout.")
    goal = _goal(payload.get("goal"))
    weekly_days = _positive_int(payload.get("weekly_days"), "weekly_days", 1, 7)
    exercises = payload.get("exercises")
    if not isinstance(exercises, list) or not 1 <= len(exercises) <= 30:
        raise RecommendationValidationError("Workout recommendation must contain exercises.")

    validated_exercises = []
    for exercise in exercises:
        exercise = _required_dict(exercise, "Exercise")
        name = exercise.get("name")
        day = _positive_int(exercise.get("day"), "day", 1, weekly_days)
        if not isinstance(name, str) or not name.strip() or len(name) > 100:
            raise RecommendationValidationError("Each exercise must have a valid name.")
        validated_exercises.append({
            "day": day,
            "name": name.strip(),
            "sets": _positive_int(exercise.get("sets"), "sets", 1, 10),
            "reps": _positive_int(exercise.get("reps"), "reps", 1, 100),
            "rest_seconds": _positive_int(exercise.get("rest_seconds"), "rest_seconds", 0, 600),
            "notes": str(exercise.get("notes", ""))[:500],
        })
    return {"type": "workout", "goal": goal, "weekly_days": weekly_days, "exercises": validated_exercises}
