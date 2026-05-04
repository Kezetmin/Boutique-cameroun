from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from shops.permissions import IsShopMember, IsOwnerOrManager

from shops.models import Shop
from .models import Customer
from .serializers import CustomerSerializer
from shops.utils import get_user_shop




@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def customer_list_create(request):
    """
    GET  -> liste les clients de la boutique connectée
    POST -> crée un client dans la boutique connectée
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if request.method == 'GET':
        customers = Customer.objects.filter(shop=shop).order_by('name')
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = CustomerSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(shop=shop)
            return Response(
                {
                    'message': 'Client créé avec succès.',
                    'customer': serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated,IsShopMember])
def customer_detail(request, customer_id):
    """
    GET    -> détail d'un client
    PUT    -> modification d'un client
    DELETE -> suppression d'un client
    """
    shop = get_user_shop(request.user)

    if not shop:
        return Response(
            {'error': 'Vous devez d’abord créer une boutique.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        customer = Customer.objects.get(id=customer_id, shop=shop)
    except Customer.DoesNotExist:
        return Response(
            {'error': 'Client introuvable dans votre boutique.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = CustomerSerializer(customer)
        return Response(serializer.data)

    if request.method == 'PUT':
        if not IsOwnerOrManager().has_permission(request, None):
            return Response(
                {'error':'Action réservée au propriétaire ou au gérant.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = CustomerSerializer(customer, data=request.data)

        if serializer.is_valid():
            serializer.save(shop=shop)
            return Response(
                {
                    'message': 'Client mis à jour avec succès.',
                    'customer': serializer.data
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        if not IsOwnerOrManager().has_permission(request, None):
            return Response(
                {'error':'Action réservée au propriétaire ou au gérant.'},
                status=status.HTTP_403_FORBIDDEN
            )
        customer.delete()
        return Response(
            {'message': 'Client supprimé avec succès.'},
            status=status.HTTP_200_OK
        )