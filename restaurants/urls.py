from rest_framework.routers import DefaultRouter

from restaurants.views import RestaurantViewSet, TableViewSet

router = DefaultRouter()
router.register(r"tables", TableViewSet, basename="tables")
router.register(r"", RestaurantViewSet, basename="restaurants")

urlpatterns = router.urls
