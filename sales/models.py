from time import timezone

from django.utils import timezone as dj_timezone

from django.db import models
from django.contrib.auth.models import User
from customers.models import Customer
from shops.models import Shop
from products.models import Product
import uuid


class Sale(models.Model):
    VALIDATED = 'validated'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (VALIDATED, 'Validée'),
        (CANCELLED, 'Annulée'),
    ]

    PAID = 'paid'
    PARTIAL = 'partial'
    UNPAID = 'unpaid'

    PAYMENT_STATUS_CHOICES = [
        (PAID, 'Payé'),
        (PARTIAL, 'Partiel'),
        (UNPAID, 'Impayé'),
    ]

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='sales')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales')
    receipt_number = models.CharField(
    max_length=50,
    unique=True,
    blank=True,
    null=True
)

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        related_name='sales',
        blank=True,
        null=True
    )

    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=UNPAID
    )

    note = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=VALIDATED
    )

    cancel_reason = models.TextField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Génère automatiquement un numéro de reçu unique.
        Exemple : RC-AB12CD34
        """
        if not self.receipt_number:
            self.receipt_number = f"RC-{uuid.uuid4().hex[:8].upper()}"

        super().save(*args, **kwargs)    

    def update_total_amount(self):
        """
        Recalcule le total de la vente à partir de ses lignes.
        """
        total = sum(item.subtotal for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])

    def __str__(self):
        return f"Vente #{self.id} - {self.shop.name}"
    
    def cancel(self, reason=None):
        """
        Annule la vente et remet les quantités vendues dans le stock.
        """
        if self.status == self.CANCELLED:
            return False

        for item in self.items.all():
            item.product.increase_stock(item.quantity)

        self.status = self.CANCELLED
        self.cancel_reason = reason
        self.cancelled_at = dj_timezone.now()
        self.save(update_fields=['status', 'cancel_reason', 'cancelled_at'])

        return True   
     
    def update_payment_status(self):
        """
        Met à jour le reste à payer et le statut de paiement.
        """
        self.remaining_amount = self.total_amount - self.amount_paid

        if self.amount_paid <= 0:
            self.payment_status = self.UNPAID
        elif self.amount_paid < self.total_amount:
            self.payment_status = self.PARTIAL
        else:
            self.payment_status = self.PAID
            self.remaining_amount = 0

        self.save(update_fields=[
            'amount_paid',
            'remaining_amount',
            'payment_status'
        ])
    def add_payment(self, amount):
        """
        Ajoute un paiement à la vente.
        """
        self.amount_paid += amount
        self.update_payment_status()

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
    


class SalePayment(models.Model):
    """
    Historique des paiements d'une vente.
    Une vente peut être payée en plusieurs fois.
    """

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='sale_payments'
    )

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        related_name='payments',
        blank=True,
        null=True
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='sale_payments',
        blank=True,
        null=True
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement {self.amount} FCFA - Vente #{self.sale.id}"