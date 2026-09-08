from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import DietMeal, DietPlan, Exercise, Member, Trainer, WorkoutPlan
from .services.diet_recommender import (
	RecommendationInputError,
	calculate_calorie_target,
	recommend_diet,
)
from .services.workout_recommender import (
	WorkoutRecommendationError,
	recommend_workout,
)


class DietRecommendationTests(TestCase):
	def setUp(self):
		user = get_user_model().objects.create_user(
			username="diet-member",
			password="test-password",
		)
		self.member = self._create_member(user)

	@staticmethod
	def _create_member(user, **overrides):
		values = {
			"user": user,
			"age": 30,
			"height": 180,
			"weight": 80,
			"gender": "male",
			"goal": "maintenance",
			"activity_level": "moderate",
			"fitness_level": "intermediate",
			"diet_preference": "non_vegetarian",
			"dietary_restrictions": "",
		}
		values.update(overrides)
		return Member.objects.create(**values)

	def test_calorie_calculation_uses_bmr_activity_and_goal(self):
		self.member.goal = "weight_loss"
		self.member.save(update_fields=["goal"])

		self.assertEqual(calculate_calorie_target(self.member), 2350)

	def test_goals_change_calorie_target(self):
		maintenance = calculate_calorie_target(self.member)
		self.member.goal = "weight_loss"
		weight_loss = calculate_calorie_target(self.member)
		self.member.goal = "muscle_gain"
		muscle_gain = calculate_calorie_target(self.member)

		self.assertLess(weight_loss, maintenance)
		self.assertGreater(muscle_gain, maintenance)

	def test_diet_preferences_generate_different_meals(self):
		self.member.diet_preference = "vegetarian"
		self.member.save(update_fields=["diet_preference"])
		vegetarian = recommend_diet(self.member)
		vegetarian_foods = set(vegetarian.meals.values_list("food", flat=True))

		self.member.diet_preference = "vegan"
		self.member.save(update_fields=["diet_preference"])
		vegan = recommend_diet(self.member)
		vegan_foods = set(vegan.meals.values_list("food", flat=True))

		self.assertNotEqual(vegetarian_foods, vegan_foods)
		self.assertTrue(any("soy" in food.lower() for food in vegan_foods))

	def test_dietary_restrictions_remove_restricted_foods(self):
		self.member.diet_preference = "vegetarian"
		self.member.dietary_restrictions = "dairy"
		self.member.save(update_fields=["diet_preference", "dietary_restrictions"])

		diet_plan = recommend_diet(self.member)
		foods = " ".join(diet_plan.meals.values_list("food", flat=True)).lower()

		self.assertNotIn("milk", foods)
		self.assertNotIn("paneer", foods)

	def test_missing_required_data_is_rejected_without_creating_plan(self):
		self.member.age = None
		self.member.save(update_fields=["age"])

		with self.assertRaises(RecommendationInputError):
			recommend_diet(self.member)

		self.assertEqual(DietPlan.objects.count(), 0)

	def test_recommendation_creates_five_meals(self):
		diet_plan = recommend_diet(self.member)

		self.assertEqual(diet_plan.meals.count(), 5)


