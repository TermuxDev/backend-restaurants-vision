from django.urls import path
from rest_framework.routers import DefaultRouter

from reservations.views import DisponibiliteAPIView, ReservationViewSet

router = DefaultRouter()
router.register(r"", ReservationViewSet, basename="reservations")

urlpatterns = [
    path("disponibilites/", DisponibiliteAPIView.as_view(), name="disponibilites"),
]
urlpatterns += router.urls
