"""
Système de gestion des médias pour Django GraphQL Auto-Generation.

Ce module fournit des fonctionnalités avancées pour :
- Génération d'URLs de médias
- Pipeline de traitement d'images
- Génération de miniatures
- Intégration CDN
- Abstraction des backends de stockage
"""

import os
import io
from typing import Dict, List, Optional, Type, Any, Union, Tuple
from pathlib import Path
import hashlib
import uuid
from datetime import datetime
from urllib.parse import urljoin

import graphene
from graphene import ObjectType, Field, String, Boolean, Int, List as GrapheneList
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.core.files.storage import default_storage, Storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import models
from django.utils.text import slugify

try:
    from PIL import Image, ImageOps, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

from ..core.settings import GraphQLAutoSettings


class MediaProcessingError(Exception):
    """Exception levée lors du traitement des médias."""
    pass


class ThumbnailSize(graphene.ObjectType):
    """Taille de miniature disponible."""
    
    name = graphene.String(description="Nom de la taille")
    width = graphene.Int(description="Largeur en pixels")
    height = graphene.Int(description="Hauteur en pixels")
    quality = graphene.Int(description="Qualité de compression (1-100)")


class MediaInfo(graphene.ObjectType):
    """Informations détaillées sur un média."""
    
    id = graphene.String(description="Identifiant unique du média")
    name = graphene.String(description="Nom original du fichier")
    size = graphene.Int(description="Taille du fichier en octets")
    content_type = graphene.String(description="Type MIME du fichier")
    url = graphene.String(description="URL d'accès au fichier original")
    cdn_url = graphene.String(description="URL CDN du fichier")
    path = graphene.String(description="Chemin de stockage du fichier")
    checksum = graphene.String(description="Somme de contrôle MD5 du fichier")
    uploaded_at = graphene.DateTime(description="Date et heure de téléchargement")
    
    # Informations spécifiques aux images
    width = graphene.Int(description="Largeur de l'image en pixels")
    height = graphene.Int(description="Hauteur de l'image en pixels")
    format = graphene.String(description="Format de l'image (JPEG, PNG, etc.)")
    
    # Miniatures disponibles
    thumbnails = graphene.List(
        lambda: ThumbnailInfo,
        description="Liste des miniatures générées"
    )


class ThumbnailInfo(graphene.ObjectType):
    """Informations sur une miniature."""
    
    size_name = graphene.String(description="Nom de la taille de miniature")
    width = graphene.Int(description="Largeur en pixels")
    height = graphene.Int(description="Hauteur en pixels")
    url = graphene.String(description="URL d'accès à la miniature")
    cdn_url = graphene.String(description="URL CDN de la miniature")
    file_size = graphene.Int(description="Taille du fichier en octets")


class StorageBackend:
    """Classe de base pour les backends de stockage."""
    
    def save(self, name: str, content: ContentFile) -> str:
        """
        Sauvegarde un fichier.
        
        Args:
            name: Nom du fichier
            content: Contenu du fichier
            
        Returns:
            str: Chemin du fichier sauvegardé
        """
        raise NotImplementedError
    
    def url(self, name: str) -> str:
        """
        Génère l'URL d'accès au fichier.
        
        Args:
            name: Nom du fichier
            
        Returns:
            str: URL d'accès au fichier
        """
        raise NotImplementedError
    
    def delete(self, name: str) -> bool:
        """
        Supprime un fichier.
        
        Args:
            name: Nom du fichier
            
        Returns:
            bool: True si la suppression a réussi
        """
        raise NotImplementedError
    
    def exists(self, name: str) -> bool:
        """
        Vérifie si un fichier existe.
        
        Args:
            name: Nom du fichier
            
        Returns:
            bool: True si le fichier existe
        """
        raise NotImplementedError


class LocalStorageBackend(StorageBackend):
    """Backend de stockage local utilisant le système de fichiers."""
    
    def __init__(self, settings: GraphQLAutoSettings):
        self.settings = settings
        self.storage = default_storage
    
    def save(self, name: str, content: ContentFile) -> str:
        """Sauvegarde un fichier localement."""
        return self.storage.save(name, content)
    
    def url(self, name: str) -> str:
        """Génère l'URL locale du fichier."""
        return self.storage.url(name)
    
    def delete(self, name: str) -> bool:
        """Supprime un fichier local."""
        try:
            self.storage.delete(name)
            return True
        except Exception:
            return False
    
    def exists(self, name: str) -> bool:
        """Vérifie si un fichier local existe."""
        return self.storage.exists(name)


