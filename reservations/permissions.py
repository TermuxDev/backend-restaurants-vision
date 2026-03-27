from rest_framework.permissions import BasePermission

from utilisateurs.models import Role


class EstProprietaireOuAdmin(BasePermission):
    message = "Vous ne pouvez acceder qu'a vos propres reservations."

    def has_object_permission(self, request, view, obj):
        if request.user.est_admin_global():
            return True
        if request.user.est_gestionnaire_restaurant() and obj.restaurant.gerant_id == request.user.id:
            return True
        return obj.client_id == request.user.id


class CreationReservationClientUniquement(BasePermission):
    message = "Seul un utilisateur CLIENT peut effectuer une reservation."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.role == Role.CLIENT
