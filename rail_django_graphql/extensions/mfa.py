"""
Système d'authentification multi-facteurs (MFA) pour Django GraphQL.

Ce module fournit :
- Authentification TOTP (Time-based One-Time Password)
- Codes de récupération
- Authentification par SMS (optionnel)
- Gestion des appareils de confiance
"""

import secrets
import qrcode
import base64
from io import BytesIO
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
import pyotp
import logging

from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone as django_timezone
from django.core.exceptions import ValidationError

import graphene
from graphene_django import DjangoObjectType

logger = logging.getLogger(__name__)


class MFADevice(models.Model):
    """
    Modèle pour les appareils MFA de l'utilisateur.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mfa_devices')
    device_name = models.CharField(max_length=100, help_text="Nom de l'appareil (ex: iPhone, Authenticator)")
    device_type = models.CharField(max_length=20, choices=[
        ('totp', 'TOTP Authenticator'),
        ('sms', 'SMS'),
        ('backup', 'Codes de récupération')
    ])
    secret_key = models.CharField(max_length=32, help_text="Clé secrète pour TOTP")
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True, help_text="Pour SMS MFA")
    
    class Meta:
        app_label = 'rail_django_graphql'
        db_table = 'mfa_devices'
        unique_together = ['user', 'device_name']
    
    def __str__(self):
        return f"{self.user.username} - {self.device_name} ({self.device_type})"
    
    def generate_qr_code(self) -> str:
        """
        Génère un QR code pour configurer l'authentificateur TOTP.
        
        Returns:
            QR code en base64
        """
        if self.device_type != 'totp':
            raise ValueError("QR code uniquement disponible pour TOTP")
        
        totp = pyotp.TOTP(self.secret_key)
        provisioning_uri = totp.provisioning_uri(
            name=self.user.username,
            issuer_name=getattr(settings, 'MFA_ISSUER_NAME', 'Django GraphQL App')
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def verify_token(self, token: str) -> bool:
        """
        Vérifie un token MFA.
        
        Args:
            token: Token à vérifier
            
        Returns:
            True si le token est valide
        """
        if self.device_type == 'totp':
            return self._verify_totp_token(token)
        elif self.device_type == 'backup':
            return self._verify_backup_code(token)
        elif self.device_type == 'sms':
            return self._verify_sms_token(token)
        
        return False
    
    def _verify_totp_token(self, token: str) -> bool:
        """
        Vérifie un token TOTP.
        
        Args:
            token: Token TOTP à vérifier
            
        Returns:
            True si le token est valide
        """
        try:
            totp = pyotp.TOTP(self.secret_key)
            # Vérifier avec une fenêtre de tolérance de ±1 période (30 secondes)
            return totp.verify(token, valid_window=1)
        except Exception as e:
            logger.error(f"Erreur lors de la vérification TOTP: {e}")
            return False
    
    def _verify_backup_code(self, code: str) -> bool:
        """
        Vérifie un code de récupération.
        
        Args:
            code: Code de récupération
            
        Returns:
            True si le code est valide
        """
        try:
            backup_codes = MFABackupCode.objects.filter(
                device=self,
                code=code,
                is_used=False
            )
            
            if backup_codes.exists():
                # Marquer le code comme utilisé
                backup_code = backup_codes.first()
                backup_code.is_used = True
                backup_code.used_at = django_timezone.now()
                backup_code.save()
                return True
            
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du code de récupération: {e}")
            return False
    
    def _verify_sms_token(self, token: str) -> bool:
        """
        Vérifie un token SMS.
        
        Args:
            token: Token SMS à vérifier
            
        Returns:
            True si le token est valide
        """
        cache_key = f"sms_token_{self.user.id}_{self.id}"
        stored_token = cache.get(cache_key)
        
        if stored_token and stored_token == token:
            cache.delete(cache_key)
            return True
        
        return False


class MFABackupCode(models.Model):
    """
    Codes de récupération MFA.
    """
    device = models.ForeignKey(MFADevice, on_delete=models.CASCADE, related_name='backup_codes')
    code = models.CharField(max_length=10)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        app_label = 'rail_django_graphql'
        db_table = 'mfa_backup_codes'
    
    def __str__(self):
        return f"Code de récupération pour {self.device.user.username}"


class TrustedDevice(models.Model):
    """
    Appareils de confiance pour éviter MFA répétitif.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trusted_devices')
    device_fingerprint = models.CharField(max_length=64, unique=True)
    device_name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        app_label = 'rail_django_graphql'
        db_table = 'trusted_devices'
    
    def __str__(self):
        return f"Appareil de confiance - {self.user.username} - {self.device_name}"
    
    def is_expired(self) -> bool:
        """Vérifie si l'appareil de confiance a expiré."""
        return django_timezone.now() > self.expires_at


