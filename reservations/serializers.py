from django.db import transaction
from rest_framework import serializers

from reservations.models import Reservation, StatutReservation
from reservations.services import (
    valider_table_disponible_sur_creneau,
    valider_coherence_table_restaurant,
    valider_creneau_libre,
    verifier_restaurant_ouvert,
)
from restaurants.models import Restaurant, Table


class DisponibiliteSerializer(serializers.Serializer):
    restaurant_public_id = serializers.UUIDField()
    date = serializers.DateField()
    heure = serializers.TimeField()
    nb_personnes = serializers.IntegerField(min_value=1)


class TableDisponibleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ["public_id", "numero", "capacite", "est_disponible"]


class ReservationSerializer(serializers.ModelSerializer):
    client_public_id = serializers.UUIDField(source="client.public_id", read_only=True)
    client_nom = serializers.CharField(source="client.nom", read_only=True)
    client_email = serializers.CharField(source="client.email", read_only=True)
    restaurant_public_id = serializers.UUIDField(source="restaurant.public_id", read_only=True)
    restaurant_nom = serializers.CharField(source="restaurant.nom", read_only=True)
    restaurant_gerant_nom = serializers.CharField(source="restaurant.gerant.nom", read_only=True)
    table_public_id = serializers.UUIDField(source="table.public_id", read_only=True)
    table_numero = serializers.IntegerField(source="table.numero", read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "public_id",
            "client_public_id",
            "client_nom",
            "client_email",
            "restaurant_public_id",
            "restaurant_nom",
            "restaurant_gerant_nom",
            "table_public_id",
            "table_numero",
            "date",
            "heure",
            "nb_personnes",
            "statut",
            "cree_le",
            "modifie_le",
        ]
        read_only_fields = [
            "public_id",
            "client_public_id",
            "restaurant_public_id",
            "table_public_id",
            "statut",
            "cree_le",
            "modifie_le",
        ]


class CreationReservationSerializer(serializers.Serializer):
    restaurant_public_id = serializers.UUIDField()
    table_public_id = serializers.UUIDField()
    date = serializers.DateField()
    heure = serializers.TimeField()
    nb_personnes = serializers.IntegerField(min_value=1)

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        try:
            restaurant = Restaurant.objects.select_for_update().get(public_id=validated_data["restaurant_public_id"])
        except Restaurant.DoesNotExist as exc:
            raise serializers.ValidationError({"restaurant_public_id": "Restaurant introuvable."}) from exc

        try:
            table = Table.objects.select_for_update().get(public_id=validated_data["table_public_id"])
        except Table.DoesNotExist as exc:
            raise serializers.ValidationError({"table_public_id": "Table introuvable."}) from exc

        valider_coherence_table_restaurant(table, restaurant)
        verifier_restaurant_ouvert(restaurant, validated_data["heure"])

        if table.capacite < validated_data["nb_personnes"]:
            raise serializers.ValidationError({"nb_personnes": "Capacite de table insuffisante."})

        if not table.est_disponible:
            raise serializers.ValidationError({"table": "Table temporairement indisponible."})

        valider_table_disponible_sur_creneau(
            table=table,
            date=validated_data["date"],
            heure=validated_data["heure"],
        )

        valider_creneau_libre(
            restaurant=restaurant,
            table=table,
            date=validated_data["date"],
            heure=validated_data["heure"],
        )

        return Reservation.objects.create(
            client=user,
            restaurant=restaurant,
            table=table,
            date=validated_data["date"],
            heure=validated_data["heure"],
            nb_personnes=validated_data["nb_personnes"],
            statut=StatutReservation.EN_ATTENTE,
        )


class ModificationReservationSerializer(serializers.Serializer):
    table_public_id = serializers.UUIDField(required=False)
    date = serializers.DateField(required=False)
    heure = serializers.TimeField(required=False)
    nb_personnes = serializers.IntegerField(min_value=1, required=False)

    @transaction.atomic
    def update(self, instance, validated_data):
        if instance.statut not in [StatutReservation.EN_ATTENTE, StatutReservation.CONFIRMEE]:
            raise serializers.ValidationError({"statut": "Seules les reservations en attente ou confirmees peuvent etre modifiees."})

        table = instance.table
        if "table_public_id" in validated_data:
            try:
                table = Table.objects.select_for_update().get(public_id=validated_data["table_public_id"])
            except Table.DoesNotExist as exc:
                raise serializers.ValidationError({"table_public_id": "Table introuvable."}) from exc
            valider_coherence_table_restaurant(table, instance.restaurant)

        date = validated_data.get("date", instance.date)
        heure = validated_data.get("heure", instance.heure)
        nb_personnes = validated_data.get("nb_personnes", instance.nb_personnes)

        verifier_restaurant_ouvert(instance.restaurant, heure)

        if table.capacite < nb_personnes:
            raise serializers.ValidationError({"nb_personnes": "Capacite de table insuffisante."})

        if not table.est_disponible:
            raise serializers.ValidationError({"table": "Table temporairement indisponible."})

        valider_table_disponible_sur_creneau(
            table=table,
            date=date,
            heure=heure,
        )

        valider_creneau_libre(
            restaurant=instance.restaurant,
            table=table,
            date=date,
            heure=heure,
            reservation_id=instance.id,
        )

        instance.table = table
        instance.date = date
        instance.heure = heure
        instance.nb_personnes = nb_personnes
        instance.save(update_fields=["table", "date", "heure", "nb_personnes", "modifie_le"])
        return instance
