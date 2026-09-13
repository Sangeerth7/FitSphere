from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch

from .models import (
	Attendance,
	DietMeal,
	DietPlan,
	Exercise,
	Member,
	MembershipEnrollment,
	MembershipPlan,
	Payment,
	Trainer,
	WorkoutPlan,
)
from .services.diet_recommender import (
	RecommendationInputError,
	calculate_calorie_target,
	recommend_diet,
)
from .services.workout_recommender import (
	WorkoutRecommendationError,
	recommend_workout,
)
from .services.ai_recommender import (
	recommend_diet_with_ai,
	recommend_workout_with_ai,
)
from .services.ollama_client import (
	OllamaResponseError,
	OllamaUnavailableError,
	generate_json,
)
from .services.recommendation_schemas import RecommendationValidationError, validate_diet_recommendation


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

	@override_settings(AI_RECOMMENDATIONS_ENABLED=False)
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


class TrainerAPITests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.admin_user = get_user_model().objects.create_user(
			username="trainer-admin",
			password="test-password",
			role="admin",
		)
		self.member_user = get_user_model().objects.create_user(
			username="trainer-member",
			password="test-password",
			role="member",
		)
		self.trainer_user = get_user_model().objects.create_user(
			username="existing-trainer",
			password="test-password",
			role="trainer",
		)
		self.new_trainer_user = get_user_model().objects.create_user(
			username="new-trainer",
			password="test-password",
			role="trainer",
		)
		self.trainer = Trainer.objects.create(
			user=self.trainer_user,
			specialization="Strength training",
			experience=5,
			qualification="Certified trainer",
			salary=30000,
		)

	def test_authenticated_user_can_list_and_retrieve_trainers(self):
		self.client.force_authenticate(user=self.member_user)

		list_response = self.client.get(reverse("trainer-list"))
		detail_response = self.client.get(
			reverse("trainer-detail", kwargs={"pk": self.trainer.id})
		)

		self.assertEqual(list_response.status_code, 200)
		self.assertEqual(detail_response.status_code, 200)
		self.assertEqual(detail_response.data["specialization"], "Strength training")

	def test_admin_can_create_update_and_delete_trainer(self):
		self.client.force_authenticate(user=self.admin_user)
		create_response = self.client.post(
			reverse("trainer-list"),
			{
				"user": self.new_trainer_user.id,
				"specialization": "Mobility",
				"experience": 3,
				"qualification": "Coach",
				"salary": "25000",
			},
		)

		self.assertEqual(create_response.status_code, 201)

		update_response = self.client.patch(
			reverse("trainer-detail", kwargs={"pk": self.trainer.id}),
			{"specialization": "Mobility"},
		)
		delete_response = self.client.delete(
			reverse("trainer-detail", kwargs={"pk": self.trainer.id})
		)

		self.assertEqual(update_response.status_code, 200)
		self.assertEqual(delete_response.status_code, 204)

	def test_non_admin_cannot_mutate_trainers(self):
		self.client.force_authenticate(user=self.member_user)

		response = self.client.patch(
			reverse("trainer-detail", kwargs={"pk": self.trainer.id}),
			{"specialization": "Blocked"},
		)

		self.assertEqual(response.status_code, 403)

	def test_unauthenticated_user_cannot_list_trainers(self):
		response = self.client.get(reverse("trainer-list"))

		self.assertEqual(response.status_code, 401)


