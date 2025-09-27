"""
Tests pour le système de gestion des médias.

Ce module teste :
- Traitement des images
- Génération de miniatures
- Backends de stockage
- Intégration CDN
- Optimisation des médias
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from PIL import Image

from django.test import TestCase
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.models import User
from django.db import models

from django_graphql_auto.extensions.media import (
    MediaManager, ImageProcessor, ThumbnailSize, MediaInfo, ThumbnailInfo,
    StorageBackend, LocalStorageBackend, S3StorageBackend, CDNManager,
    MediaProcessingError
)
from django_graphql_auto.core.settings import GraphQLAutoSettings


class TestMediaModel(models.Model):
    """Modèle de test pour les médias."""
    title = models.CharField(max_length=255, verbose_name="Titre")
    image = models.ImageField(upload_to='test_media/', verbose_name="Image")
    thumbnail = models.ImageField(upload_to='test_thumbnails/', verbose_name="Miniature", blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Propriétaire")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        app_label = 'test_app'


class MediaInfoTest(TestCase):
    """Tests pour la classe MediaInfo."""
    
    def test_media_info_creation(self):
        """Test de création d'un objet MediaInfo."""
        media_info = MediaInfo(
            filename="test.jpg",
            original_filename="original_test.jpg",
            file_size=1024,
            content_type="image/jpeg",
            width=800,
            height=600,
            url="/media/test.jpg"
        )
        
        self.assertEqual(media_info.filename, "test.jpg")
        self.assertEqual(media_info.original_filename, "original_test.jpg")
        self.assertEqual(media_info.file_size, 1024)
        self.assertEqual(media_info.content_type, "image/jpeg")
        self.assertEqual(media_info.width, 800)
        self.assertEqual(media_info.height, 600)
        self.assertEqual(media_info.url, "/media/test.jpg")
    
    def test_media_info_aspect_ratio(self):
        """Test du calcul du ratio d'aspect."""
        media_info = MediaInfo(
            filename="test.jpg",
            width=800,
            height=600
        )
        
        expected_ratio = 800 / 600
        self.assertAlmostEqual(media_info.aspect_ratio, expected_ratio, places=2)
    
    def test_media_info_is_landscape(self):
        """Test de détection du format paysage."""
        landscape_info = MediaInfo(filename="test.jpg", width=800, height=600)
        portrait_info = MediaInfo(filename="test.jpg", width=600, height=800)
        square_info = MediaInfo(filename="test.jpg", width=600, height=600)
        
        self.assertTrue(landscape_info.is_landscape)
        self.assertFalse(portrait_info.is_landscape)
        self.assertFalse(square_info.is_landscape)
    
    def test_media_info_is_portrait(self):
        """Test de détection du format portrait."""
        landscape_info = MediaInfo(filename="test.jpg", width=800, height=600)
        portrait_info = MediaInfo(filename="test.jpg", width=600, height=800)
        square_info = MediaInfo(filename="test.jpg", width=600, height=600)
        
        self.assertFalse(landscape_info.is_portrait)
        self.assertTrue(portrait_info.is_portrait)
        self.assertFalse(square_info.is_portrait)


class ThumbnailInfoTest(TestCase):
    """Tests pour la classe ThumbnailInfo."""
    
    def test_thumbnail_info_creation(self):
        """Test de création d'un objet ThumbnailInfo."""
        thumbnail_info = ThumbnailInfo(
            size=ThumbnailSize.MEDIUM,
            filename="thumb_medium_test.jpg",
            width=300,
            height=200,
            url="/media/thumbs/thumb_medium_test.jpg"
        )
        
        self.assertEqual(thumbnail_info.size, ThumbnailSize.MEDIUM)
        self.assertEqual(thumbnail_info.filename, "thumb_medium_test.jpg")
        self.assertEqual(thumbnail_info.width, 300)
        self.assertEqual(thumbnail_info.height, 200)
        self.assertEqual(thumbnail_info.url, "/media/thumbs/thumb_medium_test.jpg")


