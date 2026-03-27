from datetime import timedelta

from django.urls import reverse
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from reservations.models import Reservation, StatutReservation
from reservations.services import marquer_reservations_terminees
from restaurants.models import Restaurant, Table, TableDisponibilite
from utilisateurs.models import Role, Utilisateur


class ReservationWorkflowTests(TestCase):
	def setUp(self):
		self.client_user = Utilisateur.objects.create_user(
			email="client@example.com",
			nom="Client",
			password="secret123",
			role=Role.CLIENT,
		)
		self.manager_user = Utilisateur.objects.create_user(
			email="gerant@example.com",
			nom="Gerant",
			password="secret123",
			role=Role.GESTIONNAIRE,
		)
		self.restaurant = Restaurant.objects.create(
			nom="La Brise",
			adresse="Abidjan",
			telephone="0102030405",
			gerant=self.manager_user,
		)
		self.table = Table.objects.create(
			restaurant=self.restaurant,
			numero=1,
			capacite=4,
			est_disponible=True,
		)

	def test_default_status_is_pending(self):
		reservation = Reservation.objects.create(
			client=self.client_user,
			restaurant=self.restaurant,
			table=self.table,
			date=timezone.localdate() + timedelta(days=1),
			heure=timezone.localtime().time().replace(second=0, microsecond=0),
			nb_personnes=2,
		)

		self.assertEqual(reservation.statut, StatutReservation.EN_ATTENTE)

	def test_past_pending_reservation_is_not_auto_refused(self):
		reservation = Reservation.objects.create(
			client=self.client_user,
			restaurant=self.restaurant,
			table=self.table,
			date=timezone.localdate() - timedelta(days=1),
			heure=timezone.localtime().time().replace(second=0, microsecond=0),
			nb_personnes=2,
			statut=StatutReservation.EN_ATTENTE,
		)

		marquer_reservations_terminees()
		reservation.refresh_from_db()

		self.assertEqual(reservation.statut, StatutReservation.EN_ATTENTE)

	def test_past_confirmed_reservation_becomes_finished(self):
		reservation = Reservation.objects.create(
			client=self.client_user,
			restaurant=self.restaurant,
			table=self.table,
			date=timezone.localdate() - timedelta(days=1),
			heure=timezone.localtime().time().replace(second=0, microsecond=0),
			nb_personnes=2,
			statut=StatutReservation.CONFIRMEE,
		)

		marquer_reservations_terminees()
		reservation.refresh_from_db()

		self.assertEqual(reservation.statut, StatutReservation.TERMINEE)


class ReservationCreationAccessTests(TestCase):
	def setUp(self):
		self.api_client = APIClient()
		self.client_user = Utilisateur.objects.create_user(
			email="client2@example.com",
			nom="Client Two",
			password="secret123",
			role=Role.CLIENT,
		)
		self.manager_user = Utilisateur.objects.create_user(
			email="gerant2@example.com",
			nom="Gerant Two",
			password="secret123",
			role=Role.GESTIONNAIRE,
		)
		self.admin_user = Utilisateur.objects.create_user(
			email="admin2@example.com",
			nom="Admin Two",
			password="secret123",
			role=Role.ADMIN,
		)
		self.restaurant = Restaurant.objects.create(
			nom="Le Palmier",
			adresse="Yopougon",
			telephone="0700000000",
			gerant=self.manager_user,
		)
		self.table = Table.objects.create(
			restaurant=self.restaurant,
			numero=10,
			capacite=6,
			est_disponible=True,
		)
		self.url = reverse("reservations-list")
		self.payload = {
			"restaurant_public_id": str(self.restaurant.public_id),
			"table_public_id": str(self.table.public_id),
			"date": str(timezone.localdate() + timedelta(days=2)),
			"heure": "19:30:00",
			"nb_personnes": 2,
		}
		TableDisponibilite.objects.create(
			table=self.table,
			jour_semaine=(timezone.localdate() + timedelta(days=2)).weekday(),
			heure_debut="18:00:00",
			heure_fin="22:30:00",
		)

	def test_client_can_create_reservation(self):
		self.api_client.force_authenticate(user=self.client_user)

		response = self.api_client.post(self.url, self.payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

	def test_manager_cannot_create_reservation(self):
		self.api_client.force_authenticate(user=self.manager_user)

		response = self.api_client.post(self.url, self.payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
		self.assertIn("Seul un utilisateur CLIENT", str(response.data))

	def test_admin_cannot_create_reservation(self):
		self.api_client.force_authenticate(user=self.admin_user)

		response = self.api_client.post(self.url, self.payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
		self.assertIn("Seul un utilisateur CLIENT", str(response.data))


class DisponibiliteParCreneauTests(TestCase):
	def setUp(self):
		self.api_client = APIClient()
		self.manager_user = Utilisateur.objects.create_user(
			email="gerant3@example.com",
			nom="Gerant Three",
			password="secret123",
			role=Role.GESTIONNAIRE,
		)
		self.restaurant = Restaurant.objects.create(
			nom="Le Lagon",
			adresse="Cocody",
			telephone="0555555555",
			gerant=self.manager_user,
		)
		self.table = Table.objects.create(
			restaurant=self.restaurant,
			numero=3,
			capacite=4,
			est_disponible=True,
		)
		TableDisponibilite.objects.create(
			table=self.table,
			jour_semaine=0,
			heure_debut="18:00:00",
			heure_fin="22:00:00",
		)

	@staticmethod
	def _prochaine_date_pour_jour(jour_semaine):
		today = timezone.localdate()
		decalage = (jour_semaine - today.weekday()) % 7
		if decalage == 0:
			decalage = 7
		return today + timedelta(days=decalage)

	def test_disponibilite_retourne_table_si_creneau_correspond(self):
		date_lundi = self._prochaine_date_pour_jour(0)
		url = reverse("disponibilites")

		response = self.api_client.get(
			url,
			{
				"restaurant_public_id": str(self.restaurant.public_id),
				"date": str(date_lundi),
				"heure": "19:30:00",
				"nb_personnes": 2,
			},
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 1)

	def test_disponibilite_vide_si_hors_creneau(self):
		date_lundi = self._prochaine_date_pour_jour(0)
		url = reverse("disponibilites")

		response = self.api_client.get(
			url,
			{
				"restaurant_public_id": str(self.restaurant.public_id),
				"date": str(date_lundi),
				"heure": "23:30:00",
				"nb_personnes": 2,
			},
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 0)
