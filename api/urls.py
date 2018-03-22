from django.conf.urls import url, include

from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import (
    obtain_jwt_token, refresh_jwt_token, verify_jwt_token
)

from . import views

router = DefaultRouter()
router.register(r'notifications', views.NotificationsService)
router.register(r'classes', views.ClassesService)
router.register(r'users', views.UsersService)
router.register(r'schedule', views.ScheduleService)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^auth/$', obtain_jwt_token),
    url(r'^auth/refresh/$', refresh_jwt_token),
    url(r'^auth/verify/$', verify_jwt_token),
    url(r'^auth/user/$', views.AuthUser.as_view()),
    url(r'^auth/user/([0-9]+)/$', views.GetUserParents.as_view()),
    url(r'^subjects/$', views.SubjectsView.as_view()),
    url(r'^chats/$', views.ChatsView.as_view()),
    url(r'^chats/([0-9]+)/$', views.ChatsHistoryView.as_view()),
]
