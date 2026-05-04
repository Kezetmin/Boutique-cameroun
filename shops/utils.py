from subscriptions.utils import get_shop_plan
from .models import Shop, ShopMember
from subscriptions.utils import get_shop_plan


def get_user_shop(user):
    """
    Retourne la boutique liée à l'utilisateur connecté.
    Fonctionne pour owner et employés.
    """
    try:
        return user.shop
    except Shop.DoesNotExist:
        pass

    member = ShopMember.objects.filter(
        user=user,
        is_active=True
    ).select_related('shop').first()

    if member:
        return member.shop

    return None


def can_create_user(shop):
    """
    Vérifie si la boutique peut encore créer
    de nouveaux utilisateurs selon son pack.
    """

    plan = get_shop_plan(shop)

    if not plan:
        return False, "Votre abonnement est inactif ou expiré."

    current_members_count = ShopMember.objects.filter(
        shop=shop,
        is_active=True
    ).count()

    if current_members_count >= plan.max_users:
        return (
            False,
            f"Votre pack permet maximum {plan.max_users} utilisateur(s)."
        )

    return True, None


def get_user_membership(user):
    """
    Retourne l'appartenance active de l'utilisateur à une boutique.
    Pour l'instant, on suppose qu'un utilisateur travaille dans une seule boutique active.
    """
    return ShopMember.objects.filter(
        user=user,
        is_active=True
    ).select_related('shop').first()


def get_user_role(user):
    """
    Retourne le rôle réel de l'utilisateur :
    owner / manager / seller
    """

    # propriétaire de boutique
    if Shop.objects.filter(user=user).exists():
        return 'owner'

    # employés
    membership = ShopMember.objects.filter(
        user=user,
        is_active=True
    ).first()

    if membership:
        return membership.role

    return None


def user_is_owner(user):
    return get_user_role(user) == ShopMember.OWNER


def user_is_manager(user):
    return get_user_role(user) == ShopMember.MANAGER


def user_is_seller(user):
    return get_user_role(user) == ShopMember.SELLER


def user_is_owner_or_manager(user):
    role = get_user_role(user)
    return role in [ShopMember.OWNER, ShopMember.MANAGER]


