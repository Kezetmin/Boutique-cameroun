from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Shop
from .models import ShopMember
from .serializers import ShopMemberSerializer, CreateShopMemberSerializer
from .permissions import IsOwner
from .utils import can_create_user, get_user_shop
from sales.models import Sale, SaleItem, SalePayment
from products.models import Product, Category, StockMovement
from customers.models import Customer
from inventory.models import InventorySession, InventoryItem

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_shop(request):
    """
    Permet à un utilisateur connecté de créer sa boutique.
    Un utilisateur ne peut créer qu'une seule boutique.
    """

    # Vérifier si l'utilisateur a déjà une boutique
    if Shop.objects.filter(user=request.user).exists():
        return Response(
            {'error': 'Vous avez déjà créé une boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    name = request.data.get('name')
    owner_name = request.data.get('owner_name')
    phone = request.data.get('phone')
    address = request.data.get('address')

    # Vérification simple
    if not name or not owner_name:
        return Response(
            {'error': 'Le nom de la boutique et le nom du responsable sont obligatoires.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    shop = Shop.objects.create(
        name=name,
        owner_name=owner_name,
        phone=phone,
        address=address,
        user=request.user
    )

    return Response(
        {
            'message': 'Boutique créée avec succès.',
            'shop': {
                'id': shop.id,
                'name': shop.name,
                'owner_name': shop.owner_name,
                'phone': shop.phone,
                'address': shop.address,
                'user': shop.user.username,
            }
        },
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_shop(request):
    """
    Retourne uniquement la boutique de l'utilisateur connecté.
    C'est une première étape d'isolation des données.
    """
    try:
        shop = request.user.shop
    except Shop.DoesNotExist:
        return Response(
            {'error': 'Aucune boutique trouvée pour cet utilisateur.'},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({
        'id': shop.id,
        'name': shop.name,
        'owner_name': shop.owner_name,
        'phone': shop.phone,
        'is_demo': shop.is_demo,
        'address': shop.address,
        'user': shop.user.username,
        'created_at': shop.created_at,
    })

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsOwner])
def shop_member_list_create(request):
    """
    GET  -> liste les membres de la boutique
    POST -> crée un nouveau membre dans la boutique
    Seul le owner peut gérer les membres.
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if request.method == 'GET':
        members = ShopMember.objects.filter(shop=shop).select_related('user').order_by('role')
        serializer = ShopMemberSerializer(members, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        can_create, error_message = can_create_user(shop)

        if not can_create:
            return Response(
                {'error': error_message},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CreateShopMemberSerializer(data=request.data)

        if serializer.is_valid():
            user = User.objects.create_user(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password'],
                email=serializer.validated_data.get('email', '')
            )

            member = ShopMember.objects.create(
                shop=shop,
                user=user,
                role=serializer.validated_data['role'],
                is_active=True
            )

            result = ShopMemberSerializer(member)

            return Response(
                {
                    'message': 'Membre ajouté avec succès.',
                    'member': result.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsOwner])
def shop_member_detail(request, member_id):
    """
    PUT    -> modifier le rôle ou l'état d'un membre
    DELETE -> désactiver un membre
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        member = ShopMember.objects.get(id=member_id, shop=shop)
    except ShopMember.DoesNotExist:
        return Response(
            {'error': 'Membre introuvable dans votre boutique.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if member.role == ShopMember.OWNER:
        return Response(
            {'error': 'Impossible de modifier ou désactiver le propriétaire principal.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if request.method == 'PUT':
        role = request.data.get('role')
        is_active = request.data.get('is_active')

        if role:
            if role not in [ShopMember.MANAGER, ShopMember.SELLER]:
                return Response(
                    {'error': 'Rôle invalide.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            member.role = role

        if is_active is not None:
            member.is_active = is_active

        member.save()

        serializer = ShopMemberSerializer(member)

        return Response({
            'message': 'Membre mis à jour avec succès.',
            'member': serializer.data
        })

    if request.method == 'DELETE':
        member.is_active = False
        member.save(update_fields=['is_active'])

        return Response({
            'message': 'Membre désactivé avec succès.'
        })
    

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsOwner])
def reset_demo_data(request):
    """
    Réinitialise les données de démonstration
    uniquement pour une boutique demo.
    """

    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Boutique introuvable.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not shop.is_demo:
        return Response(
            {
                'error': (
                    'Réinitialisation autorisée uniquement '
                    'pour les boutiques de démonstration.'
                )
            },
            status=status.HTTP_403_FORBIDDEN
        )

    # ventes
    SalePayment.objects.filter(shop=shop).delete()
    SaleItem.objects.filter(sale__shop=shop).delete()
    Sale.objects.filter(shop=shop).delete()

    # clients
    Customer.objects.filter(shop=shop).delete()

    # stock
    StockMovement.objects.filter(shop=shop).delete()

    # inventaire
    InventoryItem.objects.filter(
        session__shop=shop
    ).delete()

    InventorySession.objects.filter(
        shop=shop
    ).delete()

    # produits + catégories
    Product.objects.filter(shop=shop).delete()
    Category.objects.filter(shop=shop).delete()

    return Response({
        'message': 'Données de démonstration réinitialisées avec succès.'
    })