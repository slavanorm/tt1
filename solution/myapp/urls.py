from myapp import views

from django.contrib import admin
from django.urls import include, path

from rest_framework import routers,urls



router = routers.SimpleRouter()
router.register("contacts", views.ContactViewSet,basename="contacts")

urlpatterns = [
    path("", include(router.urls)),
    path('api-auth/',
         include('rest_framework.urls', namespace='rest_framework')),
    path("admin/", admin.site.urls),
]
