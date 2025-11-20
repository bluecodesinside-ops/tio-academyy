from django.urls import path
from . import views

app_name = 'gallery'

urlpatterns = [
    path('', views.gallery_view, name='gallery'),
    path('cassia/', views.gallery_cassia_view, name='gallery_cassia'),
    path('upload/', views.upload_media, name='upload_media'),
    path('download/', views.download_image, name='download_image'),
    path('api/photos/', views.api_photos, name='api_photos'),
    path('api/videos/', views.api_videos, name='api_videos'),
]
