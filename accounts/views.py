from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from shops.utils import get_user_membership


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Inscription d'un nouvel utilisateur.
    Cette route permet de créer un compte pour un commerçant.
    """
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')

    # Vérification simple des champs obligatoires
    if not username or not password:
        return Response(
            {'error': 'Le nom d’utilisateur et le mot de passe sont obligatoires.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Vérifier si le username existe déjà
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Ce nom d’utilisateur existe déjà.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Création de l'utilisateur
    user = User.objects.create_user(
        username=username,
        password=password,
        email=email
    )

    # Création automatique du token
    token = Token.objects.create(user=user)

    return Response(
        {
            'message': 'Utilisateur créé avec succès.',
            'token': token.key,
            'username': user.username
        },
        status=status.HTTP_201_CREATED
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Connexion utilisateur.
    Si les identifiants sont corrects, on retourne le token.
    """
    username = request.data.get('username')
    password = request.data.get('password')

    # Authentification Django
    user = authenticate(username=username, password=password)

    if user is not None:
        # Récupérer ou créer le token
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'message': 'Connexion réussie.',
            'token': token.key,
            'username': user.username
        })

    return Response(
        {'error': 'Identifiants invalides.'},
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """
    Retourne les informations de l'utilisateur connecté,
    avec son rôle dans la boutique.
    """
    membership = get_user_membership(request.user)

    has_shop = membership is not None
    role = membership.role if membership else None
    shop_name = membership.shop.name if membership else None

    return Response({
        'message': 'Vous êtes connecté.',
        'username': request.user.username,
        'user_id': request.user.id,

        # Boutique
        'has_shop': has_shop,
        'shop_name': shop_name,

        # Rôle multi-utilisateur
        'role': role,
        'is_owner': role == 'owner',
        'is_manager': role == 'manager',
        'is_seller': role == 'seller',
    })