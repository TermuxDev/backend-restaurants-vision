from rest_framework import serializers

from restaurants.models import Restaurant, Table, TableDisponibilite
from utilisateurs.models import Role, Utilisateur


class TableDisponibiliteSerializer(serializers.ModelSerializer):
    jour_semaine_libelle = serializers.CharField(source="get_jour_semaine_display", read_only=True)

    class Meta:
        model = TableDisponibilite
        fields = [
            "public_id",
            "jour_semaine",
            "jour_semaine_libelle",
            "date_specifique",
            "heure_debut",
            "heure_fin",
            "actif",
        ]
        read_only_fields = ["public_id", "jour_semaine_libelle"]

    def validate(self, attrs):
        jour = attrs.get("jour_semaine")
        date_specifique = attrs.get("date_specifique")

        if (jour is None and date_specifique is None) or (jour is not None and date_specifique is not None):
            raise serializers.ValidationError(
                "Renseignez soit 'jour_semaine', soit 'date_specifique' (un seul des deux)."
            )

        heure_debut = attrs.get("heure_debut")
        heure_fin = attrs.get("heure_fin")
        if heure_debut and heure_fin and heure_debut >= heure_fin:
            raise serializers.ValidationError({"heure_fin": "L'heure de fin doit etre strictement apres l'heure de debut."})

        return attrs


class TableProfilSerializer(serializers.ModelSerializer):
    disponibilites = TableDisponibiliteSerializer(source="creneaux_disponibilite", many=True, read_only=True)

    class Meta:
        model = Table
        fields = ["public_id", "numero", "capacite", "est_disponible", "disponibilites"]


class RestaurantSerializer(serializers.ModelSerializer):
    gerant = serializers.SlugRelatedField(
        slug_field="public_id",
        queryset=Utilisateur.objects.all(),
        allow_null=True,
        required=False,
    )
    gerant_nom = serializers.CharField(source="gerant.nom", read_only=True)
    gerant_email = serializers.CharField(source="gerant.email", read_only=True)
    tables = TableProfilSerializer(many=True, read_only=True)

    class Meta:
        model = Restaurant
        fields = [
            "public_id",
            "nom",
            "adresse",
            "telephone",
            "gerant",
            "gerant_nom",
            "gerant_email",
            "heure_ouverture",
            "heure_fermeture",
            "actif",
            "tables",
        ]
        read_only_fields = ["public_id"]

    def validate_gerant(self, value):
        if value is None:
            return value
        if value.role not in [Role.GESTIONNAIRE, Role.ADMIN] and not value.is_superuser:
            raise serializers.ValidationError("Le gerant doit avoir le role GESTIONNAIRE ou ADMIN.")
        return value


class TableSerializer(serializers.ModelSerializer):
    restaurant = serializers.SlugRelatedField(slug_field="public_id", queryset=Restaurant.objects.all())
    restaurant_nom = serializers.CharField(source="restaurant.nom", read_only=True)
    restaurant_public_id = serializers.UUIDField(source="restaurant.public_id", read_only=True)
    disponibilites = TableDisponibiliteSerializer(source="creneaux_disponibilite", many=True, required=False)

    class Meta:
        model = Table
        fields = [
            "public_id",
            "restaurant",
            "restaurant_public_id",
            "restaurant_nom",
            "numero",
            "capacite",
            "est_disponible",
            "disponibilites",
        ]
        read_only_fields = ["public_id", "restaurant_public_id", "restaurant_nom"]

    def create(self, validated_data):
        disponibilites_data = validated_data.pop("creneaux_disponibilite", [])
        table = Table.objects.create(**validated_data)
        for disponibilite in disponibilites_data:
            TableDisponibilite.objects.create(table=table, **disponibilite)
        return table

    def update(self, instance, validated_data):
        disponibilites_data = validated_data.pop("creneaux_disponibilite", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if disponibilites_data is not None:
            instance.creneaux_disponibilite.all().delete()
            for disponibilite in disponibilites_data:
                TableDisponibilite.objects.create(table=instance, **disponibilite)

        return instance
