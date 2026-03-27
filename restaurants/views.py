from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework.exceptions import PermissionDenied
from rest_framework import filters, viewsets

from restaurants.models import Restaurant, Table
from restaurants.permissions import GestionRestaurantOuAdmin
from restaurants.serializers import RestaurantSerializer, TableSerializer


@extend_schema_view(
	list=extend_schema(
		tags=["Restaurants"],
		summary="Lister les restaurants",
		description="Liste paginee des restaurants avec recherche par nom/adresse. Un restaurant peut etre rattache a un gestionnaire.",
		parameters=[
			OpenApiParameter("search", str, OpenApiParameter.QUERY, description="Recherche par nom ou adresse."),
			OpenApiParameter("ordering", str, OpenApiParameter.QUERY, description="Tri: public_id, -public_id, nom, -nom."),
			OpenApiParameter("page", int, OpenApiParameter.QUERY, description="Numero de page."),
			OpenApiParameter("taille_page", int, OpenApiParameter.QUERY, description="Taille de page (max 100)."),
		],
	),
	retrieve=extend_schema(
		tags=["Restaurants"],
		summary="Detail restaurant",
		description="Retourne le profil du restaurant avec ses tables et leurs creneaux de disponibilite (jour/date/heure).",
	),
	create=extend_schema(tags=["Restaurants"], summary="Creer restaurant (admin)", description="Creation d un restaurant avec affectation eventuelle d un gestionnaire."),
	update=extend_schema(tags=["Restaurants"], summary="Modifier restaurant (admin ou gerant affecte)", description="Modification autorisee a l administrateur global ou au gestionnaire deja affecte au restaurant."),
	partial_update=extend_schema(tags=["Restaurants"], summary="Modification partielle restaurant (admin ou gerant affecte)", description="Modification partielle autorisee a l administrateur global ou au gestionnaire deja affecte au restaurant."),
	destroy=extend_schema(tags=["Restaurants"], summary="Supprimer restaurant (admin)"),
)
class RestaurantViewSet(viewsets.ModelViewSet):
	queryset = Restaurant.objects.select_related("gerant").prefetch_related("tables__creneaux_disponibilite").all().order_by("id")
	serializer_class = RestaurantSerializer
	permission_classes = [GestionRestaurantOuAdmin]
	filter_backends = [filters.SearchFilter, filters.OrderingFilter]
	search_fields = ["nom", "adresse"]
	ordering_fields = ["public_id", "nom"]
	lookup_field = "public_id"

	def perform_create(self, serializer):
		if not self.request.user.est_admin_global():
			raise PermissionDenied("Seul un administrateur peut creer un restaurant.")
		serializer.save()

	def perform_destroy(self, instance):
		if not self.request.user.est_admin_global():
			raise PermissionDenied("Seul un administrateur peut supprimer un restaurant.")
		instance.delete()


@extend_schema_view(
	list=extend_schema(
		tags=["Tables"],
		summary="Lister les tables",
		description="Liste paginee des tables avec leurs creneaux de disponibilite. Filtrage possible par restaurant. La gestion est faite par l administrateur ou le gestionnaire du restaurant concerne.",
		parameters=[
			OpenApiParameter("restaurant_public_id", str, OpenApiParameter.QUERY, description="Filtre par identifiant public du restaurant (UUID)."),
			OpenApiParameter("ordering", str, OpenApiParameter.QUERY, description="Tri: public_id, numero, capacite (avec -)."),
			OpenApiParameter("page", int, OpenApiParameter.QUERY, description="Numero de page."),
			OpenApiParameter("taille_page", int, OpenApiParameter.QUERY, description="Taille de page (max 100)."),
		],
	),
	retrieve=extend_schema(tags=["Tables"], summary="Detail table"),
	create=extend_schema(
		tags=["Tables"],
		summary="Creer table (admin ou gerant affecte)",
		description="Permet de creer une table et de definir ses creneaux de disponibilite par jour de semaine ou date specifique.",
	),
	update=extend_schema(
		tags=["Tables"],
		summary="Modifier table (admin ou gerant affecte)",
		description="Remplace les informations de la table et, si fournies, ses disponibilites (jour/date/heure).",
	),
	partial_update=extend_schema(
		tags=["Tables"],
		summary="Modification partielle table (admin ou gerant affecte)",
		description="Met a jour partiellement la table. Si le champ disponibilites est present, la liste des creneaux est remplacee.",
	),
	destroy=extend_schema(tags=["Tables"], summary="Supprimer table (admin ou gerant affecte)"),
)
class TableViewSet(viewsets.ModelViewSet):
	serializer_class = TableSerializer
	permission_classes = [GestionRestaurantOuAdmin]
	filter_backends = [filters.OrderingFilter]
	ordering_fields = ["public_id", "numero", "capacite"]
	lookup_field = "public_id"

	def get_queryset(self):
		queryset = Table.objects.select_related("restaurant").prefetch_related("creneaux_disponibilite").all().order_by("id")
		restaurant_public_id = self.request.query_params.get("restaurant_public_id")
		if restaurant_public_id:
			queryset = queryset.filter(restaurant__public_id=restaurant_public_id)
		return queryset

	def perform_create(self, serializer):
		restaurant = serializer.validated_data["restaurant"]
		if self.request.user.est_admin_global():
			serializer.save()
			return
		if self.request.user.est_gestionnaire_restaurant() and restaurant.gerant_id == self.request.user.id:
			serializer.save()
			return
		raise PermissionDenied("Vous ne pouvez ajouter des tables qu'a votre restaurant.")
