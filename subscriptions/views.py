from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from shops.models import Shop
from .models import Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer
from shops.permissions import IsOwner
from shops.utils import get_user_shop



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def plan_list(request):
    """
    Liste les plans disponibles.
    """
    plans = Plan.objects.filter(is_active=True).order_by('monthly_price')
    serializer = PlanSerializer(plans, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_subscription(request):
    """
    Retourne l'abonnement de la boutique liée à l'utilisateur connecté.
    Fonctionne pour owner, manager et seller.
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Vous n’êtes lié à aucune boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        subscription = shop.subscription
    except Subscription.DoesNotExist:
        return Response(
            {'error': 'Aucun abonnement trouvé pour cette boutique.'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = SubscriptionSerializer(subscription)

    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated,IsOwner])
def activate_subscription(request):
    """
    Active ou renouvelle l'abonnement d'une boutique.
    Pour l'instant, on simule l'activation côté backend.
    Plus tard, cette route pourra être liée à un paiement réel.
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    plan_id = request.data.get('plan_id')

    if not plan_id:
        return Response(
            {'error': 'Le plan est obligatoire.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        plan = Plan.objects.get(id=plan_id, is_active=True)
    except Plan.DoesNotExist:
        return Response(
            {'error': 'Plan introuvable ou inactif.'},
            status=status.HTTP_404_NOT_FOUND
        )


    subscription, created = Subscription.objects.get_or_create(
        shop=shop,
        defaults={
            'plan': plan,
            'start_date': timezone.localdate(),
            'end_date':  timezone.localdate(),
            'is_active': False,
            'status': Subscription.INACTIVE,
        }
    )
    subscription.activate(plan=plan, duration_days=30)
    serializer = SubscriptionSerializer(subscription)

    return Response(
        {
            'message': 'Abonnement activé avec succès.',
            'subscription': serializer.data
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated,IsOwner])
def deactivate_subscription(request):
    """
    Désactive l'abonnement de la boutique connectée.
    Utile pour test ou suspension manuelle.
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        subscription = shop.subscription
    except Subscription.DoesNotExist:
        return Response(
            {'error': 'Aucun abonnement trouvé.'},
            status=status.HTTP_404_NOT_FOUND
        )

    subscription.deactivate()

    serializer = SubscriptionSerializer(subscription)

    return Response({
        'message': 'Abonnement désactivé.',
        'subscription': serializer.data
    })