from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from products.models import Product
from shops.utils import get_user_shop
from subscriptions.utils import can_access_advanced_reports

from .models import InventorySession, InventoryItem
from .serializers import InventorySessionSerializer
from .serializers import InventoryItemSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_inventory(request):
    """
    Lance un nouvel inventaire.

    Fonction Pro uniquement.
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Boutique introuvable.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Réservé au pack Pro
    if not can_access_advanced_reports(shop):
        return Response(
            {
                'error': 'L’inventaire est disponible uniquement en pack Pro.'
            },
            status=status.HTTP_403_FORBIDDEN
        )

    products = Product.objects.filter(
        shop=shop,
        is_active=True
    )

    if not products.exists():
        return Response(
            {'error': 'Aucun produit disponible pour inventaire.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    session = InventorySession.objects.create(
        shop=shop,
        user=request.user,
        title=f"Inventaire {timezone.localdate()}"
    )

    for product in products:
        InventoryItem.objects.create(
            session=session,
            product=product,
            system_stock=product.stock_quantity,
            real_stock=product.stock_quantity
        )

    serializer = InventorySessionSerializer(session)

    return Response(
        {
            'message': 'Inventaire lancé avec succès.',
            'inventory': serializer.data
        },
        status=status.HTTP_201_CREATED
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_inventory(request, session_id):
    """
    Valide un inventaire :
    - met à jour les stocks produits
    - ferme la session
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Boutique introuvable.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        session = InventorySession.objects.get(
            id=session_id,
            shop=shop
        )
    except InventorySession.DoesNotExist:
        return Response(
            {'error': 'Session inventaire introuvable.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if session.status == InventorySession.VALIDATED:
        return Response(
            {'error': 'Cet inventaire est déjà validé.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    items = session.items.all()

    for item in items:
        product = item.product

        # mettre à jour stock réel
        product.stock_quantity = item.real_stock
        product.save()

    session.status = InventorySession.VALIDATED
    session.validated_at = timezone.now()
    session.save()

    serializer = InventorySessionSerializer(session)

    return Response({
        'message': 'Inventaire validé avec succès.',
        'inventory': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_list(request):
    """
    Liste les inventaires de la boutique connectée.
    Fonction Pro uniquement.
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Boutique introuvable.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not can_access_advanced_reports(shop):
        return Response(
            {'error': 'L’inventaire est disponible uniquement en pack Pro.'},
            status=status.HTTP_403_FORBIDDEN
        )

    inventories = InventorySession.objects.filter(
        shop=shop
    ).order_by('-created_at')

    serializer = InventorySessionSerializer(inventories, many=True)

    return Response({
        'count': inventories.count(),
        'results': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_detail(request, session_id):
    """
    Détail d’un inventaire avec ses lignes.
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Boutique introuvable.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not can_access_advanced_reports(shop):
        return Response(
            {'error': 'L’inventaire est disponible uniquement en pack Pro.'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        inventory = InventorySession.objects.get(
            id=session_id,
            shop=shop
        )
    except InventorySession.DoesNotExist:
        return Response(
            {'error': 'Inventaire introuvable.'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = InventorySessionSerializer(inventory)

    return Response(serializer.data)



@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_inventory_item(request, item_id):
    """
    Met à jour le stock réel d'une ligne d'inventaire.
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Boutique introuvable.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not can_access_advanced_reports(shop):
        return Response(
            {'error': 'L’inventaire est disponible uniquement en pack Pro.'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        item = InventoryItem.objects.get(
            id=item_id,
            session__shop=shop
        )
    except InventoryItem.DoesNotExist:
        return Response(
            {'error': 'Ligne inventaire introuvable.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # empêcher modification après validation
    if item.session.status == InventorySession.VALIDATED:
        return Response(
            {'error': 'Inventaire déjà validé.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    real_stock = request.data.get('real_stock')

    if real_stock is None:
        return Response(
            {'error': 'Le stock réel est obligatoire.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        real_stock = int(real_stock)
    except ValueError:
        return Response(
            {'error': 'Valeur invalide.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if real_stock < 0:
        return Response(
            {'error': 'Le stock réel ne peut pas être négatif.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    item.real_stock = real_stock
    item.save()

    serializer = InventoryItemSerializer(item)

    return Response({
        'message': 'Stock réel mis à jour.',
        'item': serializer.data
    })