import uuid

from django.db import models


class Restaurant(models.Model):
	id = models.BigAutoField(primary_key=True)
	public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
	nom = models.CharField(max_length=160)
	adresse = models.CharField(max_length=255)
	telephone = models.CharField(max_length=30)
	gerant = models.ForeignKey(
		'utilisateurs.Utilisateur',
		related_name='restaurants_geres',
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
	)
	heure_ouverture = models.TimeField(default="10:00")
	heure_fermeture = models.TimeField(default="23:00")
	actif = models.BooleanField(default=True)

	class Meta:
		verbose_name = "Restaurant"
		verbose_name_plural = "Restaurants"

	def __str__(self):
		return self.nom


class Table(models.Model):
	id = models.BigAutoField(primary_key=True)
	public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
	restaurant = models.ForeignKey(Restaurant, related_name="tables", on_delete=models.CASCADE)
	numero = models.PositiveIntegerField()
	capacite = models.PositiveIntegerField()
	est_disponible = models.BooleanField(default=True)

	class Meta:
		verbose_name = "Table"
		verbose_name_plural = "Tables"
		constraints = [
			models.UniqueConstraint(fields=["restaurant", "numero"], name="uq_table_numero_par_restaurant"),
		]

	def __str__(self):
		return f"{self.restaurant.nom} - Table {self.numero}"


class TableDisponibilite(models.Model):
	class JourSemaine(models.IntegerChoices):
		LUNDI = 0, "Lundi"
		MARDI = 1, "Mardi"
		MERCREDI = 2, "Mercredi"
		JEUDI = 3, "Jeudi"
		VENDREDI = 4, "Vendredi"
		SAMEDI = 5, "Samedi"
		DIMANCHE = 6, "Dimanche"

	id = models.BigAutoField(primary_key=True)
	public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
	table = models.ForeignKey(Table, related_name="creneaux_disponibilite", on_delete=models.CASCADE)
	jour_semaine = models.PositiveSmallIntegerField(choices=JourSemaine.choices, null=True, blank=True)
	date_specifique = models.DateField(null=True, blank=True)
	heure_debut = models.TimeField()
	heure_fin = models.TimeField()
	actif = models.BooleanField(default=True)

	class Meta:
		verbose_name = "Disponibilite table"
		verbose_name_plural = "Disponibilites tables"
		constraints = [
			models.CheckConstraint(
				check=(
					(models.Q(jour_semaine__isnull=False) & models.Q(date_specifique__isnull=True))
					| (models.Q(jour_semaine__isnull=True) & models.Q(date_specifique__isnull=False))
				),
				name="ck_table_dispo_jour_xor_date",
			),
			models.CheckConstraint(
				check=models.Q(heure_debut__lt=models.F("heure_fin")),
				name="ck_table_dispo_heure_debut_lt_fin",
			),
		]

	def __str__(self):
		if self.date_specifique:
			cible = self.date_specifique.isoformat()
		else:
			cible = self.get_jour_semaine_display()
		return f"{self.table} - {cible} {self.heure_debut}-{self.heure_fin}"
