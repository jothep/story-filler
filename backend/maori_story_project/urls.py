"""
URL configuration for maori_story_project project.
"""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

# Customize Django Admin titles
admin.site.site_header = "Story Fill Administration"
admin.site.site_title = "Story Fill Admin"
admin.site.index_title = "Welcome to Story Fill Management"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)