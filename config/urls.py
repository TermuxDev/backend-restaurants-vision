from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from config.views import accueil    

urlpatterns = [
    path('', accueil, name='accueil'),
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema-api'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema-api'), name='swagger-ui'),
    path('api/auth/', include('utilisateurs.urls')),
    path('api/restaurants/', include('restaurants.urls')),
    path('api/reservations/', include('reservations.urls')),
]
