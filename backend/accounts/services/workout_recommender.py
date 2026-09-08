from django.db import transaction

from accounts.models import Exercise, Trainer, WorkoutPlan


class WorkoutRecommendationError(ValueError):
	"""Raised when a member cannot safely receive a workout recommendation."""


ACTIVITY_DAYS = {
	"sedentary": 3,
	"light": 3,
	"moderate": 4,
	"high": 5,
	"very_high": 5,
}

FITNESS_SETTINGS = {
	"beginner": {"sets": 2, "reps": 10, "rest": 90},
	"intermediate": {"sets": 3, "reps": 12, "rest": 60},
	"advanced": {"sets": 4, "reps": 10, "rest": 45},
}

GOAL_TEMPLATES = {
	"weight_loss": [
		("Bodyweight squat", "Lower-body strength and conditioning"),
		("Walking lunges", "Single-leg conditioning"),
		("Push-ups", "Upper-body strength"),
		("Dumbbell row", "Upper-back strength"),
		("Mountain climbers", "Core conditioning"),
		("Plank", "Core stability"),
	],
	"muscle_gain": [
		("Barbell squat", "Lower-body hypertrophy"),
		("Romanian deadlift", "Posterior-chain strength"),
		("Bench press", "Chest and triceps strength"),
		("Dumbbell row", "Back and biceps strength"),
		("Overhead press", "Shoulder strength"),
		("Plank", "Core stability"),
	],
	"general_fitness": [
		("Bodyweight squat", "Lower-body strength"),
		("Step-ups", "Balance and conditioning"),
		("Push-ups", "Upper-body strength"),
		("Dumbbell row", "Back strength"),
		("Jumping jacks", "Cardiovascular conditioning"),
		("Plank", "Core stability"),
	],
}


def _number(value, field_name):
	try:
		number = float(value)
	except (TypeError, ValueError):
		raise WorkoutRecommendationError(f"A valid {field_name} is required.")
	if number <= 0:
		raise WorkoutRecommendationError(f"A valid {field_name} is required.")
	return number


def _normalise_goal(value):
	goal = (value or "").strip().lower().replace("-", "_").replace(" ", "_")
	aliases = {
		"lose_weight": "weight_loss",
		"fat_loss": "weight_loss",
		"gain_muscle": "muscle_gain",
		"fitness": "general_fitness",
	}
	return aliases.get(goal, goal)


def _validate_member(member):
	age = _number(getattr(member, "age", None), "age")
	height = _number(getattr(member, "height", None), "height")
	weight = _number(getattr(member, "weight", None), "weight")
	if not 13 <= age <= 100:
		raise WorkoutRecommendationError("Age must be between 13 and 100.")
	if not 100 <= height <= 250:
		raise WorkoutRecommendationError("Height must be between 100 and 250 cm.")
	if not 25 <= weight <= 350:
		raise WorkoutRecommendationError("Weight must be between 25 and 350 kg.")

	gender = (getattr(member, "gender", "") or "").strip().lower()
	if gender not in {"m", "male", "man", "f", "female", "woman"}:
		raise WorkoutRecommendationError("Gender is required for workout generation.")

	goal = _normalise_goal(getattr(member, "goal", None))
	if goal not in GOAL_TEMPLATES:
		raise WorkoutRecommendationError("Goal must be weight loss, muscle gain, or general fitness.")

	activity = (getattr(member, "activity_level", "") or "").lower()
	fitness = (getattr(member, "fitness_level", "") or "").lower()
	if activity not in ACTIVITY_DAYS:
		raise WorkoutRecommendationError("A valid activity level is required.")
	if fitness not in FITNESS_SETTINGS:
		raise WorkoutRecommendationError("A valid fitness level is required.")
	return age, height, weight, gender, goal, activity, fitness


@transaction.atomic
def recommend_workout(member, trainer=None):
	"""Create a weekly rule-based workout plan for a member."""
	age, height, weight, gender, goal, activity, fitness = _validate_member(member)
	trainer = trainer or Trainer.objects.order_by("id").first()
	if trainer is None:
		raise WorkoutRecommendationError("At least one trainer is required to generate a workout plan.")

	settings = FITNESS_SETTINGS[fitness]
	workout_days = ACTIVITY_DAYS[activity]
	exercises = GOAL_TEMPLATES[goal]
	plan = WorkoutPlan.objects.create(
		trainer=trainer,
		member=member,
		title=f"{goal.replace('_', ' ').title()} Workout Plan",
		description=(
			f"{workout_days}-day weekly plan for a {fitness} member targeting {goal.replace('_', ' ')}. "
			f"Profile: age {int(age)}, {gender}, {height:g} cm, {weight:g} kg, {activity} activity."
		),
	)

	for index, (name, focus) in enumerate(exercises):
		day = (index % workout_days) + 1
		Exercise.objects.create(
			workout=plan,
			name=name,
			sets=settings["sets"],
			reps=settings["reps"],
			rest_seconds=settings["rest"],
			notes=f"Day {day}: {focus}. Complete with controlled form.",
		)
	return plan
