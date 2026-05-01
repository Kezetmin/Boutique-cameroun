from django.db import models
from shops.models import Shop


class Customer(models.Model):
    """
    Représente un client d'une boutique.
    Utile surtout pour les ventes à crédit ou paiements partiels.
    """

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='customers'
    )

    name = models.CharField(max_length=150)

    phone = models.CharField(max_length=30, blank=True, null=True)

    address = models.CharField(max_length=255, blank=True, null=True)

    note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name