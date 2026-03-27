import uuid

from django.db import models


class StatutReservation(models.TextChoices):
	EN_ATTENTE = "EN_ATTENTE", "En attente"
	CONFIRMEE = "CONFIRMEE", "Confirmee"
	REFUSEE = "REFUSEE", "Refusee"
	ANNULEE = "ANNULEE", "Annulee"
	TERMINEE = "TERMINEE", "Terminee"


class Reservation(models.Model):
	id = models.BigAutoField(primary_key=True)
	public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
	client = models.ForeignKey('utilisateurs.Utilisateur', related_name='reservations', on_delete=models.CASCADE)
	restaurant = models.ForeignKey('restaurants.Restaurant', related_name='reservations', on_delete=models.CASCADE)
	table = models.ForeignKey('restaurants.Table', related_name='reservations', on_delete=models.PROTECT)
	date = models.DateField()
	heure = models.TimeField()
	nb_personnes = models.PositiveIntegerField()
	statut = models.CharField(max_length=12, choices=StatutReservation.choices, default=StatutReservation.EN_ATTENTE)
	cree_le = models.DateTimeField(auto_now_add=True)
	modifie_le = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = "Reservation"
		verbose_name_plural = "Reservations"
		ordering = ["-date", "-heure", "-id"]

	def __str__(self):
		return f"Reservation #{self.id} - {self.client.email}"
