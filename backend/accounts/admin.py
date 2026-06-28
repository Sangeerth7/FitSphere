from .models import Exercise,WorkoutPlan,Attendance, Payment, User, Member, Trainer ,MembershipPlan,MembershipEnrollment
from django.contrib import admin
admin.site.register(User)
admin.site.register(Member)
admin.site.register(Trainer)
admin.site.register(MembershipPlan)
admin.site.register(MembershipEnrollment)
admin.site.register(Payment)
admin.site.register(Attendance)
admin.site.register(WorkoutPlan)
admin.site.register(Exercise)