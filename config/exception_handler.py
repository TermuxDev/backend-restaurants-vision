from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


MESSAGES_STATUTS = {
    status.HTTP_400_BAD_REQUEST: "Requete invalide.",
    status.HTTP_401_UNAUTHORIZED: "Authentification requise ou invalide.",
    status.HTTP_403_FORBIDDEN: "Acces refuse.",
    status.HTTP_404_NOT_FOUND: "Ressource introuvable.",
    status.HTTP_409_CONFLICT: "Conflit de donnees.",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "Donnees non conformes.",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "Erreur interne du serveur.",
}


def gestionnaire_exceptions_api(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return Response(
            {
                "code": "erreur_interne",
                "message": MESSAGES_STATUTS[status.HTTP_500_INTERNAL_SERVER_ERROR],
                "details": [str(exc)],
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    details = response.data
    if isinstance(details, dict):
        details_payload = details
    else:
        details_payload = {"erreurs": details}

    return Response(
        {
            "code": f"http_{response.status_code}",
            "message": MESSAGES_STATUTS.get(response.status_code, "Erreur API."),
            "details": details_payload,
        },
        status=response.status_code,
    )
