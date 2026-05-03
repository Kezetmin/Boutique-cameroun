from django.db import models
from django.utils import timezone
from shops.models import Shop


class Plan(models.Model):
    """
    Représente un pack d'abonnement.
    Exemple : Basic, Pro.
    """

    BASIC = 'basic'
    PRO = 'pro'

    PLAN_CHOICES = [
        (BASIC, 'Basic'),
        (PRO, 'Pro'),
    ]

    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)

    # Prix mensuel en FCFA
    monthly_price = models.PositiveIntegerField(default=0)

    # Description courte du pack
    description = models.TextField(blank=True, null=True)

    # Préparation des limites futures
    max_products = models.PositiveIntegerField(default=50)
    max_users = models.PositiveIntegerField(default=1)

    # Fonctionnalités activables selon le pack
    can_view_advanced_reports = models.BooleanField(default=False)
    can_manage_customer_credits = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.get_name_display()


class Subscription(models.Model):
    """
    Abonnement d'une boutique.
    Permet de savoir si une boutique peut utiliser les fonctionnalités payantes.
    """

    ACTIVE = 'active'
    EXPIRED = 'expired'
    INACTIVE = 'inactive'

    STATUS_CHOICES = [
        (ACTIVE, 'Actif'),
        (EXPIRED, 'Expiré'),
        (INACTIVE, 'Inactif'),
    ]

    shop = models.OneToOneField(
        Shop,
        on_delete=models.CASCADE,
        related_name='subscription'
    )

    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )

    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=ACTIVE
    )

    is_active = models.BooleanField(default=True)
    is_trial = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def has_expired(self):
        return timezone.localdate() > self.end_date

    def refresh_status(self):
        """
        Met à jour le statut selon la date de fin.
        """
        if not self.is_active:
            self.status = self.INACTIVE
        elif self.has_expired():
            self.status = self.EXPIRED
        else:
            self.status = self.ACTIVE

        self.save(update_fields=['status'])
        return self.status

    def is_valid(self):
        """
        L'abonnement est valide seulement s'il est actif
        et que la date de fin n'est pas dépassée.
        """
        return self.is_active and not self.has_expired()

    def activate(self, plan, duration_days=30):
        """
        Active ou réactive un abonnement après paiement.
        """
        today = timezone.localdate()

        self.plan = plan
        self.start_date = today
        self.end_date = today + timezone.timedelta(days=duration_days)
        self.is_active = True
        self.status = self.ACTIVE
        self.save()

    def deactivate(self):
        """
        Désactive manuellement l'abonnement.
        """
        self.is_active = False
        self.status = self.INACTIVE
        self.save(update_fields=['is_active', 'status'])

    def __str__(self):
        return f"{self.shop.name} - {self.plan.get_name_display()} - {self.status}"