class S3StorageBackend(StorageBackend):
    """Backend de stockage Amazon S3."""
    
    def __init__(self, settings: GraphQLAutoSettings):
        if not BOTO3_AVAILABLE:
            raise MediaProcessingError("boto3 n'est pas installé. Installez-le avec: pip install boto3")
        
        self.settings = settings
        self.bucket_name = getattr(settings, 'AWS_S3_BUCKET_NAME', None)
        self.region = getattr(settings, 'AWS_S3_REGION', 'us-east-1')
        self.access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
        self.secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        
        if not all([self.bucket_name, self.access_key, self.secret_key]):
            raise MediaProcessingError("Configuration S3 incomplète")
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )
    
    def save(self, name: str, content: ContentFile) -> str:
        """Sauvegarde un fichier sur S3."""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=name,
                Body=content.read(),
                ContentType=getattr(content, 'content_type', 'application/octet-stream')
            )
            return name
        except ClientError as e:
            raise MediaProcessingError(f"Erreur lors de la sauvegarde S3: {e}")
    
    def url(self, name: str) -> str:
        """Génère l'URL S3 du fichier."""
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{name}"
    
    def delete(self, name: str) -> bool:
        """Supprime un fichier S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=name)
            return True
        except ClientError:
            return False
    
    def exists(self, name: str) -> bool:
        """Vérifie si un fichier S3 existe."""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=name)
            return True
        except ClientError:
            return False


class CDNManager:
    """Gestionnaire d'intégration CDN."""
    
    def __init__(self, settings: GraphQLAutoSettings):
        self.settings = settings
        self.cdn_base_url = getattr(settings, 'CDN_BASE_URL', None)
        self.cdn_enabled = getattr(settings, 'CDN_ENABLED', False)
    
    def get_cdn_url(self, file_path: str) -> Optional[str]:
        """
        Génère l'URL CDN pour un fichier.
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            Optional[str]: URL CDN ou None si CDN désactivé
        """
        if not self.cdn_enabled or not self.cdn_base_url:
            return None
        
        return urljoin(self.cdn_base_url.rstrip('/') + '/', file_path.lstrip('/'))
    
    def purge_cache(self, file_paths: List[str]) -> bool:
        """
        Purge le cache CDN pour les fichiers spécifiés.
        
        Args:
            file_paths: Liste des chemins de fichiers à purger
            
        Returns:
            bool: True si la purge a réussi
        """
        # Implémentation spécifique au CDN utilisé
        # Exemple pour CloudFlare, AWS CloudFront, etc.
        return True