class WorkoutRecommendationTests(TestCase):
	def setUp(self):
		member_user = get_user_model().objects.create_user(
			username="workout-member",
			password="test-password",
		)
		trainer_user = get_user_model().objects.create_user(
			username="workout-trainer",
			password="test-password",
			role="trainer",
		)
		self.member = Member.objects.create(
			user=member_user,
			age=30,
			height=180,
			weight=80,
			gender="male",
			goal="general_fitness",
			activity_level="moderate",
			fitness_level="intermediate",
		)
		self.trainer = Trainer.objects.create(
			user=trainer_user,
			specialization="Strength training",
			experience=5,
			qualification="Certified trainer",
			salary=30000,
		)

	def test_different_goals_generate_different_plans(self):
		self.member.goal = "weight_loss"
		self.member.save(update_fields=["goal"])
		weight_loss = recommend_workout(self.member, self.trainer)
		self.member.goal = "muscle_gain"
		self.member.save(update_fields=["goal"])
		muscle_gain = recommend_workout(self.member, self.trainer)

		self.assertIn("Weight Loss", weight_loss.title)
		self.assertIn("Muscle Gain", muscle_gain.title)
		self.assertNotEqual(
			set(weight_loss.exercises.values_list("name", flat=True)),
			set(muscle_gain.exercises.values_list("name", flat=True)),
		)

	def test_fitness_level_changes_sets_reps_and_rest(self):
		beginner = recommend_workout(self.member, self.trainer)
		beginner_exercise = beginner.exercises.first()

		self.member.fitness_level = "advanced"
		self.member.save(update_fields=["fitness_level"])
		advanced = recommend_workout(self.member, self.trainer)
		advanced_exercise = advanced.exercises.first()

		self.assertEqual((beginner_exercise.sets, beginner_exercise.reps, beginner_exercise.rest_seconds), (3, 12, 60))
		self.assertEqual((advanced_exercise.sets, advanced_exercise.reps, advanced_exercise.rest_seconds), (4, 10, 45))

	def test_generated_plan_contains_weekly_exercises(self):
		plan = recommend_workout(self.member, self.trainer)

		self.assertIsInstance(plan, WorkoutPlan)
		self.assertEqual(plan.exercises.count(), 6)
		self.assertEqual(Exercise.objects.filter(workout=plan).count(), 6)
		self.assertTrue(all(exercise.notes.startswith("Day ") for exercise in plan.exercises.all()))

	def test_missing_member_data_is_rejected_without_creating_plan(self):
		self.member.height = None
		self.member.save(update_fields=["height"])

		with self.assertRaises(WorkoutRecommendationError):
			recommend_workout(self.member, self.trainer)

		self.assertEqual(WorkoutPlan.objects.count(), 0)

	def test_workout_generation_succeeds_with_existing_trainer(self):
		plan = recommend_workout(self.member, self.trainer)

		self.assertEqual(plan.member, self.member)
		self.assertEqual(plan.trainer, self.trainer)
		self.assertEqual(plan.exercises.first().sets, 3)

	def test_workout_generation_requires_a_trainer(self):
		Trainer.objects.all().delete()

		with self.assertRaises(WorkoutRecommendationError):
			recommend_workout(self.member)

	def test_generate_workout_endpoint_returns_plan_summary(self):
		response = self.client.post(
			reverse("generate-workout", kwargs={"member_id": self.member.id}),
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["exercise_count"], 6)


class DietPlanAPITests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.member_user = get_user_model().objects.create_user(
			username="api-member",
			password="test-password",
			role="member",
		)
		self.admin_user = get_user_model().objects.create_user(
			username="api-admin",
			password="test-password",
			role="admin",
		)
		self.member = Member.objects.create(
			user=self.member_user,
			age=30,
			height=180,
			weight=80,
			gender="male",
			goal="maintenance",
			activity_level="moderate",
			fitness_level="intermediate",
			diet_preference="vegetarian",
		)
		self.plan = DietPlan.objects.create(
			member=self.member,
			name="Test Diet Plan",
			goal="maintenance",
			calories_target=2400,
		)
		DietMeal.objects.create(
			diet_plan=self.plan,
			meal_type="breakfast",
			food="Oats",
			quantity="1 bowl",
		)

	def test_authenticated_user_can_list_diet_plans(self):
		self.client.force_authenticate(user=self.member_user)

		response = self.client.get(reverse("diet-plans-list"))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["count"], 1)

	def test_retrieve_includes_associated_meals(self):
		self.client.force_authenticate(user=self.member_user)

		response = self.client.get(
			reverse("diet-plans-detail", kwargs={"pk": self.plan.id})
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data["meals"]), 1)
		self.assertEqual(response.data["meals"][0]["food"], "Oats")

	def test_unauthenticated_user_cannot_read_diet_plans(self):
		response = self.client.get(reverse("diet-plans-list"))

		self.assertEqual(response.status_code, 401)

	def test_member_cannot_create_diet_plan(self):
		self.client.force_authenticate(user=self.member_user)

		response = self.client.post(
			reverse("diet-plans-list"),
			{"member": self.member.id, "name": "Blocked", "goal": "maintenance"},
		)

		self.assertEqual(response.status_code, 403)

	def test_admin_can_create_diet_plan(self):
		self.client.force_authenticate(user=self.admin_user)

		response = self.client.post(
			reverse("diet-plans-list"),
			{"member": self.member.id, "name": "Admin Plan", "goal": "maintenance"},
		)

		self.assertEqual(response.status_code, 201)

	def test_existing_diet_generation_endpoint_still_works(self):
		self.client.force_authenticate(user=self.member_user)

		response = self.client.post(
			reverse("generate-diet", kwargs={"member_id": self.member.id})
		)

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data["diet_plan_id"])
