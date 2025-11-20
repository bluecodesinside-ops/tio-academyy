from django.urls import path
from . import views

app_name = 'programs'

urlpatterns = [
    # Level 1: Dance Styles
    path('', views.explore_programs, name='explore_programs'),
    
    # Level 2: Categories
    path('<str:style_slug>/', views.dance_style_detail, name='dance_style'),
    
    # Level 3: Skill Levels
    path('<str:style_slug>/<str:category_slug>/', views.category_detail, name='category'),
    
    # Level 4: Videos
    path('<str:style_slug>/<str:category_slug>/<str:level>/', views.skill_level_detail, name='skill_level'),
    path('<str:style_slug>/<str:category_slug>/<str:level>/<str:video_slug>/', views.video_detail, name='video_detail'),
    
    # Additional functionality
    path('search/', views.search_programs, name='search'),
    path('purchase/<int:video_id>/', views.purchase_video, name='purchase_video'),
]

