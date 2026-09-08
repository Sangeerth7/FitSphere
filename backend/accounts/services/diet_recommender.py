from accounts.models import DietPlan, DietMeal


def recommend_diet(member):
    """
    Generate a basic personalized diet plan based on
    the member's goal, activity level and diet preference.
    """

    # Use the member's goal
    goal = (member.goal or "").lower()

    # Create the plan name
    if goal == "weight_loss":
        plan_name = "Weight Loss Diet Plan"
        description = "A diet plan designed to support weight management."
    elif goal == "muscle_gain":
        plan_name = "Muscle Gain Diet Plan"
        description = "A diet plan designed to support muscle gain."
    else:
        plan_name = "Balanced Diet Plan"
        description = "A balanced diet plan based on the member profile."

    # Create DietPlan
    diet_plan = DietPlan.objects.create(
        member=member,
        name=plan_name,
        goal=member.goal or "general_fitness",
        description=description,
        calories_target=None
    )

    # Vegetarian meals
    if member.diet_preference == "vegetarian":

        meals = [
            ("breakfast", "Oats with milk and banana", "1 serving"),
            ("mid_morning", "Seasonal fruit", "1 serving"),
            ("lunch", "Rice, dal and vegetables", "1 plate"),
            ("evening_snack", "Nuts or roasted chickpeas", "1 serving"),
            ("dinner", "Chapati with paneer and vegetables", "1 plate"),
        ]

    # Vegan meals
    elif member.diet_preference == "vegan":

        meals = [
            ("breakfast", "Oats with soy milk and banana", "1 serving"),
            ("mid_morning", "Seasonal fruit", "1 serving"),
            ("lunch", "Rice, dal and vegetables", "1 plate"),
            ("evening_snack", "Roasted chickpeas", "1 serving"),
            ("dinner", "Chapati with lentils and vegetables", "1 plate"),
        ]

    # Eggetarian meals
    elif member.diet_preference == "eggetarian":

        meals = [
            ("breakfast", "Eggs with oats", "1 serving"),
            ("mid_morning", "Seasonal fruit", "1 serving"),
            ("lunch", "Rice, dal and vegetables", "1 plate"),
            ("evening_snack", "Boiled eggs", "2 eggs"),
            ("dinner", "Chapati with egg curry and vegetables", "1 plate"),
        ]

    # Default: non-vegetarian
    else:

        meals = [
            ("breakfast", "Eggs with oats and banana", "1 serving"),
            ("mid_morning", "Seasonal fruit", "1 serving"),
            ("lunch", "Rice, chicken and vegetables", "1 plate"),
            ("evening_snack", "Boiled eggs or nuts", "1 serving"),
            ("dinner", "Chapati with chicken and vegetables", "1 plate"),
        ]

    # Save meals to database
    for meal_type, food, quantity in meals:
        DietMeal.objects.create(
            diet_plan=diet_plan,
            meal_type=meal_type,
            food=food,
            quantity=quantity
        )

    return diet_plan