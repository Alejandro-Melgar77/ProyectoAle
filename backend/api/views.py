# backend/api/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone

from django.utils.timezone import now
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

import io
import openpyxl

from .services.plan_pago import generar_plan
from .services.simulador import simular_plan
from .services.validadores import validar_vigencia

from .models import (
    Rol, Permiso, RolPermiso, UserProfile,
    Cliente, Empleado, SolicitudCredito,
    PlanPago, ProductoFinanciero,
    DocumentoTipo, RequisitoProductoDocumento, DocumentoAdjunto, ValidacionDocumento, ResultadoValidacionIA, TransaccionPago, PlanCuota,
)

from .serializers import (
    # Usuarios
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    UserDetailSerializer, UserProfileSerializer, PublicRegisterSerializer,

    # Roles / Permisos / Bitácora
    RolSerializer, PermisoSerializer, RolPermisoSerializer,

    # Personas
    ClienteSerializer, EmpleadoSerializer,
    ClienteNestedSerializer, EmpleadoNestedSerializer,

    # Solicitudes
    SolicitudCreateSerializer, SolicitudListSerializer, SolicitudDetailSerializer, 

    # Plan pago
    PlanPagoDTO, TransaccionPagoSerializer, CuotaPendienteSerializer, PagoTarjetaSerializer, StripePaymentIntentSerializer, ConfirmarPagoSerializer,

    # Productos / Documentos
    ProductoFinancieroSerializer, DocumentoAdjuntoSerializer, DocumentoTipoSerializer,
    RequisitoProductoDocumentoSerializer, RequisitoProductoDocumentoWriteSerializer,
    ProcesarValidacionSerializer, ValidacionDocumentoSerializer, ResultadoValidacionIASerializer, DocumentoValidacionSerializer
)

#Bitacora;
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers_auth import CustomTokenObtainPairSerializer 
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import status

# =========================================================
#                    PERMISOS DE NEGOCIO
# =========================================================
class IsOfficialOrAdmin(permissions.BasePermission):
    """Permite acceso a superuser o a usuarios con rol OFICIAL/ADMIN en UserProfile."""
    def has_permission(self, request, view):
        role = getattr(getattr(request.user, 'userprofile', None), 'rol', None)
        nombre = getattr(role, 'nombre', '').upper() if role else ''
        return bool(
            request.user and request.user.is_authenticated and
            (request.user.is_superuser or nombre in ('OFICIAL', 'ADMIN'))
        )
    
