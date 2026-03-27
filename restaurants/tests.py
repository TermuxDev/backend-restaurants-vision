from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from restaurants.models import Restaurant, Table
from utilisateurs.models import Role, Utilisateur


class TableDisponibiliteApiTests(TestCase):
	def setUp(self):
		self.api_client = APIClient()
		self.manager_user = Utilisateur.objects.create_user(
			email="manager.tables@example.com",
			nom="Manager Tables",
			password="secret123",
			role=Role.GESTIONNAIRE,
		)
		self.client_user = Utilisateur.objects.create_user(
			email="client.tables@example.com",
			nom="Client Tables",
			password="secret123",
			role=Role.CLIENT,
		)
		self.restaurant = Restaurant.objects.create(
			nom="Restaurant Profile",
			adresse="Plateau",
			telephone="0111111111",
			gerant=self.manager_user,
		)

	def test_manager_can_create_table_with_disponibilites(self):
		self.api_client.force_authenticate(user=self.manager_user)
		url = reverse("tables-list")
		payload = {
			"restaurant": str(self.restaurant.public_id),
			"numero": 12,
			"capacite": 4,
			"est_disponible": True,
			"disponibilites": [
				{
					"jour_semaine": 5,
					"heure_debut": "12:00:00",
					"heure_fin": "15:00:00",
					"actif": True,
				},
				{
					"date_specifique": "2026-04-10",
					"heure_debut": "19:00:00",
					"heure_fin": "22:30:00",
					"actif": True,
				},
			],
		}

		response = self.api_client.post(url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		table = Table.objects.get(public_id=response.data["public_id"])
		self.assertEqual(table.creneaux_disponibilite.count(), 2)

	def test_restaurant_profile_shows_tables_with_disponibilites(self):
		self.api_client.force_authenticate(user=self.manager_user)
		table = Table.objects.create(
			restaurant=self.restaurant,
			numero=8,
			capacite=2,
			est_disponible=True,
		)
		table.creneaux_disponibilite.create(
			jour_semaine=4,
			heure_debut="18:00:00",
			heure_fin="22:00:00",
			actif=True,
		)

		self.api_client.force_authenticate(user=self.client_user)
		url = reverse("restaurants-detail", args=[self.restaurant.public_id])
		response = self.api_client.get(url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("tables", response.data)
		self.assertEqual(len(response.data["tables"]), 1)
		self.assertEqual(len(response.data["tables"][0]["disponibilites"]), 1)
