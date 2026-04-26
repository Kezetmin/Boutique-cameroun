from rest_framework.permissions import BasePermission
from .utils import has_valid_subscription, can_access_advanced_reports
from .utils import can_manage_customer_credits


class HasValidSubscription(BasePermission):
    """
    Bloque l'accès si la boutique n'a pas d'abonnement actif.
    """

    message = "Votre abonnement est inactif ou expiré."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if not hasattr(user, 'shop'):
            self.message = "Vous devez d’abord créer une boutique."
            return False

        subscription = getattr(user.shop, 'subscription', None)

        if not subscription:
            self.message = "Aucun abonnement trouvé pour votre boutique."
            return False

        subscription.refresh_status()

        if not subscription.is_valid():
            self.message = "Votre abonnement est expiré ou inactif. Veuillez renouveler votre abonnement."
            return False

        return True


class CanAccessAdvancedReports(BasePermission):
    """
    Permission pour les routes réservées aux packs avec rapports avancés.
    Exemple : Pro uniquement.
    """

    message = "Cette fonctionnalité est réservée au pack Pro."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if not hasattr(user, 'shop'):
            self.message = "Vous devez d’abord créer une boutique."
            return False

        return can_access_advanced_reports(user.shop)



class CanManageCustomerCredits(BasePermission):
    """
    Permission pour la gestion des crédits clients.
    Exemple : fonctionnalité réservée au pack Pro.
    """

    message = "La gestion des crédits clients est réservée au pack Pro."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if not hasattr(user, 'shop'):
            self.message = "Vous devez d’abord créer une boutique."
            return False

        return can_manage_customer_credits(user.shop)