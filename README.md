# Backend 

API REST de gestion de reservations de restaurants.

Vous trouverez dans le dossier fiches-systeme-information/ , il contient les fiches de l'etude du système d'information. (J'ai tenu à l'intégré au cas où vous aurz des imcomprehension dans mon système.)

Ce projet couvre :
- authentification JWT et gestion des profils,
- gestion des restaurants et de leurs tables,
- definition des disponibilites par jour, date et heure,
- verification des creneaux disponibles,
- creation, suivi et traitement des reservations.

Roles principaux : `CLIENT`, `GESTIONNAIRE` et `ADMIN`.

## Stack

- Django 4.2
- Django REST Framework
- SimpleJWT
- drf-spectacular

## Demarrage du projet

1. Creer et activer un environnement virtuel si necessaire.

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Installer les dependances.

```bash
pip install -r requirements.txt
```

4. Completer si besoin les variables principales dans `.env`.

```env
DJANGO_SECRET_KEY=prenez-un-mdp-plus-robuste-pour-le-deployement
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=*
MYSQL_DB=
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_HOST=127.0.0.1
MYSQL_PORT=
```

5. Appliquer les migrations.

```bash
python manage.py migrate
```

6. Lancer le serveur de developpement.

```bash
python manage.py runserver
```

7. Ouvrir la documentation.

```text
https://backend-restaurants-vision.onrender.com/api/docs/
```


## Regles d'acces

- Lecture publique sur les restaurants, tables et disponibilites.
- Creation des restaurants reservee aux administrateurs.
- Chaque restaurant ne peut configurer que ses propres tables via son gestionnaire affecte.
- Le numero de table est un numero metier defini par le restaurant, distinct de l'identifiant interne en base.
- Les echanges API utilisent des `public_id` et non les IDs internes de base de donnees.
- Seul un utilisateur `CLIENT` peut creer une reservation.

## TermuxDev