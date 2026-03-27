from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from utilisateurs.models import Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
	ordering = ("id",)
	list_display = ("id", "nom", "email", "role", "is_active", "is_staff")
	search_fields = ("nom", "email")
	list_filter = ("role", "is_active", "is_staff")
	fieldsets = (
		(None, {"fields": ("email", "password")}),
		("Informations personnelles", {"fields": ("nom", "role")}),
		(
			"Permissions",
			{
				"fields": (
					"is_active",
					"is_staff",
					"is_superuser",
					"groups",
					"user_permissions",
				)
			},
		),
		("Dates", {"fields": ("last_login",)}),
	)
	add_fieldsets = (
		(
			None,
			{
				"classes": ("wide",),
				"fields": ("email", "nom", "password1", "password2", "role", "is_staff", "is_active"),
			},
		),
	)
