from .models import ShopMember


def get_user_membership(user):
    """
    Retourne l'appartenance active de l'utilisateur à une boutique.
    Pour l'instant, on suppose qu'un utilisateur travaille dans une seule boutique active.
    """
    return ShopMember.objects.filter(
        user=user,
        is_active=True
    ).select_related('shop').first()


def get_user_shop(user):
    """
    Retourne la boutique de l'utilisateur connecté.
    Compatible avec le nouveau système multi-utilisateurs.
    """
    membership = get_user_membership(user)

    if membership:
        return membership.shop

    return None


def get_user_role(user):
    """
    Retourne le rôle de l'utilisateur dans sa boutique.
    """
    membership = get_user_membership(user)

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


def can_create_user(shop):
    """
    Vérifie si la boutique peut ajouter un utilisateur
    selon la limite du plan.
    """
    plan = get_shop_plan(shop)

    if not plan:
        return False, "Votre abonnement est inactif ou expiré."

    current_users_count = shop.members.filter(is_active=True).count()

    if current_users_count >= plan.max_users:
        return False, f"Limite atteinte : votre pack permet maximum {plan.max_users} utilisateur(s)."

    return True, None