from django.db import models
from django.contrib.auth.models import User


class Shop(models.Model):
    """
    Représente une boutique appartenant à un utilisateur.
    Plus tard, tous les produits et ventes seront liés à cette boutique.
    """

    # Nom de la boutique
    name = models.CharField(max_length=150)

    # Nom du propriétaire ou responsable
    owner_name = models.CharField(max_length=150)

    # Numéro de téléphone
    phone = models.CharField(max_length=20, blank=True, null=True)

    # Adresse ou quartier
    address = models.CharField(max_length=255, blank=True, null=True)

    # Relation 1 utilisateur = 1 boutique
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shop')

    # Date de création
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name