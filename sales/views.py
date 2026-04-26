from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Sale, SaleItem
from .serializers import SaleSerializer, SaleCreateSerializer
from shops.models import Shop
from products.models import Product


def get_user_shop(user):
    """
    Retourne la boutique de l'utilisateur connecté.
    """
    try:
        return user.shop
    except Shop.DoesNotExist:
        return None


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def sale_list_create(request):
    """
    GET  -> liste les ventes de la boutique connectée
    POST -> crée une vente avec ses lignes si le stock est suffisant
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if request.method == 'GET':
        sales = Sale.objects.filter(shop=shop).order_by('-created_at')
        serializer = SaleSerializer(sales, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = SaleCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        items_data = serializer.validated_data.get('items', [])
        note = serializer.validated_data.get('note', '')

        # Vérification complète du stock avant création
        validated_items = []
        requested_quantities = {}

        for item_data in items_data:
            product_id = item_data.get('product')
            quantity = item_data.get('quantity')

            if not product_id:
                return Response(
                    {'error': 'Chaque ligne doit contenir un produit.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not quantity or int(quantity) <= 0:
                return Response(
                    {'error': 'Chaque quantité doit être supérieure à 0.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            quantity = int(quantity)

            try:
                product = Product.objects.get(
                    id=product_id,
                    shop=shop,
                    is_active=True
                )
            except Product.DoesNotExist:
                return Response(
                    {'error': f'Produit introuvable ou non autorisé : {product_id}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if product.id not in requested_quantities:
                requested_quantities[product.id] = {
                    'product': product,
                    'quantity': 0
                }

            requested_quantities[product.id]['quantity'] += quantity

            validated_items.append({
                'product': product,
                'quantity': quantity
            })

        # Vérification finale cumulée du stock
        for item in requested_quantities.values():
            product = item['product']
            total_quantity_requested = item['quantity']

            if not product.has_enough_stock(total_quantity_requested):
                return Response(
                    {
                        'error': f'Stock insuffisant pour le produit "{product.name}".',
                        'product_id': product.id,
                        'product_name': product.name,
                        'stock_available': product.stock_quantity,
                        'quantity_requested': total_quantity_requested
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        with transaction.atomic():
            sale = Sale.objects.create(
                shop=shop,
                user=request.user,
                note=note
            )

            for item in validated_items:
                product = item['product']
                quantity = item['quantity']

                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    unit_price=product.sale_price
                )

                product.reduce_stock(quantity)

            sale.update_total_amount()

        result = SaleSerializer(sale)
        return Response(
            {
                'message': 'Vente créée avec succès et stock mis à jour.',
                'sale': result.data
            },
            status=status.HTTP_201_CREATED
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sale_detail(request, sale_id):
    """
    Retourne le détail d'une vente appartenant à la boutique connectée.
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        sale = Sale.objects.get(id=sale_id, shop=shop)
    except Sale.DoesNotExist:
        return Response(
            {'error': 'Vente introuvable dans votre boutique.'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = SaleSerializer(sale)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_history(request):
    """
    Retourne l'historique des ventes de la boutique connectée
    avec filtres simples.
    Filtres disponibles :
    - date_from=YYYY-MM-DD
    - date_to=YYYY-MM-DD
    - user_id=ID_UTILISATEUR
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    sales = Sale.objects.filter(shop=shop).order_by('-created_at')

    # Filtre par date de début
    date_from = request.query_params.get('date_from')
    if date_from:
        sales = sales.filter(created_at__date__gte=date_from)

    # Filtre par date de fin
    date_to = request.query_params.get('date_to')
    if date_to:
        sales = sales.filter(created_at__date__lte=date_to)

    # Filtre par vendeur
    user_id = request.query_params.get('user_id')
    if user_id:
        sales = sales.filter(user_id=user_id)
    total_amount = sum(sale.total_amount for sale in sales)
    serializer = SaleSerializer(sales, many=True)

    return Response({
            'count': sales.count(),
            'total_amount': total_amount,
            'results': serializer.data
        })