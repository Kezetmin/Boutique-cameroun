from .models import Subscription


def get_shop_subscription(shop):
    """
    Retourne l'abonnement de la boutique.
    Si aucun abonnement n'existe, retourne None.
    """
    try:
        return shop.subscription
    except Subscription.DoesNotExist:
        return None


def has_valid_subscription(shop):
    """
    Vérifie si la boutique a un abonnement actif et non expiré.
    """
    subscription = get_shop_subscription(shop)

    if not subscription:
        return False

    return subscription.is_valid()


def get_shop_plan(shop):
    """
    Retourne le plan de la boutique si l'abonnement est valide.
    """
    subscription = get_shop_subscription(shop)

    if not subscription or not subscription.is_valid():
        return None

    return subscription.plan


def can_create_product(shop):
    """
    Vérifie si la boutique peut encore créer un produit
    selon la limite de son pack.
    """
    plan = get_shop_plan(shop)

    if not plan:
        return False, "Votre abonnement est inactif ou expiré."

    current_products_count = shop.products.filter(is_active=True).count()

    if current_products_count >= plan.max_products:
        return False, f"Limite atteinte : votre pack permet maximum {plan.max_products} produits."

    return True, None


def can_access_advanced_reports(shop):
    """
    Vérifie si la boutique peut accéder aux rapports avancés.
    """
    plan = get_shop_plan(shop)

    if not plan:
        return False

    return plan.can_view_advanced_reports


def can_manage_customer_credits(shop):
    """
    Vérifie si la boutique peut gérer les crédits clients.
    """
    plan = get_shop_plan(shop)

    if not plan:
        return False

    return plan.can_manage_customer_credits