from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from reservations.models import Reservation, StatutReservation
from reservations.permissions import CreationReservationClientUniquement, EstProprietaireOuAdmin
from reservations.serializers import (
	CreationReservationSerializer,
	DisponibiliteSerializer,
	ModificationReservationSerializer,
	ReservationSerializer,
	TableDisponibleSerializer,
)
from reservations.services import filtrer_reservations, marquer_reservations_terminees, tables_disponibles
from restaurants.models import Restaurant


@extend_schema(
	tags=["Disponibilites"],
	summary="Verifier disponibilite",
	description="Retourne les tables disponibles pour un restaurant, date, heure et capacite donnes, en tenant compte des creneaux de disponibilite configures sur chaque table (jour/date/heure).",
	parameters=[
		OpenApiParameter(name="restaurant_public_id", required=True, type=str, location=OpenApiParameter.QUERY, description="UUID du restaurant"),
		OpenApiParameter(name="date", required=True, type=str, location=OpenApiParameter.QUERY, description="Format YYYY-MM-DD"),
		OpenApiParameter(name="heure", required=True, type=str, location=OpenApiParameter.QUERY, description="Format HH:MM"),
		OpenApiParameter(name="nb_personnes", required=True, type=int, location=OpenApiParameter.QUERY),
	],
	responses={200: TableDisponibleSerializer(many=True)},
	examples=[
		OpenApiExample(
			"Disponibilite - exemple",
			value=[{"public_id": "35d598c6-9988-42a0-a2bc-2f0dfe69d674", "numero": 7, "capacite": 4, "est_disponible": True}],
			response_only=True,
		),
	],
)
class DisponibiliteAPIView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request):
		serializer = DisponibiliteSerializer(data=request.query_params)
		serializer.is_valid(raise_exception=True)
		data = serializer.validated_data

		restaurant = get_object_or_404(Restaurant, public_id=data["restaurant_public_id"])
		tables = tables_disponibles(
			restaurant=restaurant,
			date=data["date"],
			heure=data["heure"],
			nb_personnes=data["nb_personnes"],
		)
		return Response(TableDisponibleSerializer(tables, many=True).data)


