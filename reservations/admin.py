from django.contrib import admin
from reservations.models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
	list_display = ("id", "client", "restaurant", "table", "date", "heure", "nb_personnes", "statut")
	list_filter = ("statut", "restaurant", "date")
	search_fields = ("client__email", "restaurant__nom")
