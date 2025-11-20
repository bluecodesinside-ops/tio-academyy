from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/level/<int:level_id>/', views.level_detail, name='level_detail'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('progress/', views.user_progress, name='user_progress'),
]
