from datetime import datetime

from django.db.models import Q
from rest_framework.exceptions import ValidationError

from reservations.models import Reservation, StatutReservation


def verifier_restaurant_ouvert(restaurant, heure):
    if not (restaurant.heure_ouverture <= heure <= restaurant.heure_fermeture):
        raise ValidationError({"heure": "Le restaurant est ferme a ce creneau."})


def tables_disponibles(restaurant, date, heure, nb_personnes):
    reservations_occupees = Reservation.objects.filter(
        restaurant=restaurant,
        date=date,
        heure=heure,
        statut__in=[StatutReservation.EN_ATTENTE, StatutReservation.CONFIRMEE],
    ).values_list("table_id", flat=True)

    filtre_creneaux = (
        Q(
            creneaux_disponibilite__actif=True,
            creneaux_disponibilite__date_specifique=date,
            creneaux_disponibilite__heure_debut__lte=heure,
            creneaux_disponibilite__heure_fin__gte=heure,
        )
        | Q(
            creneaux_disponibilite__actif=True,
            creneaux_disponibilite__date_specifique__isnull=True,
            creneaux_disponibilite__jour_semaine=date.weekday(),
            creneaux_disponibilite__heure_debut__lte=heure,
            creneaux_disponibilite__heure_fin__gte=heure,
        )
    )

    return restaurant.tables.filter(
        est_disponible=True,
        capacite__gte=nb_personnes,
    ).filter(filtre_creneaux).exclude(id__in=reservations_occupees).distinct().order_by("numero")


def valider_table_disponible_sur_creneau(table, date, heure):
    existe_creneau = table.creneaux_disponibilite.filter(
        actif=True,
        heure_debut__lte=heure,
        heure_fin__gte=heure,
    ).filter(
        Q(date_specifique=date)
        | Q(date_specifique__isnull=True, jour_semaine=date.weekday())
    ).exists()

    if not existe_creneau:
        raise ValidationError({
            "table": "Cette table n'est pas disponible sur le jour/date et l'heure demandes."
        })


def valider_coherence_table_restaurant(table, restaurant):
    if table.restaurant_id != restaurant.id:
        raise ValidationError({"table": "La table ne correspond pas au restaurant."})


def valider_creneau_libre(restaurant, table, date, heure, reservation_id=None):
    conflit = Reservation.objects.filter(
        restaurant=restaurant,
        table=table,
        date=date,
        heure=heure,
        statut__in=[StatutReservation.EN_ATTENTE, StatutReservation.CONFIRMEE],
    )
    if reservation_id:
        conflit = conflit.exclude(id=reservation_id)
    if conflit.exists():
        raise ValidationError({"creneau": "Cette table est deja reservee pour ce creneau."})


def filtrer_reservations(queryset, params):
    statut = params.get("statut")
    date = params.get("date")
    restaurant_public_id = params.get("restaurant_public_id")
    email_client = params.get("email_client")

    if statut:
        queryset = queryset.filter(statut=statut)
    if date:
        queryset = queryset.filter(date=date)
    if restaurant_public_id:
        queryset = queryset.filter(restaurant__public_id=restaurant_public_id)
    if email_client:
        queryset = queryset.filter(client__email__icontains=email_client)

    return queryset


def marquer_reservations_terminees():
    maintenant = datetime.now()
    reservations_passees = Q(date__lt=maintenant.date()) | (Q(date=maintenant.date()) & Q(heure__lt=maintenant.time()))

    Reservation.objects.filter(
        reservations_passees,
        statut=StatutReservation.CONFIRMEE,
    ).update(statut=StatutReservation.TERMINEE)