class ImageProcessorTest(TestCase):
    """Tests pour la classe ImageProcessor."""
    
    def setUp(self):
        """Configuration des tests."""
        self.settings = GraphQLAutoSettings()
        self.processor = ImageProcessor(self.settings)
    
    def _create_test_image(self, width=800, height=600, format='JPEG'):
        """Crée une image de test."""
        image = Image.new('RGB', (width, height), color='red')
        image_bytes = BytesIO()
        image.save(image_bytes, format=format)
        image_bytes.seek(0)
        
        return InMemoryUploadedFile(
            file=image_bytes,
            field_name='image',
            name=f'test.{format.lower()}',
            content_type=f'image/{format.lower()}',
            size=len(image_bytes.getvalue()),
            charset=None
        )
    
    def test_resize_image_proportional(self):
        """Test de redimensionnement proportionnel d'image."""
        uploaded_file = self._create_test_image(800, 600)
        
        resized_file = self.processor.resize_image(uploaded_file, max_width=400, max_height=300)
        
        # Vérification des nouvelles dimensions
        resized_image = Image.open(resized_file)
        self.assertEqual(resized_image.width, 400)
        self.assertEqual(resized_image.height, 300)
    
    def test_resize_image_no_upscaling(self):
        """Test que le redimensionnement ne fait pas d'agrandissement."""
        uploaded_file = self._create_test_image(400, 300)
        
        resized_file = self.processor.resize_image(uploaded_file, max_width=800, max_height=600)
        
        # L'image ne doit pas être agrandie
        resized_image = Image.open(resized_file)
        self.assertEqual(resized_image.width, 400)
        self.assertEqual(resized_image.height, 300)
    
    def test_optimize_image_quality(self):
        """Test d'optimisation de la qualité d'image."""
        uploaded_file = self._create_test_image(800, 600)
        original_size = uploaded_file.size
        
        optimized_file = self.processor.optimize_image(uploaded_file, quality=50)
        
        # L'image optimisée devrait être plus petite
        self.assertLess(optimized_file.size, original_size)
    
    def test_convert_format(self):
        """Test de conversion de format d'image."""
        uploaded_file = self._create_test_image(800, 600, 'PNG')
        
        converted_file = self.processor.convert_format(uploaded_file, 'JPEG')
        
        self.assertEqual(converted_file.content_type, 'image/jpeg')
        self.assertTrue(converted_file.name.endswith('.jpg'))
    
    def test_generate_thumbnail_small(self):
        """Test de génération de miniature petite."""
        uploaded_file = self._create_test_image(800, 600)
        
        thumbnail_file = self.processor.generate_thumbnail(uploaded_file, ThumbnailSize.SMALL)
        
        thumbnail_image = Image.open(thumbnail_file)
        self.assertLessEqual(thumbnail_image.width, 150)
        self.assertLessEqual(thumbnail_image.height, 150)
    
    def test_generate_thumbnail_medium(self):
        """Test de génération de miniature moyenne."""
        uploaded_file = self._create_test_image(800, 600)
        
        thumbnail_file = self.processor.generate_thumbnail(uploaded_file, ThumbnailSize.MEDIUM)
        
        thumbnail_image = Image.open(thumbnail_file)
        self.assertLessEqual(thumbnail_image.width, 300)
        self.assertLessEqual(thumbnail_image.height, 300)
    
    def test_generate_thumbnail_large(self):
        """Test de génération de miniature grande."""
        uploaded_file = self._create_test_image(800, 600)
        
        thumbnail_file = self.processor.generate_thumbnail(uploaded_file, ThumbnailSize.LARGE)
        
        thumbnail_image = Image.open(thumbnail_file)
        self.assertLessEqual(thumbnail_image.width, 600)
        self.assertLessEqual(thumbnail_image.height, 600)
    
    def test_generate_all_thumbnails(self):
        """Test de génération de toutes les miniatures."""
        uploaded_file = self._create_test_image(1200, 900)
        
        thumbnails = self.processor.generate_all_thumbnails(uploaded_file)
        
        self.assertEqual(len(thumbnails), 3)  # SMALL, MEDIUM, LARGE
        
        # Vérification que chaque taille est présente
        sizes = [thumb.size for thumb in thumbnails]
        self.assertIn(ThumbnailSize.SMALL, sizes)
        self.assertIn(ThumbnailSize.MEDIUM, sizes)
        self.assertIn(ThumbnailSize.LARGE, sizes)
    
    def test_extract_metadata(self):
        """Test d'extraction des métadonnées d'image."""
        uploaded_file = self._create_test_image(800, 600)
        
        metadata = self.processor.extract_metadata(uploaded_file)
        
        self.assertEqual(metadata['width'], 800)
        self.assertEqual(metadata['height'], 600)
        self.assertEqual(metadata['format'], 'JPEG')
        self.assertIn('file_size', metadata)
    
    def test_process_invalid_image(self):
        """Test de traitement d'un fichier non-image."""
        # Création d'un fichier texte
        content = b"This is not an image"
        uploaded_file = InMemoryUploadedFile(
            file=BytesIO(content),
            field_name='file',
            name='not_image.txt',
            content_type='text/plain',
            size=len(content),
            charset=None
        )
        
        with self.assertRaises(MediaProcessingError):
            self.processor.resize_image(uploaded_file, max_width=400, max_height=300)


