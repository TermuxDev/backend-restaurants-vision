from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from utilisateurs.models import Role, Utilisateur


class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ["public_id", "nom", "email", "role", "date_joined"]
        read_only_fields = ["public_id", "date_joined"]


class InscriptionSerializer(serializers.ModelSerializer):
    mot_de_passe = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Utilisateur
        fields = ["nom", "email", "mot_de_passe"]

    def create(self, validated_data):
        mot_de_passe = validated_data.pop("mot_de_passe")
        return Utilisateur.objects.create_user(password=mot_de_passe, role=Role.CLIENT, **validated_data)


class ConnexionSerializer(TokenObtainPairSerializer):
    username_field = Utilisateur.USERNAME_FIELD

    mot_de_passe = serializers.CharField(write_only=True, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Evite la confusion cote client: l'API ne doit exposer que mot_de_passe.
        self.fields.pop("password", None)

    def validate(self, attrs):
        attrs["password"] = attrs.pop("mot_de_passe")
        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["public_id"] = str(user.public_id)
        token["nom"] = user.nom
        token["role"] = user.role
        return token


class ChangementRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=Role.choices)
