from rest_framework.permissions import BasePermission
from .utils import get_user_membership
from .models import ShopMember,Shop


class IsShopMember(BasePermission):
    """
    Autorise uniquement les utilisateurs membres actifs d'une boutique.
    """

    message = "Vous n'êtes membre d'aucune boutique active."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        membership = get_user_membership(request.user)
        return membership is not None


class IsOwner(BasePermission):
    """
    Réservé au propriétaire de la boutique.
    """

    message = "Action réservée au propriétaire de la boutique."

    def has_permission(self, request, view):
        membership = get_user_membership(request.user)

        if not membership:
            return False

        return membership.role == ShopMember.OWNER


class IsOwnerOrManager(BasePermission):
    def has_permission(self, request, view):

        # propriétaire
        if Shop.objects.filter(user=request.user).exists():
            return True

        # manager
        membership = ShopMember.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        if membership and membership.role == 'manager':
            return True

        return False


class CanSell(BasePermission):
    """
    Autorise owner, manager et seller à vendre.
    """

    message = "Vous n'avez pas le droit d'enregistrer une vente."

    def has_permission(self, request, view):
        membership = get_user_membership(request.user)

        if not membership:
            return False

        return membership.role in [
            ShopMember.OWNER,
            ShopMember.MANAGER,
            ShopMember.SELLER
        ]