class LocalStorageBackendTest(TestCase):
    """Tests pour le backend de stockage local."""
    
    def setUp(self):
        """Configuration des tests."""
        self.settings = GraphQLAutoSettings()
        self.backend = LocalStorageBackend(self.settings)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Nettoyage après les tests."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_save_file(self):
        """Test de sauvegarde de fichier."""
        content = b"Test file content"
        uploaded_file = InMemoryUploadedFile(
            file=BytesIO(content),
            field_name='file',
            name='test.txt',
            content_type='text/plain',
            size=len(content),
            charset=None
        )
        
        with patch('django.core.files.storage.default_storage') as mock_storage:
            mock_storage.save.return_value = 'saved_test.txt'
            mock_storage.url.return_value = '/media/saved_test.txt'
            
            filename = self.backend.save_file(uploaded_file, 'test_folder/')
            
            self.assertEqual(filename, 'saved_test.txt')
            mock_storage.save.assert_called_once()
    
    def test_delete_file(self):
        """Test de suppression de fichier."""
        with patch('django.core.files.storage.default_storage') as mock_storage:
            mock_storage.exists.return_value = True
            mock_storage.delete.return_value = None
            
            result = self.backend.delete_file('test.txt')
            
            self.assertTrue(result)
            mock_storage.delete.assert_called_once_with('test.txt')
    
    def test_get_file_url(self):
        """Test de récupération d'URL de fichier."""
        with patch('django.core.files.storage.default_storage') as mock_storage:
            mock_storage.url.return_value = '/media/test.txt'
            
            url = self.backend.get_file_url('test.txt')
            
            self.assertEqual(url, '/media/test.txt')
            mock_storage.url.assert_called_once_with('test.txt')
    
    def test_file_exists(self):
        """Test de vérification d'existence de fichier."""
        with patch('django.core.files.storage.default_storage') as mock_storage:
            mock_storage.exists.return_value = True
            
            exists = self.backend.file_exists('test.txt')
            
            self.assertTrue(exists)
            mock_storage.exists.assert_called_once_with('test.txt')


