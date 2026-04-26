from django.db import models
from django.contrib.auth.models import User
from shops.models import Shop
from products.models import Product


class Sale(models.Model):
    """
    Représente une vente effectuée dans une boutique.
    """
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='sales'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sales'
    )

    # Total global de la vente
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Remarque facultative
    note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_total_amount(self):
        """
        Recalcule le total de la vente à partir de ses lignes.
        """
        total = sum(item.subtotal for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])

    def __str__(self):
        return f"Vente #{self.id} - {self.shop.name}"


class SaleItem(models.Model):
    """
    Représente une ligne de vente.
    Exemple :
    - Coca 50cl x 2
    - Savon x 1
    """
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='sale_items'
    )

    # Quantité vendue
    quantity = models.PositiveIntegerField()

    # Prix unitaire au moment de la vente
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Sous-total = quantité * prix unitaire
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Avant d'enregistrer la ligne, on calcule le sous-total.
        """
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"