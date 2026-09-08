from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import DietPlan
from .services.diet_recommender import (
	RecommendationInputError,
	calculate_calorie_target,
	recommend_diet,
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
		from .models import Member

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
