from django.urls import path
from . import views

app_name = 'slideshow'

urlpatterns = [
    path('api/data/', views.slideshow_data, name='slideshow_data'),
]

