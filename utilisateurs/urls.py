from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from utilisateurs.views import (
    ConnexionAPIView,
    InscriptionAPIView,
    ListeUtilisateursAPIView,
    ProfilAPIView,
    RoleUtilisateurAPIView,
)

urlpatterns = [
    path("inscription/", InscriptionAPIView.as_view(), name="inscription"),
    path("connexion/", ConnexionAPIView.as_view(), name="connexion"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("profil/", ProfilAPIView.as_view(), name="profil"),
    path("utilisateurs/", ListeUtilisateursAPIView.as_view(), name="liste-utilisateurs"),
    path("utilisateurs/<str:public_id>/role/", RoleUtilisateurAPIView.as_view(), name="maj-role-utilisateur"),
]
