import os
from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-a-changer-en-prod")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'drf_spectacular',
    'rest_framework_simplejwt.token_blacklist',
    'utilisateurs',
    'restaurants',
    'reservations',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

if os.getenv("MYSQL_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("MYSQL_DB", "restaurants_db"),
            "USER": os.getenv("MYSQL_USER", "root"),
            "PASSWORD": os.getenv("MYSQL_PASSWORD", ""),
            "HOST": os.getenv("MYSQL_HOST", "127.0.0.1"),
            "PORT": os.getenv("MYSQL_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Africa/Abidjan'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

AUTH_USER_MODEL = 'utilisateurs.Utilisateur'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'config.pagination.PaginationStandard',
    'PAGE_SIZE': 10,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'config.exception_handler.gestionnaire_exceptions_api',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=45),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}

PROJECT_PORTFOLIO_URL = os.getenv(
    "PROJECT_PORTFOLIO_URL",
    "https://emploirapide.net/talent-market/talents/diomande-keuwe-mickael",
)
PROJECT_DOCUMENTATION_URL = os.getenv("PROJECT_DOCUMENTATION_URL", "")

spectacular_description_lines = [
    "Je vous presente la documentation SWAGGER de mon projet de gestion de reservations de restaurants. Cette API RESTful a ete developpée en utilisant Django REST Framework et couvre pour la gestion des utilisateurs, des restaurants, des tables et des reservations.",
    "",
    "Cette API couvre l'essentiel :",
    "- authentification JWT et gestion des profils,",
    "- gestion des restaurants et de leurs tables,",
    "- definition des disponibilites par jour, date et heure,",
    "- verification des creneaux disponibles,",
    "- creation, suivi et traitement des reservations.",
    "",
    "Roles principaux : CLIENT, GESTIONNAIRE et ADMIN.",
]

if PROJECT_PORTFOLIO_URL:
    spectacular_description_lines.extend([
        "",
        f"Profil Emploi rapide : [Consulter mon profil ]({PROJECT_PORTFOLIO_URL})",
    ])

if PROJECT_DOCUMENTATION_URL:
    spectacular_description_lines.append(
        f"Documentation complete : [Telecharger la documentation]({PROJECT_DOCUMENTATION_URL})"
    )

SPECTACULAR_SETTINGS = {
    'TITLE': 'API REST - Gestion de reservations de restaurants',
    'DESCRIPTION': "\n".join(spectacular_description_lines),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {
        'name': 'Diomande Keuwe Mickael as TermuxDev',
        'email': 'keuwemichael@gmail.com',
        'url': PROJECT_PORTFOLIO_URL,
    },
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
    },
    'TAGS': [
        {'name': 'Authentification', 'description': 'Inscription, connexion JWT et gestion de session'},
        {'name': 'Utilisateurs', 'description': 'Profils, roles CLIENT/GESTIONNAIRE/ADMIN et administration'},
        {'name': 'Restaurants', 'description': 'Gestion des restaurants et affectation d un gestionnaire'},
        {'name': 'Tables', 'description': 'Gestion des tables et capacites par restaurant'},
        {'name': 'Reservations', 'description': 'Creation, modification, annulation, confirmation et refus'},
        {'name': 'Disponibilites', 'description': 'Moteur de verification des creneaux'},
    ],
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
]
CORS_ALLOW_CREDENTIALS = True
