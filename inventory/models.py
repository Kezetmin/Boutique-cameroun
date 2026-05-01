from django.db import models
from django.contrib.auth.models import User

from shops.models import Shop
from products.models import Product


class InventorySession(models.Model):
    """
    Représente une opération d'inventaire.
    Exemple : inventaire du 30 avril 2026.
    """

    DRAFT = 'draft'
    VALIDATED = 'validated'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (DRAFT, 'Brouillon'),
        (VALIDATED, 'Validé'),
        (CANCELLED, 'Annulé'),
    ]

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='inventory_sessions'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='inventory_sessions',
        null=True,
        blank=True
    )

    title = models.CharField(max_length=150, default='Inventaire boutique')

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT
    )

    note = models.TextField(blank=True, null=True)

    validated_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.shop.name}"


class InventoryItem(models.Model):
    """
    Ligne d'inventaire pour un produit.
    """

    session = models.ForeignKey(
        InventorySession,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_items'
    )

    # Stock connu par le système au moment de l'inventaire
    system_stock = models.IntegerField(default=0)

    # Stock compté physiquement dans la boutique
    real_stock = models.IntegerField(default=0)

    # Différence = réel - système
    difference = models.IntegerField(default=0)

    note = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.difference = self.real_stock - self.system_stock
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} | Écart : {self.difference}"

# Create your models here.
