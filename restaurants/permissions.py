from rest_framework.permissions import SAFE_METHODS, BasePermission

class LecturePubliqueEcritureAdmin(BasePermission):
    message = "Seuls les administrateurs peuvent modifier cette ressource."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if not (request.user and request.user.is_authenticated):
            return False
        return bool(request.user.est_admin_global())


class GestionRestaurantOuAdmin(BasePermission):
    message = "Action reservee a l'administrateur ou au gestionnaire du restaurant concerne."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.est_admin_global():
            return True

        restaurant = getattr(obj, "restaurant", obj)
        return bool(request.user.est_gestionnaire_restaurant() and restaurant.gerant_id == request.user.id)
