"""
Explore Programs URLs now redirect to /courses/.

Legacy path names are preserved so old links and reverse() still resolve,
then bounce users to the unified Courses catalog.
"""
from django.shortcuts import redirect
from django.urls import path

app_name = 'programs'


def redirect_to_courses(request, **kwargs):
    """Ignore legacy hierarchy kwargs; always send users to /courses/."""
    return redirect('courses')


urlpatterns = [
    path('', redirect_to_courses, name='explore_programs'),
    path('search/', redirect_to_courses, name='search'),
    path('purchase/<int:video_id>/', redirect_to_courses, name='purchase_video'),
    path('<str:style_slug>/', redirect_to_courses, name='dance_style'),
    path('<str:style_slug>/<str:category_slug>/', redirect_to_courses, name='category'),
    path(
        '<str:style_slug>/<str:category_slug>/<str:level>/',
        redirect_to_courses,
        name='skill_level',
    ),
    path(
        '<str:style_slug>/<str:category_slug>/<str:level>/<str:video_slug>/',
        redirect_to_courses,
        name='video_detail',
    ),
]
