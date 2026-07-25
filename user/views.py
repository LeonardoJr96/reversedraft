from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

from .models import User
from .serializers import UserSerializer, MeSerializer, ChangePasswordSerializer

from .services import register_user
from common.validators import validate_birth_date
from common.services import log_personal_data_access

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):

        try:

            if not validate_birth_date(serializer.validated_data['birth_date']):
                raise DRFValidationError({
                    'birth_date': "É necessário ter pelo menos 18 anos para se cadastrar."
            })

            serializer.validated_data.pop('password_confirm')
            serializer.validated_data.pop('accept_terms')
            serializer.validated_data['terms_accepted_at'] = timezone.now()

            user = register_user(
                serializer.validated_data
            )
            
            log_personal_data_access(actor=user, subject=user, action='cadastro_realizado', request=self.request)

        except DjangoValidationError as e:
            raise DRFValidationError(str(e))

        serializer.instance = user


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/users/me/  -> perfil + saldo de lances + histórico de participações
    PATCH/PUT /api/v1/users/me/ -> edita os campos editáveis do próprio perfil
    (Cláusula 2.1.1: "Área minha conta, com saldo de lances e histórico de participações")
    """
    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        serializer.save()
        log_personal_data_access(actor=self.request.user, subject=self.request.user, action='perfil_editado', request=self.request)


class ChangePasswordView(APIView):
    """
    POST /api/v1/users/change-password/
    Troca de senha do próprio usuário autenticado (exige a senha atual).
    Recuperação de senha por e-mail ("esqueci minha senha") é um fluxo à
    parte — precisa de um provedor de e-mail configurado, ver observação
    no chat.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data['current_password']):
            raise DRFValidationError({'current_password': 'Senha atual incorreta.'})

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        log_personal_data_access(actor=request.user, subject=request.user, action='senha_alterada', request=request)

        return Response({'detail': 'Senha alterada com sucesso.'})