class ImageProcessor:
    """Processeur d'images avec génération de miniatures."""
    
    def __init__(self, settings: GraphQLAutoSettings):
        if not PIL_AVAILABLE:
            raise MediaProcessingError("Pillow n'est pas installé. Installez-le avec: pip install Pillow")
        
        self.settings = settings
        self.thumbnail_sizes = getattr(settings, 'THUMBNAIL_SIZES', {
            'small': {'width': 150, 'height': 150, 'quality': 85},
            'medium': {'width': 300, 'height': 300, 'quality': 85},
            'large': {'width': 800, 'height': 600, 'quality': 90},
        })
        self.optimize_images = getattr(settings, 'OPTIMIZE_IMAGES', True)
        self.progressive_jpeg = getattr(settings, 'PROGRESSIVE_JPEG', True)
    
    def is_image(self, file: Union[InMemoryUploadedFile, TemporaryUploadedFile]) -> bool:
        """
        Vérifie si un fichier est une image.
        
        Args:
            file: Fichier à vérifier
            
        Returns:
            bool: True si c'est une image
        """
        try:
            with Image.open(file) as img:
                img.verify()
            file.seek(0)  # Reset file pointer
            return True
        except Exception:
            return False
    
    def get_image_info(self, file: Union[InMemoryUploadedFile, TemporaryUploadedFile]) -> Dict[str, Any]:
        """
        Extrait les informations d'une image.
        
        Args:
            file: Fichier image
            
        Returns:
            Dict[str, Any]: Informations sur l'image
        """
        try:
            with Image.open(file) as img:
                info = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                }
            file.seek(0)
            return info
        except Exception as e:
            raise MediaProcessingError(f"Erreur lors de l'analyse de l'image: {e}")
    
    def optimize_image(self, image: Image.Image, format: str = 'JPEG', quality: int = 85) -> io.BytesIO:
        """
        Optimise une image.
        
        Args:
            image: Image PIL à optimiser
            format: Format de sortie
            quality: Qualité de compression
            
        Returns:
            io.BytesIO: Image optimisée
        """
        output = io.BytesIO()
        
        # Conversion en RGB si nécessaire pour JPEG
        if format == 'JPEG' and image.mode in ('RGBA', 'LA', 'P'):
            # Créer un fond blanc pour les images avec transparence
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Options de sauvegarde
        save_kwargs = {
            'format': format,
            'quality': quality,
            'optimize': self.optimize_images
        }
        
        if format == 'JPEG' and self.progressive_jpeg:
            save_kwargs['progressive'] = True
        
        image.save(output, **save_kwargs)
        output.seek(0)
        return output
    
    def generate_thumbnail(self, image: Image.Image, size_config: Dict[str, Any]) -> io.BytesIO:
        """
        Génère une miniature.
        
        Args:
            image: Image source
            size_config: Configuration de la taille
            
        Returns:
            io.BytesIO: Miniature générée
        """
        width = size_config['width']
        height = size_config['height']
        quality = size_config.get('quality', 85)
        
        # Redimensionnement avec conservation des proportions
        thumbnail = image.copy()
        thumbnail.thumbnail((width, height), Image.Resampling.LANCZOS)
        
        # Centrage sur un canvas de la taille exacte demandée
        if thumbnail.size != (width, height):
            canvas = Image.new('RGB', (width, height), (255, 255, 255))
            offset = ((width - thumbnail.width) // 2, (height - thumbnail.height) // 2)
            canvas.paste(thumbnail, offset)
            thumbnail = canvas
        
        return self.optimize_image(thumbnail, 'JPEG', quality)
    
    def process_image(self, file: Union[InMemoryUploadedFile, TemporaryUploadedFile]) -> Dict[str, Any]:
        """
        Traite une image et génère ses miniatures.
        
        Args:
            file: Fichier image à traiter
            
        Returns:
            Dict[str, Any]: Informations sur l'image traitée et ses miniatures
        """
        if not self.is_image(file):
            raise MediaProcessingError("Le fichier n'est pas une image valide")
        
        # Informations de base
        image_info = self.get_image_info(file)
        
        # Ouverture de l'image
        with Image.open(file) as img:
            # Correction de l'orientation EXIF
            img = ImageOps.exif_transpose(img)
            
            # Génération des miniatures
            thumbnails = {}
            for size_name, size_config in self.thumbnail_sizes.items():
                thumbnail_data = self.generate_thumbnail(img, size_config)
                thumbnails[size_name] = {
                    'data': thumbnail_data,
                    'width': size_config['width'],
                    'height': size_config['height'],
                    'size': len(thumbnail_data.getvalue())
                }
            
            # Image optimisée originale
            optimized_original = self.optimize_image(img, image_info['format'] or 'JPEG')
        
        file.seek(0)
        
        return {
            'info': image_info,
            'optimized_original': optimized_original,
            'thumbnails': thumbnails
        }


class MediaManager:
    """Gestionnaire principal des médias."""
    
    def __init__(self, settings: GraphQLAutoSettings):
        self.settings = settings
        self.storage_backend = self._get_storage_backend()
        self.cdn_manager = CDNManager(settings)
        self.image_processor = ImageProcessor(settings) if PIL_AVAILABLE else None
        
    def _get_storage_backend(self) -> StorageBackend:
        """
        Sélectionne le backend de stockage approprié.
        
        Returns:
            StorageBackend: Backend de stockage configuré
        """
        backend_type = getattr(self.settings, 'STORAGE_BACKEND', 'local')
        
        if backend_type == 's3':
            return S3StorageBackend(self.settings)
        else:
            return LocalStorageBackend(self.settings)
    
    def generate_media_path(self, filename: str, media_type: str = 'general') -> str:
        """
        Génère un chemin pour un média.
        
        Args:
            filename: Nom du fichier
            media_type: Type de média (image, document, etc.)
            
        Returns:
            str: Chemin généré
        """
        file_extension = Path(filename).suffix.lower()
        unique_name = f"{uuid.uuid4().hex}{file_extension}"
        
        now = datetime.now()
        date_path = f"{now.year}/{now.month:02d}/{now.day:02d}"
        
        return f"media/{media_type}/{date_path}/{unique_name}"
    
    def save_media(self, file: Union[InMemoryUploadedFile, TemporaryUploadedFile]) -> MediaInfo:
        """
        Sauvegarde un média avec traitement automatique.
        
        Args:
            file: Fichier à sauvegarder
            
        Returns:
            MediaInfo: Informations sur le média sauvegardé
        """
        # Détermination du type de média
        is_image = self.image_processor and self.image_processor.is_image(file)
        media_type = 'images' if is_image else 'documents'
        
        # Génération du chemin
        media_path = self.generate_media_path(file.name, media_type)
        
        # Traitement spécifique aux images
        thumbnails = []
        image_info = {}
        
        if is_image:
            processed = self.image_processor.process_image(file)
            image_info = processed['info']
            
            # Sauvegarde de l'image optimisée
            optimized_content = ContentFile(
                processed['optimized_original'].getvalue(),
                name=Path(media_path).name
            )
            saved_path = self.storage_backend.save(media_path, optimized_content)
            
            # Sauvegarde des miniatures
            for size_name, thumb_data in processed['thumbnails'].items():
                thumb_path = media_path.replace(
                    Path(media_path).name,
                    f"thumb_{size_name}_{Path(media_path).name}"
                )
                thumb_content = ContentFile(
                    thumb_data['data'].getvalue(),
                    name=Path(thumb_path).name
                )
                thumb_saved_path = self.storage_backend.save(thumb_path, thumb_content)
                
                thumbnails.append(ThumbnailInfo(
                    size_name=size_name,
                    width=thumb_data['width'],
                    height=thumb_data['height'],
                    url=self.storage_backend.url(thumb_saved_path),
                    cdn_url=self.cdn_manager.get_cdn_url(thumb_saved_path),
                    file_size=thumb_data['size']
                ))
        else:
            # Sauvegarde directe pour les non-images
            content = ContentFile(file.read(), name=Path(media_path).name)
            saved_path = self.storage_backend.save(media_path, content)
            file.seek(0)
        
        # Calcul du checksum
        file.seek(0)
        checksum = hashlib.md5(file.read()).hexdigest()
        file.seek(0)
        
        # URL principale
        main_url = self.storage_backend.url(saved_path)
        cdn_url = self.cdn_manager.get_cdn_url(saved_path)
        
        return MediaInfo(
            id=str(uuid.uuid4()),
            name=file.name,
            size=file.size,
            content_type=file.content_type,
            url=main_url,
            cdn_url=cdn_url,
            path=saved_path,
            checksum=checksum,
            uploaded_at=datetime.now(),
            width=image_info.get('width'),
            height=image_info.get('height'),
            format=image_info.get('format'),
            thumbnails=thumbnails
        )
    
    def delete_media(self, media_path: str) -> bool:
        """
        Supprime un média et ses miniatures.
        
        Args:
            media_path: Chemin du média à supprimer
            
        Returns:
            bool: True si la suppression a réussi
        """
        success = True
        
        # Suppression du fichier principal
        if not self.storage_backend.delete(media_path):
            success = False
        
        # Suppression des miniatures (si c'est une image)
        base_path = Path(media_path)
        for size_name in self.image_processor.thumbnail_sizes.keys() if self.image_processor else []:
            thumb_path = str(base_path.parent / f"thumb_{size_name}_{base_path.name}")
            if self.storage_backend.exists(thumb_path):
                if not self.storage_backend.delete(thumb_path):
                    success = False
        
        # Purge du cache CDN
        if self.cdn_manager.cdn_enabled:
            self.cdn_manager.purge_cache([media_path])
        
        return success