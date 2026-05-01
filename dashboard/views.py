from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shops.models import Shop
from products.models import Product
from subscriptions.permissions import CanAccessAdvancedReports
from sales.models import Sale, SaleItem, SalePayment
from shops.utils import get_user_shop, get_user_role

    


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    shop = get_user_shop(request.user)
    role = get_user_role(request.user)

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=400
        )

    today = timezone.localdate()
    period = request.query_params.get('period', 'today')

    if period == '7days':
        start_date = today - timezone.timedelta(days=6)
    elif period == '30days':
        start_date = today - timezone.timedelta(days=29)
    else:
        period = 'today'
        start_date = today

    end_date = today

    valid_sales_period = Sale.objects.filter(
        shop=shop,
        status=Sale.VALIDATED,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )

    cancelled_sales_period = Sale.objects.filter(
        shop=shop,
        status=Sale.CANCELLED,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )

    if role == 'seller':
        valid_sales_period = valid_sales_period.filter(user=request.user)
        cancelled_sales_period = cancelled_sales_period.filter(user=request.user)

    sales_count_today = valid_sales_period.count()

    total_sales_today = valid_sales_period.aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')

    cash_collected_today = SalePayment.objects.filter(
        shop=shop,
        sale__status=Sale.VALIDATED,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )

    if role == 'seller':
        cash_collected_today = cash_collected_today.filter(user=request.user)

    cash_collected_today = cash_collected_today.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')

    profit_expression = ExpressionWrapper(
        (F('unit_price') - F('product__purchase_price')) * F('quantity'),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )

    sale_items_period = SaleItem.objects.filter(
        sale__shop=shop,
        sale__status=Sale.VALIDATED,
        sale__created_at__date__gte=start_date,
        sale__created_at__date__lte=end_date
    )

    if role == 'seller':
        sale_items_period = sale_items_period.filter(sale__user=request.user)

    today_profit = sale_items_period.aggregate(
        total_profit=Sum(profit_expression)
    )['total_profit'] or Decimal('0.00')

    debts_sales = Sale.objects.filter(
        shop=shop,
        status=Sale.VALIDATED,
        remaining_amount__gt=0
    )

    if role == 'seller':
        debts_sales = debts_sales.filter(user=request.user)

    total_remaining_debts = debts_sales.aggregate(
        total=Sum('remaining_amount')
    )['total'] or Decimal('0.00')

    unpaid_sales_count = debts_sales.count()

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

    top_products = SaleItem.objects.filter(
        sale__shop=shop,
        sale__status=Sale.VALIDATED,
        sale__created_at__date__gte=start_date,
        sale__created_at__date__lte=end_date
    )

    if role == 'seller':
        top_products = top_products.filter(sale__user=request.user)

    top_products = top_products.values(
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

    return Response({
        'shop_name': shop.name,
        'date': today,
        'period': period,
        'start_date': start_date,
        'end_date': end_date,

        'role': role,

        'sales_count_today': sales_count_today,
        'total_sales_today': total_sales_today,
        'today_profit': today_profit,
        'cash_collected_today': cash_collected_today,

        'total_remaining_debts': total_remaining_debts,
        'unpaid_sales_count': unpaid_sales_count,

        'cancelled_sales_today': cancelled_sales_period.count(),

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