class S3StorageBackendTest(TestCase):
    """Tests pour le backend de stockage S3."""
    
    def setUp(self):
        """Configuration des tests."""
        self.settings = GraphQLAutoSettings()
        self.settings.AWS_ACCESS_KEY_ID = 'test_key'
        self.settings.AWS_SECRET_ACCESS_KEY = 'test_secret'
        self.settings.AWS_STORAGE_BUCKET_NAME = 'test-bucket'
        self.settings.AWS_S3_REGION_NAME = 'us-east-1'
        
        self.backend = S3StorageBackend(self.settings)
    
    @patch('boto3.client')
    def test_save_file_to_s3(self, mock_boto_client):
        """Test de sauvegarde de fichier sur S3."""
        # Configuration du mock S3
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        content = b"Test file content"
        uploaded_file = InMemoryUploadedFile(
            file=BytesIO(content),
            field_name='file',
            name='test.txt',
            content_type='text/plain',
            size=len(content),
            charset=None
        )
        
        filename = self.backend.save_file(uploaded_file, 'test_folder/')
        
        # Vérification que le fichier a été uploadé
        mock_s3.upload_fileobj.assert_called_once()
        self.assertTrue(filename.startswith('test_folder/'))
        self.assertTrue(filename.endswith('.txt'))
    
    @patch('boto3.client')
    def test_delete_file_from_s3(self, mock_boto_client):
        """Test de suppression de fichier sur S3."""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        result = self.backend.delete_file('test.txt')
        
        mock_s3.delete_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test.txt'
        )
        self.assertTrue(result)
    
    @patch('boto3.client')
    def test_get_file_url_from_s3(self, mock_boto_client):
        """Test de récupération d'URL de fichier sur S3."""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        url = self.backend.get_file_url('test.txt')
        
        expected_url = f"https://{self.settings.AWS_STORAGE_BUCKET_NAME}.s3.{self.settings.AWS_S3_REGION_NAME}.amazonaws.com/test.txt"
        self.assertEqual(url, expected_url)
    
    @patch('boto3.client')
    def test_file_exists_on_s3(self, mock_boto_client):
        """Test de vérification d'existence de fichier sur S3."""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_object.return_value = {'ContentLength': 1024}
        
        exists = self.backend.file_exists('test.txt')
        
        mock_s3.head_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test.txt'
        )
        self.assertTrue(exists)


class CDNManagerTest(TestCase):
    """Tests pour le gestionnaire CDN."""
    
    def setUp(self):
        """Configuration des tests."""
        self.settings = GraphQLAutoSettings()
        self.settings.CDN_ENABLED = True
        self.settings.CDN_BASE_URL = 'https://cdn.example.com'
        self.cdn_manager = CDNManager(self.settings)
    
    def test_get_cdn_url(self):
        """Test de génération d'URL CDN."""
        file_path = 'images/test.jpg'
        cdn_url = self.cdn_manager.get_cdn_url(file_path)
        
        expected_url = 'https://cdn.example.com/images/test.jpg'
        self.assertEqual(cdn_url, expected_url)
    
    def test_get_cdn_url_disabled(self):
        """Test avec CDN désactivé."""
        self.settings.CDN_ENABLED = False
        cdn_manager = CDNManager(self.settings)
        
        file_path = 'images/test.jpg'
        cdn_url = cdn_manager.get_cdn_url(file_path)
        
        # Devrait retourner le chemin original
        self.assertEqual(cdn_url, file_path)
    
    def test_invalidate_cache(self):
        """Test d'invalidation du cache CDN."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            
            result = self.cdn_manager.invalidate_cache(['images/test.jpg'])
            
            self.assertTrue(result)
    
    def test_get_optimized_url(self):
        """Test de génération d'URL optimisée."""
        file_path = 'images/test.jpg'
        optimized_url = self.cdn_manager.get_optimized_url(
            file_path, 
            width=300, 
            height=200, 
            quality=80
        )
        
        self.assertIn('w=300', optimized_url)
        self.assertIn('h=200', optimized_url)
        self.assertIn('q=80', optimized_url)


