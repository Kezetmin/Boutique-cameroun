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
    Autorise uniquement le propriétaire réel de la boutique.
    """

    def has_permission(self, request, view):
        # propriétaire principal
        if Shop.objects.filter(user=request.user).exists():
            return True

        return False

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

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # 1. Le propriétaire réel de la boutique peut vendre
        if Shop.objects.filter(user=user).exists():
            return True

        # 2. Les employés actifs peuvent vendre
        membership = ShopMember.objects.filter(
            user=user,
            is_active=True
        ).first()

        if membership and membership.role in [
            ShopMember.MANAGER,
            ShopMember.SELLER,
        ]:
            return True

        return False