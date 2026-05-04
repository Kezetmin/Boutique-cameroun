from django.db import models
from shops.models import Shop
from django.contrib.auth.models import User


class Category(models.Model):
    """
    Représente une catégorie de produits pour une boutique.
    Exemple : Boissons, Riz, Savons, etc.
    """

    # Nom de la catégorie
    name = models.CharField(max_length=100)

    # Petite description facultative
    description = models.TextField(blank=True, null=True)

    # Chaque catégorie appartient à une boutique
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='categories'
    )

    # Dates utiles
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Empêche deux catégories du même nom dans la même boutique
        unique_together = ['name', 'shop']

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Représente un produit appartenant à une boutique.
    Tous les produits seront liés à une boutique précise.
    """

    # Nom du produit
    name = models.CharField(max_length=150)

    # Petite description facultative
    description = models.TextField(blank=True, null=True)

    # Prix d'achat du produit
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Prix de vente du produit
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Quantité disponible en stock
    stock_quantity = models.PositiveIntegerField(default=0)

    # Seuil minimum pour signaler un stock faible
    low_stock_threshold = models.PositiveIntegerField(default=5)

    # Produit actif ou non
    is_active = models.BooleanField(default=True)

    # Catégorie du produit
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    # Boutique à laquelle appartient le produit
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='products'
    )

    # Dates utiles
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_low_stock(self):
        """
        Retourne True si le stock est inférieur ou égal au seuil d'alerte.
        """
        return self.stock_quantity <= self.low_stock_threshold

    def __str__(self):
        return self.name

    def reduce_stock(self, quantity):
        """
        Réduit le stock du produit après une vente.
        """
        self.stock_quantity -= quantity
        self.save(update_fields=['stock_quantity'])

    def increase_stock(self, quantity):
        """
        Méthode utile plus tard si on annule une vente
        ou si on veut remettre du stock.
        """
        self.stock_quantity += quantity
        self.save(update_fields=['stock_quantity'])

    def has_enough_stock(self, quantity):
        """
        Vérifie si le stock disponible est suffisant
        pour la quantité demandée.
        """
        return self.stock_quantity >= quantity  


class StockMovement(models.Model):
    """
    Historique des mouvements de stock.
    Exemple :
    - entrée fournisseur
    - correction de stock
    - retour produit
    """

    IN = 'in'
    OUT = 'out'
    ADJUSTMENT = 'adjustment'

    MOVEMENT_TYPES = [
        (IN, 'Entrée de stock'),
        (OUT, 'Sortie de stock'),
        (ADJUSTMENT, 'Correction de stock'),
    ]

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='stock_movements'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_movements'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements'
    )

    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES,
        default=IN
    )
    supplier = models.CharField(max_length=150,blank=True,null=True)

    quantity = models.PositiveIntegerField()

    note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} - {self.get_movement_type_display()}"  