class MediaManagerTest(TestCase):
    """Tests pour le gestionnaire de médias."""
    
    def setUp(self):
        """Configuration des tests."""
        self.settings = GraphQLAutoSettings()
        self.media_manager = MediaManager(self.settings)
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def _create_test_image(self, width=800, height=600):
        """Crée une image de test."""
        image = Image.new('RGB', (width, height), color='blue')
        image_bytes = BytesIO()
        image.save(image_bytes, format='JPEG')
        image_bytes.seek(0)
        
        return InMemoryUploadedFile(
            file=image_bytes,
            field_name='image',
            name='test.jpg',
            content_type='image/jpeg',
            size=len(image_bytes.getvalue()),
            charset=None
        )
    
    @patch('django_graphql_auto.extensions.media.LocalStorageBackend')
    def test_process_and_save_image(self, mock_storage_backend):
        """Test de traitement et sauvegarde d'image."""
        # Configuration du mock storage
        mock_backend = Mock()
        mock_backend.save_file.return_value = 'saved_image.jpg'
        mock_backend.get_file_url.return_value = '/media/saved_image.jpg'
        mock_storage_backend.return_value = mock_backend
        
        uploaded_file = self._create_test_image(1200, 900)
        
        media_info = self.media_manager.process_and_save_image(
            uploaded_file,
            resize_options={'max_width': 800, 'max_height': 600},
            generate_thumbnails=True
        )
        
        self.assertIsInstance(media_info, MediaInfo)
        self.assertEqual(media_info.filename, 'saved_image.jpg')
        self.assertEqual(media_info.url, '/media/saved_image.jpg')
        self.assertGreater(len(media_info.thumbnails), 0)
    
    @patch('django_graphql_auto.extensions.media.LocalStorageBackend')
    def test_delete_media(self, mock_storage_backend):
        """Test de suppression de média."""
        mock_backend = Mock()
        mock_backend.delete_file.return_value = True
        mock_storage_backend.return_value = mock_backend
        
        media_info = MediaInfo(
            filename='test.jpg',
            url='/media/test.jpg',
            thumbnails=[
                ThumbnailInfo(
                    size=ThumbnailSize.SMALL,
                    filename='thumb_small_test.jpg',
                    width=150,
                    height=150,
                    url='/media/thumbs/thumb_small_test.jpg'
                )
            ]
        )
        
        result = self.media_manager.delete_media(media_info)
        
        self.assertTrue(result)
        # Vérification que le fichier principal et les miniatures ont été supprimés
        self.assertEqual(mock_backend.delete_file.call_count, 2)
    
    def test_get_media_info(self):
        """Test de récupération d'informations de média."""
        uploaded_file = self._create_test_image(800, 600)
        
        media_info = self.media_manager.get_media_info(uploaded_file)
        
        self.assertEqual(media_info.width, 800)
        self.assertEqual(media_info.height, 600)
        self.assertEqual(media_info.content_type, 'image/jpeg')
        self.assertTrue(media_info.is_landscape)
    
    def test_optimize_existing_media(self):
        """Test d'optimisation de média existant."""
        with patch('django_graphql_auto.extensions.media.LocalStorageBackend') as mock_storage_backend:
            mock_backend = Mock()
            mock_backend.file_exists.return_value = True
            mock_backend.save_file.return_value = 'optimized_image.jpg'
            mock_backend.get_file_url.return_value = '/media/optimized_image.jpg'
            mock_storage_backend.return_value = mock_backend
            
            # Mock pour simuler la lecture du fichier existant
            with patch('django.core.files.storage.default_storage.open') as mock_open:
                mock_file = Mock()
                mock_file.read.return_value = self._create_test_image().read()
                mock_open.return_value = mock_file
                
                result = self.media_manager.optimize_existing_media(
                    'original_image.jpg',
                    quality=70,
                    max_width=600,
                    max_height=400
                )
                
                self.assertTrue(result)