class MembershipAPITests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.admin_user = get_user_model().objects.create_user(
			username="membership-admin",
			password="test-password",
			role="admin",
		)
		self.member_user = get_user_model().objects.create_user(
			username="membership-member",
			password="test-password",
			role="member",
		)
		self.member = Member.objects.create(user=self.member_user)
		self.plan = MembershipPlan.objects.create(
			name="Quarterly",
			price="1500.00",
			duration_months=3,
			description="Quarterly access",
		)

	def test_admin_can_create_list_retrieve_update_and_delete_plan(self):
		self.client.force_authenticate(user=self.admin_user)
		create_response = self.client.post(
			reverse("plans-list"),
			{
				"name": "Annual",
				"price": "5000.00",
				"duration_months": 12,
				"description": "Annual access",
			},
		)

		self.assertEqual(create_response.status_code, 201)
		plan_id = create_response.data["id"]
		self.assertEqual(self.client.get(reverse("plans-list")).status_code, 200)
		self.assertEqual(
			self.client.get(reverse("plans-detail", kwargs={"pk": plan_id})).status_code,
			200,
		)
		self.assertEqual(
			self.client.patch(
				reverse("plans-detail", kwargs={"pk": plan_id}),
				{"price": "5500.00"},
			).status_code,
			200,
		)
		self.assertEqual(
			self.client.delete(reverse("plans-detail", kwargs={"pk": plan_id})).status_code,
			204,
		)

	def test_non_admin_cannot_mutate_plans(self):
		self.client.force_authenticate(user=self.member_user)

		response = self.client.post(
			reverse("plans-list"),
			{"name": "Blocked", "price": "1000", "duration_months": 1},
		)

		self.assertEqual(response.status_code, 403)

	def test_member_can_create_enrollment_and_end_date_is_calculated(self):
		self.client.force_authenticate(user=self.member_user)

		response = self.client.post(
			reverse("enrollments-list"),
			{"member": self.member.id, "plan": self.plan.id, "start_date": "2026-09-12"},
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data["end_date"], "2026-12-12")

	def test_invalid_member_or_plan_returns_validation_error(self):
		self.client.force_authenticate(user=self.member_user)

		invalid_member = self.client.post(
			reverse("enrollments-list"),
			{"member": 99999, "plan": self.plan.id, "start_date": "2026-09-12"},
		)
		invalid_plan = self.client.post(
			reverse("enrollments-list"),
			{"member": self.member.id, "plan": 99999, "start_date": "2026-09-12"},
		)

		self.assertEqual(invalid_member.status_code, 400)
		self.assertEqual(invalid_plan.status_code, 400)

	def test_unauthenticated_user_cannot_access_membership_apis(self):
		self.assertEqual(self.client.get(reverse("plans-list")).status_code, 401)
		self.assertEqual(self.client.get(reverse("enrollments-list")).status_code, 401)


class PaymentAPITests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.member_user = get_user_model().objects.create_user(
			username="payment-member",
			password="test-password",
			role="member",
		)
		self.member = Member.objects.create(user=self.member_user)
		self.plan = MembershipPlan.objects.create(
			name="Payment Plan",
			price="1750.00",
			duration_months=3,
		)
		self.enrollment = MembershipEnrollment.objects.create(
			member=self.member,
			plan=self.plan,
			start_date="2026-09-12",
			end_date="2026-12-12",
		)

	def test_authenticated_user_can_create_payment_with_derived_amount(self):
		self.client.force_authenticate(user=self.member_user)

		response = self.client.post(
			reverse("payments-list"),
			{
				"enrollment": self.enrollment.id,
				"amount": "1.00",
				"payment_method": "upi",
				"status": "paid",
			},
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data["amount"], "1750.00")

	def test_payment_list_and_retrieve_require_authentication(self):
		payment = Payment.objects.create(
			enrollment=self.enrollment,
			amount=self.plan.price,
			payment_method="cash",
			status="pending",
		)

		self.assertEqual(self.client.get(reverse("payments-list")).status_code, 401)
		self.client.force_authenticate(user=self.member_user)
		self.assertEqual(self.client.get(reverse("payments-list")).status_code, 200)
		self.assertEqual(
			self.client.get(reverse("payments-detail", kwargs={"pk": payment.id})).status_code,
			200,
		)

	def test_invalid_enrollment_returns_validation_error(self):
		self.client.force_authenticate(user=self.member_user)

		response = self.client.post(
			reverse("payments-list"),
			{"enrollment": 99999, "payment_method": "card", "status": "paid"},
		)

		self.assertEqual(response.status_code, 400)

	def test_payment_methods_and_statuses_are_validated(self):
		self.client.force_authenticate(user=self.member_user)

		response = self.client.post(
			reverse("payments-list"),
			{"enrollment": self.enrollment.id, "payment_method": "bitcoin", "status": "paid"},
		)

		self.assertEqual(response.status_code, 400)