# =========================================================
#                    Registrar Inicio de Sesion
# =========================================================
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada de login (usa serializer que registra el acceso en Bitácora).
    """

    serializer_class = CustomTokenObtainPairSerializer

    def get_serializer_context(self):
        """
        Inyecta el request actual al serializer para poder registrar el acceso correctamente.
        """
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
# =========================================================
#                          USUARIOS
# =========================================================
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register_public', 'password_reset_request', 'password_reset_confirm']:
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action == 'list':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        u = request.user
        data = UserSerializer(u).data
        cli = Cliente.objects.filter(user=u).first()
        emp = Empleado.objects.filter(user=u).first()
        data['rol_nombre'] = getattr(getattr(u, 'userprofile', None), 'rol', None) and u.userprofile.rol.nombre
        data['cliente_id'] = cli.id if cli else None
        data['empleado_id'] = emp.id if emp else None
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_public(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)

    # -------- Password --------
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Contraseña actual incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Bitacora.objects.create(
            usuario=request.user,
            tipo_accion="CAMBIO_CONTRASENA",
            ip=self.get_client_ip(request)
        )
        return Response({"message": "Contraseña cambiada exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
            send_mail(
                'Restablecimiento de Contraseña',
                f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return Response({"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}, status=200)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace es inválido o ha expirado."}, status=400)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Contraseña restablecida exitosamente."}, status=200)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')
    
# =========================================================
#                    CLIENTE / EMPLEADO
# =========================================================
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related('user').all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cliente.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.select_related('user').all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Empleado.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#              ROLES / PERMISOS / BITÁCORA
# =========================================================
class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register_public', 'password_reset_request', 'password_reset_confirm']:
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action == 'list':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        u = request.user
        data = UserSerializer(u).data
        cli = Cliente.objects.filter(user=u).first()
        emp = Empleado.objects.filter(user=u).first()
        data['rol_nombre'] = getattr(getattr(u, 'userprofile', None), 'rol', None) and u.userprofile.rol.nombre
        data['cliente_id'] = cli.id if cli else None
        data['empleado_id'] = emp.id if emp else None
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_public(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)

    # -------- Password --------
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Contraseña actual incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Bitacora.objects.create(
            usuario=request.user,
            tipo_accion="CAMBIO_CONTRASENA",
            ip=self.get_client_ip(request)
        )
        return Response({"message": "Contraseña cambiada exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
            send_mail(
                'Restablecimiento de Contraseña',
                f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return Response({"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}, status=200)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace es inválido o ha expirado."}, status=400)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Contraseña restablecida exitosamente."}, status=200)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')
    
# =========================================================
#                    CLIENTE / EMPLEADO
# =========================================================
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related('user').all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cliente.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.select_related('user').all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Empleado.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#              ROLES / PERMISOS / BITÁCORA
# =========================================================
class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register_public', 'password_reset_request', 'password_reset_confirm']:
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action == 'list':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        u = request.user
        data = UserSerializer(u).data
        cli = Cliente.objects.filter(user=u).first()
        emp = Empleado.objects.filter(user=u).first()
        data['rol_nombre'] = getattr(getattr(u, 'userprofile', None), 'rol', None) and u.userprofile.rol.nombre
        data['cliente_id'] = cli.id if cli else None
        data['empleado_id'] = emp.id if emp else None
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_public(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)

    # -------- Password --------
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Contraseña actual incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Bitacora.objects.create(
            usuario=request.user,
            tipo_accion="CAMBIO_CONTRASENA",
            ip=self.get_client_ip(request)
        )
        return Response({"message": "Contraseña cambiada exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
            send_mail(
                'Restablecimiento de Contraseña',
                f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return Response({"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}, status=200)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace es inválido o ha expirado."}, status=400)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Contraseña restablecida exitosamente."}, status=200)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')
    
# =========================================================
#                    CLIENTE / EMPLEADO
# =========================================================
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related('user').all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cliente.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.select_related('user').all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Empleado.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#              ROLES / PERMISOS / BITÁCORA
# =========================================================
class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register_public', 'password_reset_request', 'password_reset_confirm']:
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action == 'list':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        u = request.user
        data = UserSerializer(u).data
        cli = Cliente.objects.filter(user=u).first()
        emp = Empleado.objects.filter(user=u).first()
        data['rol_nombre'] = getattr(getattr(u, 'userprofile', None), 'rol', None) and u.userprofile.rol.nombre
        data['cliente_id'] = cli.id if cli else None
        data['empleado_id'] = emp.id if emp else None
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_public(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)

    # -------- Password --------
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Contraseña actual incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Bitacora.objects.create(
            usuario=request.user,
            tipo_accion="CAMBIO_CONTRASENA",
            ip=self.get_client_ip(request)
        )
        return Response({"message": "Contraseña cambiada exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
            send_mail(
                'Restablecimiento de Contraseña',
                f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return Response({"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}, status=200)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace es inválido o ha expirado."}, status=400)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Contraseña restablecida exitosamente."}, status=200)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')
    
# =========================================================
#                    CLIENTE / EMPLEADO
# =========================================================
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related('user').all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cliente.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.select_related('user').all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Empleado.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#              ROLES / PERMISOS / BITÁCORA
# =========================================================
class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register_public', 'password_reset_request', 'password_reset_confirm']:
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action == 'list':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        u = request.user
        data = UserSerializer(u).data
        cli = Cliente.objects.filter(user=u).first()
        emp = Empleado.objects.filter(user=u).first()
        data['rol_nombre'] = getattr(getattr(u, 'userprofile', None), 'rol', None) and u.userprofile.rol.nombre
        data['cliente_id'] = cli.id if cli else None
        data['empleado_id'] = emp.id if emp else None
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_public(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)

    # -------- Password --------
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Contraseña actual incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Bitacora.objects.create(
            usuario=request.user,
            tipo_accion="CAMBIO_CONTRASENA",
            ip=self.get_client_ip(request)
        )
        return Response({"message": "Contraseña cambiada exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
            send_mail(
                'Restablecimiento de Contraseña',
                f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return Response({"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}, status=200)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace es inválido o ha expirado."}, status=400)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Contraseña restablecida exitosamente."}, status=200)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')
    
# =========================================================
#                    CLIENTE / EMPLEADO
# =========================================================
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related('user').all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cliente.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.select_related('user').all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Empleado.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#              ROLES / PERMISOS / BITÁCORA
# =========================================================
class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register_public', 'password_reset_request', 'password_reset_confirm']:
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action == 'list':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        u = request.user
        data = UserSerializer(u).data
        cli = Cliente.objects.filter(user=u).first()
        emp = Empleado.objects.filter(user=u).first()
        data['rol_nombre'] = getattr(getattr(u, 'userprofile', None), 'rol', None) and u.userprofile.rol.nombre
        data['cliente_id'] = cli.id if cli else None
        data['empleado_id'] = emp.id if emp else None
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_public(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)

    # -------- Password --------
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Contraseña actual incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Bitacora.objects.create(
            usuario=request.user,
            tipo_accion="CAMBIO_CONTRASENA",
            ip=self.get_client_ip(request)
        )
        return Response({"message": "Contraseña cambiada exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
            send_mail(
                'Restablecimiento de Contraseña',
                f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return Response({"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}, status=200)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace es inválido o ha expirado."}, status=400)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Contraseña restablecida exitosamente."}, status=200)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')
    
# =========================================================
#                    CLIENTE / EMPLEADO
# =========================================================
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related('user').all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cliente.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.select_related('user').all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Empleado.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#              ROLES / PERMISOS / BITÁCORA
# =========================================================
class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register_public', 'password_reset_request', 'password_reset_confirm']:
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action == 'list':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        u = request.user
        data = UserSerializer(u).data
        cli = Cliente.objects.filter(user=u).first()
        emp = Empleado.objects.filter(user=u).first()
        data['rol_nombre'] = getattr(getattr(u, 'userprofile', None), 'rol', None) and u.userprofile.rol.nombre
        data['cliente_id'] = cli.id if cli else None
        data['empleado_id'] = emp.id if emp else None
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_public(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)

    # -------- Password --------
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Contraseña actual incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Bitacora.objects.create(
            usuario=request.user,
            tipo_accion="CAMBIO_CONTRASENA",
            ip=self.get_client_ip(request)
        )
        return Response({"message": "Contraseña cambiada exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
            send_mail(
                'Restablecimiento de Contraseña',
                f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return Response({"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}, status=200)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace es inválido o ha expirado."}, status=400)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Contraseña restablecida exitosamente."}, status=200)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')
    
# =========================================================
#                    CLIENTE / EMPLEADO
# =========================================================
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related('user').all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cliente.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.select_related('user').all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Empleado.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#              ROLES / PERMISOS / BITÁCORA
# =========================================================
class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register_public', 'password_reset_request', 'password_reset_confirm']:
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action == 'list':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        u = request.user
        data = UserSerializer(u).data
        cli = Cliente.objects.filter(user=u).first()
        emp = Empleado.objects.filter(user=u).first()
        data['rol_nombre'] = getattr(getattr(u, 'userprofile', None), 'rol', None) and u.userprofile.rol.nombre
        data['cliente_id'] = cli.id if cli else None
        data['empleado_id'] = emp.id if emp else None
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_public(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)

    # -------- Password --------
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Contraseña actual incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Bitacora.objects.create(
            usuario=request.user,
            tipo_accion="CAMBIO_CONTRASENA",
            ip=self.get_client_ip(request)
        )
        return Response({"message": "Contraseña cambiada exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
            send_mail(
                'Restablecimiento de Contraseña',
                f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return Response({"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}, status=200)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace es inválido o ha expirado."}, status=400)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Contraseña restablecida exitosamente."}, status=200)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')
    
# =========================================================
#                    CLIENTE / EMPLEADO
# =========================================================
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related('user').all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cliente.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.select_related('user').all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Empleado.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#              ROLES / PERMISOS / BITÁCORA
# =========================================================
class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register_public', 'password_reset_request', 'password_reset_confirm']:
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action == 'list':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        u = request.user
        data = UserSerializer(u).data
        cli = Cliente.objects.filter(user=u).first()
        emp = Empleado.objects.filter(user=u).first()
        data['rol_nombre'] = getattr(getattr(u, 'userprofile', None), 'rol', None) and u.userprofile.rol.nombre
        data['cliente_id'] = cli.id if cli else None
        data['empleado_id'] = emp.id if emp else None
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_public(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)

    # -------- Password --------
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Contraseña actual incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Bitacora.objects.create(
            usuario=request.user,
            tipo_accion="CAMBIO_CONTRASENA",
            ip=self.get_client_ip(request)
        )
        return Response({"message": "Contraseña cambiada exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
            send_mail(
                'Restablecimiento de Contraseña',
                f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return Response({"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}, status=200)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace es inválido o ha expirado."}, status=400)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Contraseña restablecida exitosamente."}, status=200)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')
    
# =========================================================
#                    CLIENTE / EMPLEADO
# =========================================================
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related('user').all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cliente.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.select_related('user').all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Empleado.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#              ROLES / PERMISOS / BITÁCORA
# =========================================================
class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register_public', 'password_reset_request', 'password_reset_confirm']:
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action == 'list':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        u = request.user
        data = UserSerializer(u).data
        cli = Cliente.objects.filter(user=u).first()
        emp = Empleado.objects.filter(user=u).first()
        data['rol_nombre'] = getattr(getattr(u, 'userprofile', None), 'rol', None) and u.userprofile.rol.nombre
        data['cliente_id'] = cli.id if cli else None
        data['empleado_id'] = emp.id if emp else None
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_public(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)

    # -------- Password --------
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Contraseña actual incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Bitacora.objects.create(
            usuario=request.user,
            tipo_accion="CAMBIO_CONTRASENA",
            ip=self.get_client_ip(request)
        )
        return Response({"message": "Contraseña cambiada exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
            send_mail(
                'Restablecimiento de Contraseña',
                f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return Response({"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}, status=200)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace es inválido o ha expirado."}, status=400)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Contraseña restablecida exitosamente."}, status=200)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')
    
# =========================================================
#                    CLIENTE / EMPLEADO
# =========================================================
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related('user').all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cliente.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.select_related('user').all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Empleado.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#              ROLES / PERMISOS / BITÁCORA
# =========================================================
class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register_public', 'password_reset_request', 'password_reset_confirm']:
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action == 'list':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        u = request.user
        data = UserSerializer(u).data
        cli = Cliente.objects.filter(user=u).first()
        emp = Empleado.objects.filter(user=u).first()
        data['rol_nombre'] = getattr(getattr(u, 'userprofile', None), 'rol', None) and u.userprofile.rol.nombre
        data['cliente_id'] = cli.id if cli else None
        data['empleado_id'] = emp.id if emp else None
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_public(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)

    # -------- Password --------
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Contraseña actual incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Bitacora.objects.create(
            usuario=request.user,
            tipo_accion="CAMBIO_CONTRASENA",
            ip=self.get_client_ip(request)
        )
        return Response({"message": "Contraseña cambiada exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
            send_mail(
                'Restablecimiento de Contraseña',
                f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return Response({"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}, status=200)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace es inválido o ha expirado."}, status=400)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Contraseña restablecida exitosamente."}, status=200)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')
    
# =========================================================
#                    CLIENTE / EMPLEADO
# =========================================================
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related('user').all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cliente.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.select_related('user').all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Empleado.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#              ROLES / PERMISOS / BITÁCORA
# =========================================================
class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register_public', 'password_reset_request', 'password_reset_confirm']:
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action == 'list':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        u = request.user
        data = UserSerializer(u).data
        cli = Cliente.objects.filter(user=u).first()
        emp = Empleado.objects.filter(user=u).first()
        data['rol_nombre'] = getattr(getattr(u, 'userprofile', None), 'rol', None) and u.userprofile.rol.nombre
        data['cliente_id'] = cli.id if cli else None
        data['empleado_id'] = emp.id if emp else None
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_public(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)

    # -------- Password --------
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Contraseña actual incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Bitacora.objects.create(
            usuario=request.user,
            tipo_accion="CAMBIO_CONTRASENA",
            ip=self.get_client_ip(request)
        )
        return Response({"message": "Contraseña cambiada exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
            send_mail(
                'Restablecimiento de Contraseña',
                f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return Response({"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}, status=200)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace es inválido o ha expirado."}, status=400)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Contraseña restablecida exitosamente."}, status=200)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')
    
# =========================================================
#                    CLIENTE / EMPLEADO
# =========================================================
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related('user').all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cliente.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.select_related('user').all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Empleado.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#              ROLES / PERMISOS / BITÁCORA
# =========================================================
class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register_public', 'password_reset_request', 'password_reset_confirm']:
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action == 'list':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        u = request.user
        data = UserSerializer(u).data
        cli = Cliente.objects.filter(user=u).first()
        emp = Empleado.objects.filter(user=u).first()
        data['rol_nombre'] = getattr(getattr(u, 'userprofile', None), 'rol', None) and u.userprofile.rol.nombre
        data['cliente_id'] = cli.id if cli else None
        data['empleado_id'] = emp.id if emp else None
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_public(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)

    # -------- Password --------
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Contraseña actual incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Bitacora.objects.create(
            usuario=request.user,
            tipo_accion="CAMBIO_CONTRASENA",
            ip=self.get_client_ip(request)
        )
        return Response({"message": "Contraseña cambiada exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
            send_mail(
                'Restablecimiento de Contraseña',
                f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return Response({"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}, status=200)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace es inválido o ha expirado."}, status=400)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Contraseña restablecida exitosamente."}, status=200)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')
    
# =========================================================
#                    CLIENTE / EMPLEADO
# =========================================================
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related('user').all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cliente.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.select_related('user').all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Empleado.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#              ROLES / PERMISOS / BITÁCORA
# =========================================================
class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register_public', 'password_reset_request', 'password_reset_confirm']:
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action == 'list':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        u = request.user
        data = UserSerializer(u).data
        cli = Cliente.objects.filter(user=u).first()
        emp = Empleado.objects.filter(user=u).first()
        data['rol_nombre'] = getattr(getattr(u, 'userprofile', None), 'rol', None) and u.userprofile.rol.nombre
        data['cliente_id'] = cli.id if cli else None
        data['empleado_id'] = emp.id if emp else None
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_public(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)

    # -------- Password --------
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Contraseña actual incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Bitacora.objects.create(
            usuario=request.user,
            tipo_accion="CAMBIO_CONTRASENA",
            ip=self.get_client_ip(request)
        )
        return Response({"message": "Contraseña cambiada exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
            send_mail(
                'Restablecimiento de Contraseña',
                f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return Response({"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}, status=200)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace es inválido o ha expirado."}, status=400)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Contraseña restablecida exitosamente."}, status=200)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')
    
# =========================================================
#                    CLIENTE / EMPLEADO
# =========================================================
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related('user').all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cliente.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.select_related('user').all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Empleado.objects.select_related('user').filter(empresa=self.request.user.userprofile.empresa)
    
    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#              ROLES / PERMISOS / BITÁCORA
# =========================================================
class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register_public', 'password_reset_request', 'password_reset_confirm']:
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action == 'list':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        u = request.user
        data = UserSerializer(u).data
        cli = Cliente.objects.filter(user=u).first()
        emp = Empleado.objects.filter(user=u).first()
        data['rol_nombre'] = getattr(getattr(u, 'userprofile', None), 'rol', None) and u.userprofile.rol.nombre
        data['cliente_id'] = cli.id if cli else None
        data['empleado_id'] = emp.id if emp else None
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_public(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)

    # -------- Password --------
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Contraseña actual incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Bitacora.objects.create(
            usuario=request.user,
            tipo_accion="CAMBIO_CONTRASENA",
            ip=self.get_client_ip(request)
        )
        return Response({"message": "Contraseña cambiada exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
            send_mail(
                'Restablecimiento de Contraseña',
                f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return Response({"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}, status=200)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace es inválido o ha expirado."}, status=400)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Contraseña restablecida exitosamente."}, status=200)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')
    
# =========================================================
#                    PERMISOS
# =========================================================
class PermisoViewSet(viewsets.ModelViewSet):
    serializer_class = PermisoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Permiso.objects.filter(empresa=self.request.user.userprofile.empresa)

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class RolPermisoViewSet(viewsets.ModelViewSet):
    serializer_class = RolPermisoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return RolPermiso.objects.filter(empresa=self.request.user.userprofile.empresa)

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#                    SOLICITUDES
# =========================================================
class SolicitudCreditoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SolicitudCreateSerializer
        if self.action == 'list':
            return SolicitudListSerializer
        return SolicitudDetailSerializer
    
    def get_queryset(self):
        return SolicitudCredito.objects.filter(
            empresa=self.request.user.userprofile.empresa
        ).select_related('cliente', 'oficial', 'producto')

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#                    PRODUCTOS
# =========================================================
class ProductoFinancieroViewSet(viewsets.ModelViewSet):
    serializer_class = ProductoFinancieroSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ProductoFinanciero.objects.filter(
            empresa=self.request.user.userprofile.empresa,
            activo=True
        )

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#                    DOCUMENTOS
# =========================================================
class DocumentoTipoViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentoTipoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DocumentoTipo.objects.filter(empresa=self.request.user.userprofile.empresa)

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class RequisitoProductoDocumentoViewSet(viewsets.ModelViewSet):
    serializer_class = RequisitoProductoDocumentoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return RequisitoProductoDocumento.objects.filter(
            empresa=self.request.user.userprofile.empresa
        ).select_related('producto', 'documento')

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class DocumentoAdjuntoViewSet(viewsets.ModelViewSet):
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = DocumentoAdjuntoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DocumentoAdjunto.objects.filter(
            empresa=self.request.user.userprofile.empresa
        ).select_related('documento_tipo', 'solicitud')

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#                    VALIDACIONES
# =========================================================
class ValidacionDocumentoViewSet(viewsets.ModelViewSet):
    serializer_class = ValidacionDocumentoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ValidacionDocumento.objects.filter(
            empresa=self.request.user.userprofile.empresa
        ).select_related('documento')

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

class ResultadoValidacionIAViewSet(viewsets.ModelViewSet):
    serializer_class = ResultadoValidacionIASerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ResultadoValidacionIA.objects.filter(
            empresa=self.request.user.userprofile.empresa
        ).select_related('solicitud')

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)

# =========================================================
#                    PAGOS
# =========================================================
class TransaccionPagoViewSet(viewsets.ModelViewSet):
    serializer_class = TransaccionPagoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TransaccionPago.objects.filter(
            empresa=self.request.user.userprofile.empresa
        ).select_related('cuota')

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.userprofile.empresa)