from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Notification, Class, ClassTeacherSubject, Schedule


admin.site.register(User, UserAdmin)
admin.site.register(Notification)
admin.site.register(Class)
admin.site.register(ClassTeacherSubject)
admin.site.register(Schedule)
