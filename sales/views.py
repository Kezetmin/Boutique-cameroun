from datetime import timedelta
from itertools import product

from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Sale, SaleItem
from .serializers import SaleSerializer, SaleCreateSerializer,AddSalePaymentSerializer
from shops.models import Shop
from products.models import Product
from django.db import transaction
from decimal import Decimal
from .models import Sale, SaleItem, SalePayment
from customers.models import Customer
from rest_framework.exceptions import ValidationError
from shops.permissions import CanSell, IsOwnerOrManager
from shops.utils import get_user_shop, get_user_role
from subscriptions.utils import can_manage_customer_credits
from subscriptions.utils import can_access_advanced_reports
from django.utils import timezone as dj_timezone
from subscriptions.utils import can_access_advanced_reports

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated,CanSell])
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
        role = get_user_role(request.user)
        sales = Sale.objects.filter(shop=shop).order_by('-created_at')
        if role == 'seller':
            sales = sales.filter(user=request.user)
       
        
        sale_status = request.query_params.get('status')
        if sale_status:
            sales = sales.filter(status=sale_status)

        serializer = SaleSerializer(sales, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = SaleCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        items_data = serializer.validated_data.get('items', [])
        note = serializer.validated_data.get('note', '')
        customer_id = serializer.validated_data.get('customer')
        amount_paid = serializer.validated_data.get('amount_paid', 0)
        customer = None
        if customer_id:
           try:
              customer = Customer.objects.get(id=customer_id, shop=shop)
           except Customer.DoesNotExist:
                return Response(
                    {'error': 'Client introuvable dans votre boutique.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        # Vérification complète du stock avant création
        validated_items = []
        requested_quantities = {}

        for item_data in items_data:
            product_id = item_data.get('product')
            quantity = item_data.get('quantity')
            custom_unit_price = item_data.get('unit_price')

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
            try :
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
            # Ici seulement, product existe
            unit_price = product.sale_price
            if custom_unit_price is not None:
                try:
                 unit_price = Decimal(str(custom_unit_price))

                except:
                    return Response(
                        {'error': 'Le prix de vente personnalisé est invalide.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if unit_price <= 0:
                    return Response(
                        {'error': 'Le prix de vente personnalisé doit être supérieur à 0.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if unit_price < product.purchase_price:
                    return Response(
                        {
                             'error': f'Le prix de vente de "{product.name}" ne peut pas être inférieur au prix d’achat.',
                'product_name': product.name,
                'purchase_price': str(product.purchase_price),
                'unit_price_requested': str(unit_price)
                            },
                        status=status.HTTP_400_BAD_REQUEST
                    )
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
                'quantity': quantity,
                'unit_price': unit_price
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
                customer=customer,
                note=note
            )

            for item in validated_items:
                product = item['product']
                quantity = item['quantity']
                unit_price = item['unit_price']

                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price
                )

                product.reduce_stock(quantity)

            sale.update_total_amount()

            if amount_paid > sale.total_amount:
                raise ValidationError({
                    'error': 'Le montant payé ne peut pas dépasser le total de la vente.'
                })
            
            if amount_paid < sale.total_amount:
                  if not can_manage_customer_credits(shop):
                    return Response(
                        {'error': 'Votre abonnement actuel ne permet pas les ventes à crédit. Veuillez contacter le support pour plus d’informations.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            if amount_paid < sale.total_amount and not customer:
                raise ValidationError({
                    'error': 'Le client est obligatoire pour une vente partielle ou impayée.'
                })

            sale.amount_paid = amount_paid
            sale.update_payment_status()

            if amount_paid > 0:
                SalePayment.objects.create(
                    shop=shop,
                    sale=sale,
                    customer=customer,
                    user=request.user,
                    amount=amount_paid,
                    note='Paiement initial'
                )

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
    Historique des ventes.

    Owner / Manager :
    - voient toutes les ventes de la boutique
    - peuvent filtrer par vendeur

    Seller :
    - voit uniquement ses propres ventes

    Pack Basic :
    - historique simple

    Pack Pro :
    - filtres avancés
    """

    shop = get_user_shop(request.user)
    role = get_user_role(request.user)

    if not shop:
        return Response(
            {'error': 'Boutique introuvable.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------
    # Récupération des filtres
    # -----------------------------
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    period = request.query_params.get('period')
    user_id = request.query_params.get('user_id')

    # -----------------------------
    # Base queryset
    # -----------------------------
    sales = Sale.objects.filter(
        shop=shop
    ).order_by('-created_at')

    # -----------------------------
    # Seller → uniquement ses ventes
    # -----------------------------
    if role == 'seller':
        sales = sales.filter(user=request.user)

    # -----------------------------
    # Owner / Manager → filtre vendeur
    # -----------------------------
    if user_id and role in ['owner', 'manager']:
        sales = sales.filter(user_id=user_id)

    # -----------------------------
    # Filtres avancés → Pro uniquement
    # -----------------------------
    if (date_from or date_to or user_id) and not can_access_advanced_reports(shop):
        return Response(
            {
                'error': (
                    'Les filtres avancés sont disponibles '
                    'uniquement en pack Pro.'
                )
            },
            status=status.HTTP_403_FORBIDDEN
        )

    # -----------------------------
    # Filtre date début
    # -----------------------------
    if date_from:
        sales = sales.filter(
            created_at__date__gte=date_from
        )

    # -----------------------------
    # Filtre date fin
    # -----------------------------
    if date_to:
        sales = sales.filter(
            created_at__date__lte=date_to
        )

    # -----------------------------
    # Filtres rapides période
    # -----------------------------
    today = dj_timezone.localdate()

    if period == 'today':
        sales = sales.filter(
            created_at__date=today
        )

    elif period == '7days':
        start_date = today - timedelta(days=7)

        sales = sales.filter(
            created_at__date__gte=start_date
        )

    elif period == '30days':
        start_date = today - timedelta(days=30)

        sales = sales.filter(
            created_at__date__gte=start_date
        )

    serializer = SaleSerializer(
        sales,
        many=True
    )

    return Response({
        'count': sales.count(),
        'results': serializer.data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated,IsOwnerOrManager])
def cancel_sale(request, sale_id):
    """
    Annule une vente sans la supprimer.
    Remet automatiquement les quantités vendues dans le stock.
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

    if sale.status == Sale.CANCELLED:
        return Response(
            {'error': 'Cette vente est déjà annulée.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    reason = request.data.get('reason', '')

    with transaction.atomic():
        sale.cancel(reason=reason)

    serializer = SaleSerializer(sale)

    return Response({
        'message': 'Vente annulée avec succès. Le stock a été restauré.',
        'sale': serializer.data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated,CanSell])
def add_sale_payment(request, sale_id):
    """
    Ajoute un paiement à une vente partielle ou impayée.
    Met à jour le montant payé, le reste à payer et le statut.
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
    if not can_manage_customer_credits(shop):
        return Response(
        {'error': 'Les paiements de dettes sont réservés au pack Pro.'},
        status=status.HTTP_403_FORBIDDEN
    )

    if sale.status == Sale.CANCELLED:
        return Response(
            {'error': 'Impossible d’ajouter un paiement sur une vente annulée.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if sale.payment_status == Sale.PAID:
        return Response(
            {'error': 'Cette vente est déjà totalement payée.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = AddSalePaymentSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    amount = serializer.validated_data['amount']
    note = serializer.validated_data.get('note', '')

    if amount > sale.remaining_amount:
        return Response(
            {
                'error': 'Le paiement dépasse le reste à payer.',
                'remaining_amount': str(sale.remaining_amount),
                'amount_requested': str(amount)
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        SalePayment.objects.create(
            shop=shop,
            sale=sale,
            customer=sale.customer,
            user=request.user,
            amount=amount,
            note=note or 'Paiement complémentaire'
        )

        sale.add_payment(amount)

    result = SaleSerializer(sale)

    return Response({
        'message': 'Paiement ajouté avec succès.',
        'sale': result.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_debts(request):
    """
    Liste uniquement les ventes non soldées :
    - payment_status partial ou unpaid
    - remaining_amount > 0

    Inclut aussi les articles concernés par chaque dette.
    """
    shop = get_user_shop(request.user)
    role = get_user_role(request.user)

    if not can_manage_customer_credits(shop):
       return Response(
        {'error': 'La gestion des dettes est réservée au pack Pro.'},
        status=status.HTTP_403_FORBIDDEN
    )

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    debts = Sale.objects.filter(
        shop=shop,
        status=Sale.VALIDATED,
        payment_status__in=[Sale.PARTIAL, Sale.UNPAID],
        remaining_amount__gt=0
    ).order_by('-created_at')
    
    if role == 'seller':
        debts = debts.filter(user=request.user)


    data = []

    for sale in debts:
        items_data = []

        for item in sale.items.all():
            items_data.append({
                'product_name': item.product.name,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'subtotal': item.subtotal,
            })

        data.append({
            'id': sale.id,
            'customer_name': sale.customer.name if sale.customer else None,
            'customer_phone': sale.customer.phone if sale.customer else None,
            'total_amount': sale.total_amount,
            'amount_paid': sale.amount_paid,
            'remaining_amount': sale.remaining_amount,
            'payment_status': sale.payment_status,
            'created_at': sale.created_at,
            'username': sale.user.username if sale.user else None,
            'items': items_data,
        })

    return Response({
        'count': debts.count(),
        'results': data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sale_receipt(request, sale_id):
    """
    Retourne les données d’un reçu de vente.
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
            {'error': 'Vente introuvable.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Préparer les données du reçu
    items = []
    for item in sale.items.all():
        items.append({
            'product_name': item.product.name,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'subtotal': item.subtotal,
        })

    data = {
        'receipt_number': sale.receipt_number,
        'shop_name': sale.shop.name,
        'date': sale.created_at,
        'seller': sale.user.username,
        'customer': sale.customer.name if sale.customer else None,
        'items': items,
        'total_amount': sale.total_amount,
        'amount_paid': sale.amount_paid,
        'remaining_amount': sale.remaining_amount,
        'payment_status': sale.payment_status,
    }

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cash_summary(request):
    """
    Résumé de la caisse.

    Basic :
    - caisse du jour uniquement

    Pro :
    - filtres date_from / date_to autorisés
    """
    shop = get_user_shop(request.user)
    role = get_user_role(request.user)

    if not shop:
        return Response(
            {'error': 'Boutique introuvable.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    today = dj_timezone.localdate()

    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    user_id = request.query_params.get('user_id')

    # Par défaut : aujourd'hui
    start_date = today
    end_date = today

    # Les filtres avancés sont réservés au Pro
    if date_from or date_to:
        if not can_access_advanced_reports(shop):
            return Response(
                {
                    'error': 'Les filtres de caisse sont disponibles uniquement en pack Pro.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        start_date = date_from or today
        end_date = date_to or today

    sales = Sale.objects.filter(
        shop=shop,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
        status=Sale.VALIDATED
    )

    if role == 'seller':
        sales = sales.filter(user=request.user)
    if user_id and role in ['owner', 'manager']:
        sales = sales.filter(user_id=user_id)

    payments = SalePayment.objects.filter(
        shop=shop,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )

    if role == 'seller':
        payments = payments.filter(user=request.user)

    total_sales = sum(sale.total_amount for sale in sales)
    total_paid = sum(sale.amount_paid for sale in sales)
    total_remaining = sum(sale.remaining_amount for sale in sales)
    total_payments = sum(payment.amount for payment in payments)

    return Response({
        'date_from': start_date,
        'date_to': end_date,
        'is_advanced': bool(date_from or date_to),
        'total_sales': total_sales,
        'total_paid': total_paid,
        'total_remaining': total_remaining,
        'total_payments': total_payments,
        'sales_count': sales.count(),
        'payments_count': payments.count(),
    })