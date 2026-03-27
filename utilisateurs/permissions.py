from rest_framework.permissions import BasePermission

from utilisateurs.models import Role


class EstAdministrateur(BasePermission):
    message = "Action reservee aux administrateurs."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return bool(request.user.est_admin_global())