class AttendanceAPITests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = get_user_model().objects.create_user(
			username="attendance-member",
			password="test-password",
			role="member",
		)
		self.member = Member.objects.create(user=self.user)

	def test_authenticated_user_can_mark_attendance(self):
		self.client.force_authenticate(user=self.user)

		response = self.client.post(
			reverse("attendance-list"),
			{
				"member": self.member.id,
				"check_in": "09:00:00",
				"status": "present",
			},
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data["member"], self.member.id)
		self.assertEqual(response.data["check_in"], "09:00:00")
		self.assertIsNotNone(response.data["date"])

	def test_attendance_can_be_listed_and_retrieved(self):
		attendance = Attendance.objects.create(
			member=self.member,
			check_in="09:00:00",
			check_out="17:00:00",
			status="present",
		)
		self.client.force_authenticate(user=self.user)

		list_response = self.client.get(reverse("attendance-list"))
		detail_response = self.client.get(
			reverse("attendance-detail", kwargs={"pk": attendance.id})
		)

		self.assertEqual(list_response.status_code, 200)
		self.assertEqual(detail_response.status_code, 200)
		self.assertEqual(detail_response.data["check_out"], "17:00:00")

	def test_attendance_can_be_updated_and_deleted(self):
		attendance = Attendance.objects.create(
			member=self.member,
			check_in="09:00:00",
			status="present",
		)
		self.client.force_authenticate(user=self.user)

		update_response = self.client.patch(
			reverse("attendance-detail", kwargs={"pk": attendance.id}),
			{"check_out": "17:00:00", "status": "present"},
		)
		delete_response = self.client.delete(
			reverse("attendance-detail", kwargs={"pk": attendance.id})
		)

		self.assertEqual(update_response.status_code, 200)
		self.assertEqual(delete_response.status_code, 204)

	def test_invalid_member_returns_validation_error(self):
		self.client.force_authenticate(user=self.user)

		response = self.client.post(
			reverse("attendance-list"),
			{"member": 99999, "check_in": "09:00:00", "status": "present"},
		)

		self.assertEqual(response.status_code, 400)

	def test_unauthenticated_user_cannot_access_attendance(self):
		self.assertEqual(self.client.get(reverse("attendance-list")).status_code, 401)


class CorsLoginTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(
			username="cors-member",
			password="test-password",
			role="member",
		)

	def test_login_preflight_allows_only_frontend_origin(self):
		response = self.client.options(
			reverse("login"),
			HTTP_ORIGIN="http://localhost:5173",
			HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
			HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type",
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(
			response["Access-Control-Allow-Origin"],
			"http://localhost:5173",
		)

	def test_login_response_allows_frontend_origin_and_returns_jwt(self):
		response = self.client.post(
			reverse("login"),
			{"username": "cors-member", "password": "test-password"},
			HTTP_ORIGIN="http://localhost:5173",
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(
			response["Access-Control-Allow-Origin"],
			"http://localhost:5173",
		)
		self.assertIn("access", response.json())

	def test_other_origins_are_not_allowed(self):
		response = self.client.options(
			reverse("login"),
			HTTP_ORIGIN="http://localhost:5174",
			HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
		)

		self.assertNotIn("Access-Control-Allow-Origin", response)


class AIRecommendationTests(TestCase):
	def setUp(self):
		member_user = get_user_model().objects.create_user(
			username="ai-member",
			password="test-password",
		)
		trainer_user = get_user_model().objects.create_user(
			username="ai-trainer",
			password="test-password",
			role="trainer",
		)
		self.member = Member.objects.create(
			user=member_user,
			age=30,
			height=180,
			weight=80,
			gender="male",
			goal="weight_loss",
			activity_level="moderate",
			fitness_level="intermediate",
			diet_preference="vegetarian",
			dietary_restrictions="",
		)
		self.trainer = Trainer.objects.create(
			user=trainer_user,
			specialization="Strength training",
			experience=5,
			qualification="Certified trainer",
			salary=30000,
		)

	@staticmethod
	def diet_payload(food="Oats with banana"):
		return {
			"type": "diet",
			"goal": "weight_loss",
			"calories_target": 2100,
			"meals": [
				{"meal_type": "breakfast", "food": food, "quantity": "1 serving", "notes": ""},
				{"meal_type": "lunch", "food": "Rice and dal", "quantity": "1 plate", "notes": ""},
			],
		}

	@staticmethod
	def workout_payload():
		return {
			"type": "workout",
			"goal": "weight_loss",
			"weekly_days": 3,
			"exercises": [
				{"day": 1, "name": "Bodyweight squat", "sets": 3, "reps": 12, "rest_seconds": 60, "notes": "Controlled form"},
			],
		}

	@override_settings(AI_RECOMMENDATIONS_ENABLED=True)
	@patch("accounts.services.ai_recommender.generate_json")
	def test_successful_ai_diet_recommendation_is_saved(self, generate_json):
		generate_json.return_value = self.diet_payload()

		plan, source = recommend_diet_with_ai(self.member)

		self.assertEqual(source, "ollama")
		self.assertEqual(plan.calories_target, 2100)
		self.assertEqual(plan.meals.count(), 2)

	@override_settings(AI_RECOMMENDATIONS_ENABLED=True)
	@patch("accounts.services.ai_recommender.generate_json")
	def test_successful_ai_workout_recommendation_is_saved(self, generate_json):
		generate_json.return_value = self.workout_payload()

		plan, source = recommend_workout_with_ai(self.member)

		self.assertEqual(source, "ollama")
		self.assertEqual(plan.exercises.count(), 1)
		self.assertEqual(plan.exercises.first().sets, 3)

	@override_settings(AI_RECOMMENDATIONS_ENABLED=True)
	@patch("accounts.services.ai_recommender.generate_json")
	def test_invalid_json_uses_rule_based_diet_fallback(self, generate_json):
		generate_json.side_effect = OllamaResponseError("bad JSON")

		plan, source = recommend_diet_with_ai(self.member)

		self.assertEqual(source, "rule_based")
		self.assertEqual(plan.meals.count(), 5)

	@override_settings(AI_RECOMMENDATIONS_ENABLED=True)
	@patch("accounts.services.ai_recommender.generate_json")
	def test_invalid_schema_uses_rule_based_workout_fallback(self, generate_json):
		generate_json.return_value = {"type": "workout", "goal": "weight_loss", "weekly_days": 99, "exercises": []}

		plan, source = recommend_workout_with_ai(self.member)

		self.assertEqual(source, "rule_based")
		self.assertEqual(plan.exercises.count(), 6)

	@override_settings(AI_RECOMMENDATIONS_ENABLED=True)
	@patch("accounts.services.ai_recommender.generate_json")
	def test_unavailable_ollama_uses_rule_based_diet_fallback(self, generate_json):
		generate_json.side_effect = OllamaUnavailableError("offline")

		plan, source = recommend_diet_with_ai(self.member)

		self.assertEqual(source, "rule_based")
		self.assertIn("Rule-based", plan.description)

	@override_settings(AI_RECOMMENDATIONS_ENABLED=True)
	@patch("accounts.services.ai_recommender.generate_json")
	def test_timeout_uses_rule_based_workout_fallback(self, generate_json):
		generate_json.side_effect = OllamaUnavailableError("timeout")

		plan, source = recommend_workout_with_ai(self.member)

		self.assertEqual(source, "rule_based")
		self.assertEqual(plan.exercises.count(), 6)

	@override_settings(AI_RECOMMENDATIONS_ENABLED=True)
	@patch("accounts.services.ai_recommender.generate_json")
	def test_restricted_food_is_rejected_before_ai_write(self, generate_json):
		self.member.dietary_restrictions = "dairy"
		self.member.save(update_fields=["dietary_restrictions"])
		generate_json.return_value = self.diet_payload("Oats with milk")

		plan, source = recommend_diet_with_ai(self.member)

		self.assertEqual(source, "rule_based")
		self.assertEqual(DietPlan.objects.count(), 1)
		self.assertNotIn("milk", " ".join(plan.meals.values_list("food", flat=True)).lower())

	def test_safe_numeric_validation_rejects_invalid_ai_calories(self):
		with self.assertRaises(RecommendationValidationError):
			validate_diet_recommendation(
				{**self.diet_payload(), "calories_target": 99999},
				{"dietary_restrictions": []},
			)

	@override_settings(AI_RECOMMENDATIONS_ENABLED=True)
	@patch("accounts.services.ai_recommender.generate_json")
	def test_invalid_ai_response_does_not_write_partial_plan(self, generate_json):
		generate_json.return_value = {"type": "diet", "goal": "weight_loss", "calories_target": 2100, "meals": [{"food": "Missing meal type"}]}

		plan, source = recommend_diet_with_ai(self.member)

		self.assertEqual(source, "rule_based")
		self.assertEqual(DietPlan.objects.count(), 1)
		self.assertEqual(plan.name, "Weight Loss Diet Plan")

	@patch("accounts.services.ollama_client.urlopen", side_effect=TimeoutError)
	def test_ollama_timeout_is_converted_to_unavailable_error(self, urlopen):
		with self.assertRaises(OllamaUnavailableError):
			generate_json("test prompt")

