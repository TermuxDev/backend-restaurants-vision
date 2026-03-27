import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models


class Role(models.TextChoices):
	CLIENT = "CLIENT", "Client"
	ADMIN = "ADMIN", "Administrateur"
	GESTIONNAIRE = "GESTIONNAIRE", "Gestionnaire restaurant"


class GestionnaireUtilisateur(BaseUserManager):
	def create_user(self, email, nom, password=None, **extra_fields):
		if not email:
			raise ValueError("L'email est obligatoire.")

		email = self.normalize_email(email)
		utilisateur = self.model(email=email, nom=nom, **extra_fields)
		utilisateur.set_password(password)
		utilisateur.save(using=self._db)
		return utilisateur

	def create_superuser(self, email, nom, password=None, **extra_fields):
		extra_fields.setdefault("is_staff", True)
		extra_fields.setdefault("is_superuser", True)
		extra_fields.setdefault("role", Role.ADMIN)

		if extra_fields.get("is_staff") is not True:
			raise ValueError("Le superutilisateur doit avoir is_staff=True.")
		if extra_fields.get("is_superuser") is not True:
			raise ValueError("Le superutilisateur doit avoir is_superuser=True.")

		return self.create_user(email, nom, password, **extra_fields)


class Utilisateur(AbstractBaseUser, PermissionsMixin):
	id = models.BigAutoField(primary_key=True)
	public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
	nom = models.CharField(max_length=120)
	email = models.EmailField(unique=True)
	role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)
	date_joined = models.DateTimeField(auto_now_add=True)

	objects = GestionnaireUtilisateur()

	USERNAME_FIELD = "email"
	REQUIRED_FIELDS = ["nom"]

	class Meta:
		verbose_name = "Utilisateur"
		verbose_name_plural = "Utilisateurs"

	def __str__(self):
		return f"{self.nom} <{self.email}>"

	def est_admin_global(self):
		return self.role == Role.ADMIN or self.is_superuser

	def est_gestionnaire_restaurant(self):
		return self.role == Role.GESTIONNAIRE
