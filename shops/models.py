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
    is_demo = models.BooleanField(default=False)

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
    

from django.db import models
from django.contrib.auth.models import User


class ShopMember(models.Model):
    """
    Représente un utilisateur membre d'une boutique.
    Permet de gérer plusieurs utilisateurs dans une même boutique.
    """

    OWNER = 'owner'
    MANAGER = 'manager'
    SELLER = 'seller'

    ROLE_CHOICES = [
        (OWNER, 'Propriétaire'),
        (MANAGER, 'Gérant'),
        (SELLER, 'Vendeur'),
    ]

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='members'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shop_memberships'
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=SELLER
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['shop', 'user']

    def __str__(self):
        return f"{self.user.username} - {self.shop.name} - {self.role}"

    def is_owner(self):
        return self.role == self.OWNER

    def is_manager(self):
        return self.role == self.MANAGER

    def is_seller(self):
        return self.role == self.SELLER