class MFAManager:
    """
    Gestionnaire pour les opérations MFA.
    """
    
    def __init__(self):
        """Initialise le gestionnaire MFA."""
        self.totp_validity_window = getattr(settings, 'MFA_TOTP_VALIDITY_WINDOW', 1)
        self.backup_codes_count = getattr(settings, 'MFA_BACKUP_CODES_COUNT', 10)
        self.trusted_device_duration = getattr(settings, 'MFA_TRUSTED_DEVICE_DURATION', 30)  # jours
        self.sms_token_length = getattr(settings, 'MFA_SMS_TOKEN_LENGTH', 6)
        self.sms_token_validity = getattr(settings, 'MFA_SMS_TOKEN_VALIDITY', 300)  # 5 minutes
    
    def setup_totp_device(self, user: User, device_name: str) -> Tuple[MFADevice, str]:
        """
        Configure un appareil TOTP pour l'utilisateur.
        
        Args:
            user: Utilisateur
            device_name: Nom de l'appareil
            
        Returns:
            Tuple (appareil MFA, QR code en base64)
        """
        # Générer une clé secrète
        secret_key = pyotp.random_base32()
        
        # Créer l'appareil MFA
        device = MFADevice.objects.create(
            user=user,
            device_name=device_name,
            device_type='totp',
            secret_key=secret_key,
            is_active=False  # Sera activé après vérification
        )
        
        # Générer le QR code
        qr_code = device.generate_qr_code()
        
        return device, qr_code
    
    def verify_and_activate_totp_device(self, device: MFADevice, token: str) -> bool:
        """
        Vérifie et active un appareil TOTP.
        
        Args:
            device: Appareil MFA à activer
            token: Token de vérification
            
        Returns:
            True si l'activation a réussi
        """
        if device.verify_token(token):
            device.is_active = True
            device.last_used = django_timezone.now()
            device.save()
            
            # Générer les codes de récupération
            self._generate_backup_codes(device)
            
            return True
        
        return False
    
    def setup_sms_device(self, user: User, phone_number: str, device_name: str) -> MFADevice:
        """
        Configure un appareil SMS pour l'utilisateur.
        
        Args:
            user: Utilisateur
            phone_number: Numéro de téléphone
            device_name: Nom de l'appareil
            
        Returns:
            Appareil MFA créé
        """
        device = MFADevice.objects.create(
            user=user,
            device_name=device_name,
            device_type='sms',
            phone_number=phone_number,
            secret_key='',  # Pas de clé secrète pour SMS
            is_active=True
        )
        
        return device
    
    def send_sms_token(self, device: MFADevice) -> bool:
        """
        Envoie un token SMS à l'utilisateur.
        
        Args:
            device: Appareil SMS
            
        Returns:
            True si l'envoi a réussi
        """
        if device.device_type != 'sms' or not device.phone_number:
            return False
        
        # Générer un token aléatoire
        token = ''.join([str(secrets.randbelow(10)) for _ in range(self.sms_token_length)])
        
        # Stocker le token en cache
        cache_key = f"sms_token_{device.user.id}_{device.id}"
        cache.set(cache_key, token, self.sms_token_validity)
        
        # Envoyer le SMS (implémentation dépendante du fournisseur)
        return self._send_sms(device.phone_number, token)
    
    def verify_mfa_token(self, user: User, token: str, device_id: Optional[int] = None) -> bool:
        """
        Vérifie un token MFA pour l'utilisateur.
        
        Args:
            user: Utilisateur
            token: Token à vérifier
            device_id: ID de l'appareil spécifique (optionnel)
            
        Returns:
            True si le token est valide
        """
        devices = user.mfa_devices.filter(is_active=True)
        
        if device_id:
            devices = devices.filter(id=device_id)
        
        for device in devices:
            if device.verify_token(token):
                device.last_used = django_timezone.now()
                device.save()
                return True
        
        return False
    
    def is_mfa_required(self, user: User) -> bool:
        """
        Détermine si MFA est requis pour l'utilisateur.
        
        Args:
            user: Utilisateur
            
        Returns:
            True si MFA est requis
        """
        # Vérifier si l'utilisateur a des appareils MFA actifs
        has_active_devices = user.mfa_devices.filter(is_active=True).exists()
        
        # Vérifier la politique MFA globale
        mfa_required_for_all = getattr(settings, 'MFA_REQUIRED_FOR_ALL_USERS', False)
        mfa_required_for_staff = getattr(settings, 'MFA_REQUIRED_FOR_STAFF', True)
        
        if mfa_required_for_all:
            return True
        
        if mfa_required_for_staff and (user.is_staff or user.is_superuser):
            return True
        
        return has_active_devices
    
    def is_device_trusted(self, user: User, device_fingerprint: str) -> bool:
        """
        Vérifie si un appareil est de confiance.
        
        Args:
            user: Utilisateur
            device_fingerprint: Empreinte de l'appareil
            
        Returns:
            True si l'appareil est de confiance
        """
        try:
            trusted_device = TrustedDevice.objects.get(
                user=user,
                device_fingerprint=device_fingerprint,
                is_active=True
            )
            
            if trusted_device.is_expired():
                trusted_device.is_active = False
                trusted_device.save()
                return False
            
            return True
        except TrustedDevice.DoesNotExist:
            return False
    
    def add_trusted_device(self, user: User, device_fingerprint: str, 
                          device_name: str, ip_address: str, user_agent: str) -> TrustedDevice:
        """
        Ajoute un appareil de confiance.
        
        Args:
            user: Utilisateur
            device_fingerprint: Empreinte de l'appareil
            device_name: Nom de l'appareil
            ip_address: Adresse IP
            user_agent: User agent
            
        Returns:
            Appareil de confiance créé
        """
        expires_at = django_timezone.now() + timedelta(days=self.trusted_device_duration)
        
        trusted_device = TrustedDevice.objects.create(
            user=user,
            device_fingerprint=device_fingerprint,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        
        return trusted_device
    
    def generate_device_fingerprint(self, ip_address: str, user_agent: str) -> str:
        """
        Génère une empreinte d'appareil.
        
        Args:
            ip_address: Adresse IP
            user_agent: User agent
            
        Returns:
            Empreinte de l'appareil
        """
        import hashlib
        fingerprint_data = f"{ip_address}:{user_agent}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()
    
    def get_backup_codes(self, user: User) -> List[str]:
        """
        Récupère les codes de récupération non utilisés de l'utilisateur.
        
        Args:
            user: Utilisateur
            
        Returns:
            Liste des codes de récupération
        """
        backup_device = user.mfa_devices.filter(device_type='backup', is_active=True).first()
        
        if not backup_device:
            return []
        
        backup_codes = backup_device.backup_codes.filter(is_used=False)
        return [code.code for code in backup_codes]
    
    def regenerate_backup_codes(self, user: User) -> List[str]:
        """
        Régénère les codes de récupération pour l'utilisateur.
        
        Args:
            user: Utilisateur
            
        Returns:
            Nouveaux codes de récupération
        """
        # Supprimer les anciens codes
        backup_device = user.mfa_devices.filter(device_type='backup').first()
        
        if backup_device:
            backup_device.backup_codes.all().delete()
        else:
            backup_device = MFADevice.objects.create(
                user=user,
                device_name='Codes de récupération',
                device_type='backup',
                secret_key='',
                is_active=True
            )
        
        # Générer de nouveaux codes
        return self._generate_backup_codes(backup_device)
    
    def _generate_backup_codes(self, device: MFADevice) -> List[str]:
        """
        Génère des codes de récupération pour un appareil.
        
        Args:
            device: Appareil MFA
            
        Returns:
            Liste des codes générés
        """
        codes = []
        
        for _ in range(self.backup_codes_count):
            # Générer un code de 8 caractères
            code = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
            codes.append(code)
            
            MFABackupCode.objects.create(
                device=device,
                code=code
            )
        
        return codes
    
    def _send_sms(self, phone_number: str, token: str) -> bool:
        """
        Envoie un SMS avec le token.
        
        Args:
            phone_number: Numéro de téléphone
            token: Token à envoyer
            
        Returns:
            True si l'envoi a réussi
        """
        # Cette méthode doit être implémentée selon le fournisseur SMS choisi
        # (Twilio, AWS SNS, etc.)
        
        try:
            # Exemple avec Twilio (nécessite configuration)
            sms_provider = getattr(settings, 'MFA_SMS_PROVIDER', None)
            
            if sms_provider == 'twilio':
                return self._send_sms_twilio(phone_number, token)
            elif sms_provider == 'aws_sns':
                return self._send_sms_aws(phone_number, token)
            else:
                # Mode développement - logger le token
                logger.info(f"Token SMS pour {phone_number}: {token}")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi SMS: {e}")
            return False
    
    def _send_sms_twilio(self, phone_number: str, token: str) -> bool:
        """
        Envoie un SMS via Twilio.
        
        Args:
            phone_number: Numéro de téléphone
            token: Token à envoyer
            
        Returns:
            True si l'envoi a réussi
        """
        try:
            from twilio.rest import Client
            
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
            from_number = getattr(settings, 'TWILIO_FROM_NUMBER', '')
            
            client = Client(account_sid, auth_token)
            
            message = client.messages.create(
                body=f"Votre code de vérification: {token}",
                from_=from_number,
                to=phone_number
            )
            
            return message.sid is not None
            
        except Exception as e:
            logger.error(f"Erreur Twilio: {e}")
            return False
    
    def _send_sms_aws(self, phone_number: str, token: str) -> bool:
        """
        Envoie un SMS via AWS SNS.
        
        Args:
            phone_number: Numéro de téléphone
            token: Token à envoyer
            
        Returns:
            True si l'envoi a réussi
        """
        try:
            import boto3
            
            sns = boto3.client('sns')
            
            response = sns.publish(
                PhoneNumber=phone_number,
                Message=f"Votre code de vérification: {token}"
            )
            
            return response['ResponseMetadata']['HTTPStatusCode'] == 200
            
        except Exception as e:
            logger.error(f"Erreur AWS SNS: {e}")
            return False


# Instance globale du gestionnaire MFA
mfa_manager = MFAManager()


# Types GraphQL pour MFA

class MFADeviceType(DjangoObjectType):
    """Type GraphQL pour les appareils MFA."""
    
    class Meta:
        model = MFADevice
        fields = ('id', 'device_name', 'device_type', 'is_active', 'is_primary', 'created_at', 'last_used')


class TrustedDeviceType(DjangoObjectType):
    """Type GraphQL pour les appareils de confiance."""
    
    class Meta:
        model = TrustedDevice
        fields = ('id', 'device_name', 'ip_address', 'created_at', 'expires_at', 'is_active')


class SetupTOTPMutation(graphene.Mutation):
    """Mutation pour configurer TOTP."""
    
    class Arguments:
        device_name = graphene.String(required=True)
    
    success = graphene.Boolean()
    device_id = graphene.Int()
    qr_code = graphene.String()
    secret_key = graphene.String()
    message = graphene.String()
    
    def mutate(self, info, device_name):
        user = info.context.user
        
        if not user.is_authenticated:
            return SetupTOTPMutation(success=False, message="Authentification requise")
        
        try:
            device, qr_code = mfa_manager.setup_totp_device(user, device_name)
            
            return SetupTOTPMutation(
                success=True,
                device_id=device.id,
                qr_code=qr_code,
                secret_key=device.secret_key,
                message="Appareil TOTP configuré avec succès"
            )
        except Exception as e:
            return SetupTOTPMutation(success=False, message=str(e))


class VerifyTOTPMutation(graphene.Mutation):
    """Mutation pour vérifier et activer TOTP."""
    
    class Arguments:
        device_id = graphene.Int(required=True)
        token = graphene.String(required=True)
    
    success = graphene.Boolean()
    backup_codes = graphene.List(graphene.String)
    message = graphene.String()
    
    def mutate(self, info, device_id, token):
        user = info.context.user
        
        if not user.is_authenticated:
            return VerifyTOTPMutation(success=False, message="Authentification requise")
        
        try:
            device = MFADevice.objects.get(id=device_id, user=user)
            
            if mfa_manager.verify_and_activate_totp_device(device, token):
                backup_codes = mfa_manager.get_backup_codes(user)
                
                return VerifyTOTPMutation(
                    success=True,
                    backup_codes=backup_codes,
                    message="Appareil TOTP activé avec succès"
                )
            else:
                return VerifyTOTPMutation(success=False, message="Token invalide")
                
        except MFADevice.DoesNotExist:
            return VerifyTOTPMutation(success=False, message="Appareil non trouvé")
        except Exception as e:
            return VerifyTOTPMutation(success=False, message=str(e))


class MFAMutations(graphene.ObjectType):
    """Mutations MFA."""
    setup_totp = SetupTOTPMutation.Field()
    verify_totp = VerifyTOTPMutation.Field()


class MFAQueries(graphene.ObjectType):
    """Requêtes MFA."""
    mfa_devices = graphene.List(MFADeviceType)
    trusted_devices = graphene.List(TrustedDeviceType)
    backup_codes = graphene.List(graphene.String)
    
    def resolve_mfa_devices(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return []
        return user.mfa_devices.filter(is_active=True)
    
    def resolve_trusted_devices(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return []
        return user.trusted_devices.filter(is_active=True)
    
    def resolve_backup_codes(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return []
        return mfa_manager.get_backup_codes(user)