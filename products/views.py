from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from shops.models import Shop
from django.db import transaction
from .models import Product, Category, StockMovement
from .serializers import ProductSerializer, CategorySerializer, StockMovementSerializer
from subscriptions.utils import can_create_product
from subscriptions.permissions import HasValidSubscription


def get_user_shop(user):
    """
    Retourne la boutique de l'utilisateur connecté.
    """
    try:
        return user.shop
    except Shop.DoesNotExist:
        return None


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, HasValidSubscription])
def category_list_create(request):
    """
    GET  -> liste les catégories de la boutique connectée
    POST -> crée une catégorie pour la boutique connectée
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if request.method == 'GET':
        categories = Category.objects.filter(shop=shop).order_by('name')
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = CategorySerializer(data=request.data)

        if serializer.is_valid():
            name = serializer.validated_data['name']

            if Category.objects.filter(name__iexact=name, shop=shop).exists():
                return Response(
                    {'error': 'Cette catégorie existe déjà dans votre boutique.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer.save(shop=shop)
            return Response(
                {
                    'message': 'Catégorie créée avec succès.',
                    'category': serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, HasValidSubscription])
def category_detail(request, category_id):
    """
    GET    -> détail d’une catégorie
    PUT    -> modification d’une catégorie
    DELETE -> suppression d’une catégorie
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        category = Category.objects.get(id=category_id, shop=shop)
    except Category.DoesNotExist:
        return Response(
            {'error': 'Catégorie introuvable dans votre boutique.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = CategorySerializer(category, data=request.data)

        if serializer.is_valid():
            name = serializer.validated_data['name']

            if Category.objects.filter(name__iexact=name, shop=shop).exclude(id=category.id).exists():
                return Response(
                    {'error': 'Une autre catégorie avec ce nom existe déjà dans votre boutique.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer.save(shop=shop)
            return Response(
                {
                    'message': 'Catégorie mise à jour avec succès.',
                    'category': serializer.data
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        category.delete()
        return Response(
            {'message': 'Catégorie supprimée avec succès.'},
            status=status.HTTP_200_OK
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def product_list_create(request):
    """
    GET  -> liste les produits de la boutique connectée
    POST -> crée un produit dans la boutique connectée
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if request.method == 'GET':
        products = Product.objects.filter(shop=shop).order_by('-created_at')
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        can_create, error_message = can_create_product(shop)
        if not can_create:
            return Response(
                {'error': error_message},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            category = None
            category_id = serializer.validated_data.get('category')

            if category_id:
                if category_id.shop != shop:
                    return Response(
                        {'error': 'Cette catégorie ne vous appartient pas.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                category = category_id

            serializer.save(shop=shop, category=category)
            return Response(
                {
                    'message': 'Produit créé avec succès.',
                    'product': serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def product_detail(request, product_id):
    """
    GET    -> détail d’un produit
    PUT    -> modification d’un produit
    DELETE -> suppression d’un produit
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        product = Product.objects.get(id=product_id, shop=shop)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Produit introuvable dans votre boutique.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = ProductSerializer(product, data=request.data)

        if serializer.is_valid():
            category = serializer.validated_data.get('category')

            if category and category.shop != shop:
                return Response(
                    {'error': 'Cette catégorie ne vous appartient pas.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer.save(shop=shop)
            return Response(
                {
                    'message': 'Produit mis à jour avec succès.',
                    'product': serializer.data
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        product.delete()
        return Response(
            {'message': 'Produit supprimé avec succès.'},
            status=status.HTTP_200_OK
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stock_entry(request):
    """
    Permet d'ajouter du stock à un produit de la boutique connectée.
    Crée aussi un mouvement de stock pour garder l'historique.
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    product_id = request.data.get('product')
    quantity = request.data.get('quantity')
    note = request.data.get('note', '')

    if not product_id:
        return Response(
            {'error': 'Le produit est obligatoire.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not quantity or int(quantity) <= 0:
        return Response(
            {'error': 'La quantité doit être supérieure à 0.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    quantity = int(quantity)

    try:
        product = Product.objects.get(id=product_id, shop=shop, is_active=True)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Produit introuvable dans votre boutique.'},
            status=status.HTTP_404_NOT_FOUND
        )

    with transaction.atomic():
        # Augmentation automatique du stock
        product.increase_stock(quantity)

        # Création de l'historique
        movement = StockMovement.objects.create(
            shop=shop,
            product=product,
            user=request.user,
            movement_type=StockMovement.IN,
            quantity=quantity,
            note=note
        )

    serializer = StockMovementSerializer(movement)

    return Response(
        {
            'message': 'Entrée de stock enregistrée avec succès.',
            'new_stock_quantity': product.stock_quantity,
            'movement': serializer.data
        },
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stock_movement_history(request):
    """
    Retourne l'historique des mouvements de stock
    de la boutique connectée.
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    movements = StockMovement.objects.filter(shop=shop).order_by('-created_at')

    product_id = request.query_params.get('product')
    movement_type = request.query_params.get('movement_type')

    if product_id:
        movements = movements.filter(product_id=product_id)

    if movement_type:
        movements = movements.filter(movement_type=movement_type)

    serializer = StockMovementSerializer(movements, many=True)

    return Response({
        'count': movements.count(),
        'results': serializer.data
    })