class MediaIntegrationTest(TestCase):
    """Tests d'intégration pour le système de gestion des médias."""
    
    def setUp(self):
        """Configuration des tests d'intégration."""
        self.settings = GraphQLAutoSettings()
        self.media_manager = MediaManager(self.settings)
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def _create_test_image(self, width=800, height=600):
        """Crée une image de test."""
        image = Image.new('RGB', (width, height), color='green')
        image_bytes = BytesIO()
        image.save(image_bytes, format='JPEG')
        image_bytes.seek(0)
        
        return InMemoryUploadedFile(
            file=image_bytes,
            field_name='image',
            name='integration_test.jpg',
            content_type='image/jpeg',
            size=len(image_bytes.getvalue()),
            charset=None
        )
    
    @patch('django_graphql_auto.extensions.media.LocalStorageBackend')
    @patch('django_graphql_auto.extensions.media.CDNManager')
    def test_complete_media_workflow(self, mock_cdn_manager, mock_storage_backend):
        """Test du workflow complet de gestion des médias."""
        # Configuration des mocks
        mock_backend = Mock()
        mock_backend.save_file.return_value = 'workflow_test.jpg'
        mock_backend.get_file_url.return_value = '/media/workflow_test.jpg'
        mock_storage_backend.return_value = mock_backend
        
        mock_cdn = Mock()
        mock_cdn.get_cdn_url.return_value = 'https://cdn.example.com/workflow_test.jpg'
        mock_cdn_manager.return_value = mock_cdn
        
        # 1. Téléchargement et traitement de l'image
        uploaded_file = self._create_test_image(1200, 900)
        
        media_info = self.media_manager.process_and_save_image(
            uploaded_file,
            resize_options={'max_width': 800, 'max_height': 600},
            generate_thumbnails=True,
            optimize_quality=80
        )
        
        # 2. Vérification du résultat
        self.assertIsInstance(media_info, MediaInfo)
        self.assertEqual(media_info.filename, 'workflow_test.jpg')
        self.assertGreater(len(media_info.thumbnails), 0)
        
        # 3. Vérification que les miniatures ont été générées
        thumbnail_sizes = [thumb.size for thumb in media_info.thumbnails]
        self.assertIn(ThumbnailSize.SMALL, thumbnail_sizes)
        self.assertIn(ThumbnailSize.MEDIUM, thumbnail_sizes)
        self.assertIn(ThumbnailSize.LARGE, thumbnail_sizes)
        
        # 4. Vérification des appels aux backends
        mock_backend.save_file.assert_called()  # Au moins une fois pour l'image principale
    
    def test_media_processing_error_handling(self):
        """Test de gestion des erreurs de traitement des médias."""
        # Création d'un fichier corrompu
        content = b"This is not a valid image"
        uploaded_file = InMemoryUploadedFile(
            file=BytesIO(content),
            field_name='image',
            name='corrupted.jpg',
            content_type='image/jpeg',
            size=len(content),
            charset=None
        )
        
        with self.assertRaises(MediaProcessingError):
            self.media_manager.process_and_save_image(uploaded_file)
    
    @patch('django_graphql_auto.extensions.media.LocalStorageBackend')
    def test_batch_thumbnail_generation(self, mock_storage_backend):
        """Test de génération de miniatures en lot."""
        mock_backend = Mock()
        mock_backend.save_file.return_value = 'batch_test.jpg'
        mock_backend.get_file_url.return_value = '/media/batch_test.jpg'
        mock_storage_backend.return_value = mock_backend
        
        # Création de plusieurs images de test
        images = []
        for i in range(3):
            image = self._create_test_image(800 + i*100, 600 + i*100)
            image.name = f'batch_test_{i}.jpg'
            images.append(image)
        
        results = []
        for image in images:
            media_info = self.media_manager.process_and_save_image(
                image,
                generate_thumbnails=True
            )
            results.append(media_info)
        
        # Vérification que toutes les images ont été traitées
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, MediaInfo)
            self.assertGreater(len(result.thumbnails), 0)


if __name__ == '__main__':
    pytest.main([__file__])