@extend_schema_view(
	list=extend_schema(
		tags=["Reservations"],
		summary="Lister les reservations",
		description="Liste paginee. Client: ses reservations. Gestionnaire: reservations de son restaurant. Admin: toutes les reservations.",
		parameters=[
			OpenApiParameter("statut", str, OpenApiParameter.QUERY, description="EN_ATTENTE, CONFIRMEE, REFUSEE, ANNULEE, TERMINEE"),
			OpenApiParameter("date", str, OpenApiParameter.QUERY, description="Filtre par date YYYY-MM-DD"),
			OpenApiParameter("restaurant_public_id", str, OpenApiParameter.QUERY, description="Filtre par UUID restaurant"),
			OpenApiParameter("email_client", str, OpenApiParameter.QUERY, description="Filtre partiel sur email client (admin)."),
			OpenApiParameter("page", int, OpenApiParameter.QUERY),
			OpenApiParameter("taille_page", int, OpenApiParameter.QUERY),
		],
	),
	retrieve=extend_schema(tags=["Reservations"], summary="Detail reservation"),
	create=extend_schema(
		tags=["Reservations"],
		summary="Effectuer une reservation",
		description="Cree une reservation en attente apres verification de capacite et conflit de creneau. Seul un utilisateur avec le role CLIENT peut effectuer cette operation. Le restaurant devra ensuite confirmer ou refuser.",
		request=CreationReservationSerializer,
		responses={
			201: ReservationSerializer,
			403: OpenApiResponse(response=OpenApiTypes.OBJECT, description="Refus: seuls les utilisateurs CLIENT peuvent creer une reservation."),
		},
		examples=[
			OpenApiExample(
				"Creation reservation - requete",
				value={
					"restaurant_public_id": "9c2abb4d-63d4-4059-8f8a-6c77e0c34dc6",
					"table_public_id": "2f69cff5-dcb5-4862-869e-c478ccf7ed8b",
					"date": "2026-03-28",
					"heure": "20:30",
					"nb_personnes": 4,
				},
				request_only=True,
			),
		],
	),
	partial_update=extend_schema(
		tags=["Reservations"],
		summary="Modifier reservation",
		description="Met a jour partiellement une reservation en attente ou confirmee.",
		request=ModificationReservationSerializer,
		responses={200: ReservationSerializer},
	),
)
class ReservationViewSet(
	mixins.ListModelMixin,
	mixins.RetrieveModelMixin,
	mixins.CreateModelMixin,
	mixins.UpdateModelMixin,
	viewsets.GenericViewSet,
):
	queryset = Reservation.objects.select_related("client", "restaurant", "table").all()
	permission_classes = [permissions.IsAuthenticated, EstProprietaireOuAdmin]
	lookup_field = "public_id"

	def get_permissions(self):
		permissions_list = [permissions.IsAuthenticated(), EstProprietaireOuAdmin()]
		if self.action == "create":
			permissions_list.append(CreationReservationClientUniquement())
		return permissions_list

	def get_queryset(self):
		marquer_reservations_terminees()
		queryset = self.queryset
		if self.request.user.est_admin_global():
			return filtrer_reservations(queryset, self.request.query_params)
		if self.request.user.est_gestionnaire_restaurant():
			queryset = queryset.filter(restaurant__gerant=self.request.user)
		else:
			queryset = queryset.filter(client=self.request.user)
		return filtrer_reservations(queryset, self.request.query_params)

	def get_serializer_class(self):
		if self.action == "create":
			return CreationReservationSerializer
		if self.action == "partial_update":
			return ModificationReservationSerializer
		return ReservationSerializer

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		reservation = serializer.save()
		return Response(ReservationSerializer(reservation).data, status=status.HTTP_201_CREATED)

	def partial_update(self, request, *args, **kwargs):
		reservation = self.get_object()
		self.check_object_permissions(request, reservation)

		serializer = self.get_serializer(reservation, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		reservation = serializer.save()
		return Response(ReservationSerializer(reservation).data)

	@action(detail=True, methods=["post"])
	@extend_schema(
		tags=["Reservations"],
		summary="Annuler reservation",
		description="Annule une reservation en attente ou confirmee.",
		responses={200: ReservationSerializer},
	)
	def annuler(self, request, pk=None):
		reservation = self.get_object()
		self.check_object_permissions(request, reservation)
		if reservation.statut in [StatutReservation.ANNULEE, StatutReservation.REFUSEE, StatutReservation.TERMINEE]:
			return Response({"detail": "Cette reservation ne peut plus etre annulee."}, status=status.HTTP_400_BAD_REQUEST)

		reservation.statut = StatutReservation.ANNULEE
		reservation.save(update_fields=["statut", "modifie_le"])
		return Response(ReservationSerializer(reservation).data)

	@action(detail=True, methods=["post"])
	@extend_schema(
		tags=["Reservations"],
		summary="Confirmer reservation",
		description="Permet au gestionnaire du restaurant ou a l'administrateur de confirmer une reservation en attente.",
		responses={200: ReservationSerializer},
		examples=[
			OpenApiExample(
				"Confirmation reservation - reponse",
				value={
					"public_id": "cabd0af6-fb7f-4348-8f48-f8823b1cb36f",
					"client_public_id": "c4b4d1af-a57e-4f16-b6f5-d1fca1d85a66",
					"client_nom": "Jean Dupont",
					"client_email": "jean@exemple.com",
					"restaurant_public_id": "9c2abb4d-63d4-4059-8f8a-6c77e0c34dc6",
					"restaurant_nom": "Le Jardin",
					"restaurant_gerant_nom": "Manager Resto",
					"table_public_id": "2f69cff5-dcb5-4862-869e-c478ccf7ed8b",
					"table_numero": 7,
					"date": "2026-03-28",
					"heure": "20:30:00",
					"nb_personnes": 4,
					"statut": "CONFIRMEE"
				},
				response_only=True,
			),
		],
	)
	def confirmer(self, request, pk=None):
		reservation = self.get_object()
		if not (request.user.est_admin_global() or (request.user.est_gestionnaire_restaurant() and reservation.restaurant.gerant_id == request.user.id)):
			raise PermissionDenied("Vous ne pouvez confirmer que les reservations de votre restaurant.")
		if reservation.statut != StatutReservation.EN_ATTENTE:
			return Response({"detail": "Seules les reservations en attente peuvent etre confirmees."}, status=status.HTTP_400_BAD_REQUEST)
		reservation.statut = StatutReservation.CONFIRMEE
		reservation.save(update_fields=["statut", "modifie_le"])
		return Response(ReservationSerializer(reservation).data)

	@action(detail=True, methods=["post"])
	@extend_schema(
		tags=["Reservations"],
		summary="Refuser reservation",
		description="Permet au gestionnaire du restaurant ou a l'administrateur de refuser une reservation en attente.",
		responses={200: ReservationSerializer},
		examples=[
			OpenApiExample(
				"Refus reservation - reponse",
				value={
					"public_id": "cabd0af6-fb7f-4348-8f48-f8823b1cb36f",
					"client_public_id": "c4b4d1af-a57e-4f16-b6f5-d1fca1d85a66",
					"client_nom": "Jean Dupont",
					"client_email": "jean@exemple.com",
					"restaurant_public_id": "9c2abb4d-63d4-4059-8f8a-6c77e0c34dc6",
					"restaurant_nom": "Le Jardin",
					"restaurant_gerant_nom": "Manager Resto",
					"table_public_id": "2f69cff5-dcb5-4862-869e-c478ccf7ed8b",
					"table_numero": 7,
					"date": "2026-03-28",
					"heure": "20:30:00",
					"nb_personnes": 4,
					"statut": "REFUSEE"
				},
				response_only=True,
			),
		],
	)
	def refuser(self, request, pk=None):
		reservation = self.get_object()
		if not (request.user.est_admin_global() or (request.user.est_gestionnaire_restaurant() and reservation.restaurant.gerant_id == request.user.id)):
			raise PermissionDenied("Vous ne pouvez refuser que les reservations de votre restaurant.")
		if reservation.statut != StatutReservation.EN_ATTENTE:
			return Response({"detail": "Seules les reservations en attente peuvent etre refusees."}, status=status.HTTP_400_BAD_REQUEST)
		reservation.statut = StatutReservation.REFUSEE
		reservation.save(update_fields=["statut", "modifie_le"])
		return Response(ReservationSerializer(reservation).data)

	@action(detail=False, methods=["get"])
	@extend_schema(
		tags=["Reservations"],
		summary="Consulter historique",
		description="Retourne les reservations finalisees ou traitees (REFUSEE, ANNULEE, TERMINEE).",
		parameters=[
			OpenApiParameter("statut", str, OpenApiParameter.QUERY, description="Optionnel: REFUSEE, ANNULEE ou TERMINEE"),
			OpenApiParameter("date", str, OpenApiParameter.QUERY, description="Filtre date YYYY-MM-DD"),
			OpenApiParameter("restaurant_public_id", str, OpenApiParameter.QUERY, description="Filtre par UUID restaurant"),
			OpenApiParameter("page", int, OpenApiParameter.QUERY),
			OpenApiParameter("taille_page", int, OpenApiParameter.QUERY),
		],
		responses={200: ReservationSerializer(many=True)},
	)
	def historique(self, request):
		queryset = self.get_queryset().filter(statut__in=[StatutReservation.REFUSEE, StatutReservation.ANNULEE, StatutReservation.TERMINEE])
		page = self.paginate_queryset(queryset)
		if page is not None:
			serializer = ReservationSerializer(page, many=True)
			return self.get_paginated_response(serializer.data)
		serializer = ReservationSerializer(queryset, many=True)
		return Response(serializer.data)
