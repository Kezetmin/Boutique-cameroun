from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Shop


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
        'address': shop.address,
        'user': shop.user.username,
        'created_at': shop.created_at,
    })