"""
Programs admin is intentionally empty.

Sellable catalog (name + cover → videos, Stripe unlock) lives under Courses.
Legacy DanceStyle / Category / SkillLevel / Video data remains in the DB
but is hidden so admins see one consolidated list.
"""
from django.contrib import admin

from .models import (
    Category,
    DanceStyle,
    Genre,
    SiteSection,
    SkillLevel,
    UserVideoAccess,
    Video,
    VideoFolder,
)


class _HiddenModelAdmin(admin.ModelAdmin):
    """Keep models registered for migrations/FK resolution; hide from admin index."""

    def get_model_perms(self, request):
        return {}


# Soft-deprecate: unregister any prior registrations, then hide all models.
for _model in (
    Genre,
    SiteSection,
    VideoFolder,
    DanceStyle,
    Category,
    SkillLevel,
    Video,
    UserVideoAccess,
):
    try:
        admin.site.unregister(_model)
    except admin.sites.NotRegistered:
        pass
    admin.site.register(_model, _HiddenModelAdmin)
