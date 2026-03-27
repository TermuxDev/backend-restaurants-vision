from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from utilisateurs.models import Utilisateur
from utilisateurs.permissions import EstAdministrateur
from utilisateurs.serializers import (
	ChangementRoleSerializer,
	ConnexionSerializer,
	InscriptionSerializer,
	UtilisateurSerializer,
)


@extend_schema(
	tags=["Authentification"],
	summary="Inscription client",
	description="Cree un compte client. Le role par defaut est CLIENT et un identifiant public unique (public_id) est attribue automatiquement.",
	request=InscriptionSerializer,
	responses={201: UtilisateurSerializer},
	examples=[
		OpenApiExample(
			"Inscription - requete",
			value={"nom": "Jean Dupont", "email": "utilisateur@example.com", "mot_de_passe": "motdepasse123"},
			request_only=True,
		),
		OpenApiExample(
			"Inscription - reponse",
			value={
				"public_id": "4cb83b87-4d57-4472-a9c8-4f11b0da0dd1",
				"nom": "Jean Dupont",
				"email": "utilisateur@example.com",
				"role": "CLIENT",
				"date_joined": "2026-03-26T10:00:00+01:00",
			},
			response_only=True,
		),
	],
)
class InscriptionAPIView(generics.CreateAPIView):
	queryset = Utilisateur.objects.all()
	permission_classes = [permissions.AllowAny]
	serializer_class = InscriptionSerializer


@extend_schema(
	tags=["Authentification"],
	summary="Connexion JWT",
	description="Authentifie un utilisateur et retourne les tokens JWT access/refresh. Le token inclut les claims nom, role et public_id.",
	request=ConnexionSerializer,
	responses={200: dict},
	examples=[
		OpenApiExample(
			"Connexion - requete",
			value={"email": "jean@exemple.com", "mot_de_passe": "motdepasse123"},
			request_only=True,
		),
		OpenApiExample(
			"Connexion - reponse",
			value={
				"refresh": "<token_refresh>",
				"access": "<token_access>",
			},
			response_only=True,
		),
	],
)
class ConnexionAPIView(TokenObtainPairView):
	permission_classes = [permissions.AllowAny]
	serializer_class = ConnexionSerializer


@extend_schema(
	tags=["Utilisateurs"],
	summary="Consulter profil",
	description="Retourne le profil de l'utilisateur authentifie.",
	responses={200: UtilisateurSerializer},
)
class ProfilAPIView(generics.RetrieveUpdateAPIView):
	serializer_class = UtilisateurSerializer

	def get_object(self):
		return self.request.user


@extend_schema(
	tags=["Utilisateurs"],
	summary="Lister les utilisateurs",
	description="Endpoint reserve a l'administrateur pour consulter les utilisateurs et leurs roles CLIENT, GESTIONNAIRE ou ADMIN.",
	responses={200: UtilisateurSerializer(many=True)},
)
class ListeUtilisateursAPIView(generics.ListAPIView):
	queryset = Utilisateur.objects.all().order_by("public_id")
	serializer_class = UtilisateurSerializer
	permission_classes = [EstAdministrateur]


@extend_schema_view(
	patch=extend_schema(
		tags=["Utilisateurs"],
		summary="Modifier role utilisateur",
		description="Permet a un administrateur d'assigner le role CLIENT, GESTIONNAIRE ou ADMIN via l'identifiant public de l'utilisateur.",
		parameters=[
			OpenApiParameter("public_id", str, OpenApiParameter.PATH, description="UUID public de l'utilisateur cible"),
		],
		request=ChangementRoleSerializer,
		responses={200: UtilisateurSerializer},
		examples=[
			OpenApiExample("Changement role - requete", value={"role": "GESTIONNAIRE"}, request_only=True),
		],
	)
)
class RoleUtilisateurAPIView(generics.UpdateAPIView):
	queryset = Utilisateur.objects.all()
	serializer_class = ChangementRoleSerializer
	permission_classes = [EstAdministrateur]
	lookup_field = "public_id"

	def patch(self, request, *args, **kwargs):
		utilisateur = self.get_object()
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		utilisateur.role = serializer.validated_data["role"]
		utilisateur.save(update_fields=["role"])
		return Response(UtilisateurSerializer(utilisateur).data, status=status.HTTP_200_OK)
