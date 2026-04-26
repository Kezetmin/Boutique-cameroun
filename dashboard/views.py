from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shops.models import Shop
from sales.models import Sale, SaleItem
from products.models import Product
from subscriptions.permissions import CanAccessAdvancedReports

def get_user_shop(user):
    """
    Retourne la boutique de l'utilisateur connecté.
    """
    try:
        return user.shop
    except Shop.DoesNotExist:
        return None
    


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Retourne les statistiques principales du dashboard
    pour la boutique de l'utilisateur connecté.
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=400
        )

    # Date du jour
    today = timezone.localdate()

    # Ventes du jour pour la boutique connectée
    today_sales = Sale.objects.filter(
        shop=shop,
        created_at__date=today
    )

    # Nombre de ventes du jour
    sales_count_today = today_sales.count()

    # Chiffre d'affaires du jour
    total_sales_today = today_sales.aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')

    # Calcul du bénéfice du jour
    # bénéfice = somme des (prix vente - prix achat) * quantité
    profit_expression = ExpressionWrapper(
        (F('unit_price') - F('product__purchase_price')) * F('quantity'),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )

    today_profit = SaleItem.objects.filter(
        sale__shop=shop,
        sale__created_at__date=today
    ).aggregate(
        total_profit=Sum(profit_expression)
    )['total_profit'] or Decimal('0.00')

    # Produits en stock faible
    low_stock_products = Product.objects.filter(
        shop=shop,
        stock_quantity__lte=F('low_stock_threshold'),
        is_active=True
    ).order_by('stock_quantity')

    low_stock_data = []
    for product in low_stock_products:
        low_stock_data.append({
            'id': product.id,
            'name': product.name,
            'stock_quantity': product.stock_quantity,
            'low_stock_threshold': product.low_stock_threshold,
            'category_name': product.category.name if product.category else None,
        })

    # Top produits les plus vendus
    top_products = SaleItem.objects.filter(
        sale__shop=shop
    ).values(
        'product',
        'product__name'
    ).annotate(
        total_quantity_sold=Sum('quantity'),
        sales_count=Count('id')
    ).order_by('-total_quantity_sold')[:5]

    top_products_data = []
    for item in top_products:
        top_products_data.append({
            'product_id': item['product'],
            'product_name': item['product__name'],
            'total_quantity_sold': item['total_quantity_sold'],
            'sales_count': item['sales_count'],
        })
    total_products = Product.objects.filter(shop=shop, is_active=True).count()
    return Response({
        'shop_name': shop.name,
        'date': today,
        'sales_count_today': sales_count_today,
        'total_sales_today': total_sales_today,
        'today_profit': today_profit,
        'low_stock_products': low_stock_data,
        'top_products': top_products_data,
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated, CanAccessAdvancedReports])
def advanced_dashboard_stats(request):
    """
    Exemple de route réservée au pack Pro.
    Plus tard, on mettra ici des rapports avancés.
    """
    return Response({
        'message': 'Bienvenue dans les rapports avancés Pro.',
        'data': {
            'advanced_reports': True
        }
    })