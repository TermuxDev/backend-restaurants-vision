from django.contrib import admin
from restaurants.models import Restaurant, Table


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
	list_display = ("id", "nom", "telephone", "gerant", "actif")
	search_fields = ("nom", "adresse")
	list_filter = ("actif", "gerant")


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
	list_display = ("id", "restaurant", "numero", "capacite", "est_disponible")
	list_filter = ("est_disponible", "restaurant")
	search_fields = ("restaurant__nom",)
