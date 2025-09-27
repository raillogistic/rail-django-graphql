"""
Tests pour le système de téléchargement de fichiers.

Ce module teste :
- Génération des mutations de téléchargement
- Validation des fichiers
- Sécurité des téléchargements
- Traitement des fichiers
- Gestion des erreurs
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from PIL import Image

from django.test import TestCase
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.contrib.auth.models import User
from django.db import models

from django_graphql_auto.generators.file_uploads import (
    FileUploadGenerator, FileInfo, FileUploadResult, MultipleFileUploadResult,
    FileValidator, FileProcessor, FileUploadError, FileValidationError,
    FileProcessingError
)
from django_graphql_auto.extensions.virus_scanner import (
    VirusScanner, ScanResult, ThreatDetected, VirusScanError
)
from django_graphql_auto.core.settings import GraphQLAutoSettings


class TestFileModel(models.Model):
    """Modèle de test pour les fichiers."""
    name = models.CharField(max_length=255, verbose_name="Nom du fichier")
    file = models.FileField(upload_to='test_files/', verbose_name="Fichier")
    image = models.ImageField(upload_to='test_images/', verbose_name="Image", blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Propriétaire")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        app_label = 'test_app'


class FileInfoTest(TestCase):
    """Tests pour la classe FileInfo."""
    
    def test_file_info_creation(self):
        """Test de création d'un objet FileInfo."""
        file_info = FileInfo(
            name="test.txt",
            size=1024,
            content_type="text/plain",
            extension=".txt"
        )
        
        self.assertEqual(file_info.name, "test.txt")
        self.assertEqual(file_info.size, 1024)
        self.assertEqual(file_info.content_type, "text/plain")
        self.assertEqual(file_info.extension, ".txt")
    
    def test_file_info_from_uploaded_file(self):
        """Test de création d'un FileInfo depuis un fichier téléchargé."""
        # Création d'un fichier en mémoire
        content = b"Test file content"
        uploaded_file = InMemoryUploadedFile(
            file=BytesIO(content),
            field_name='file',
            name='test.txt',
            content_type='text/plain',
            size=len(content),
            charset=None
        )
        
        file_info = FileInfo.from_uploaded_file(uploaded_file)
        
        self.assertEqual(file_info.name, "test.txt")
        self.assertEqual(file_info.size, len(content))
        self.assertEqual(file_info.content_type, "text/plain")
        self.assertEqual(file_info.extension, ".txt")


class FileValidatorTest(TestCase):
    """Tests pour la classe FileValidator."""
    
    def setUp(self):
        """Configuration des tests."""
        self.settings = GraphQLAutoSettings()
        self.validator = FileValidator(self.settings)
    
    def test_validate_file_size_valid(self):
        """Test de validation de taille de fichier valide."""
        file_info = FileInfo(
            name="test.txt",
            size=1024,  # 1KB
            content_type="text/plain",
            extension=".txt"
        )
        
        # Ne doit pas lever d'exception
        self.validator.validate_file_size(file_info, max_size=2048)
    
    def test_validate_file_size_invalid(self):
        """Test de validation de taille de fichier invalide."""
        file_info = FileInfo(
            name="test.txt",
            size=2048,  # 2KB
            content_type="text/plain",
            extension=".txt"
        )
        
        with self.assertRaises(FileValidationError) as context:
            self.validator.validate_file_size(file_info, max_size=1024)
        
        self.assertIn("trop volumineux", str(context.exception))
    
    def test_validate_file_type_valid(self):
        """Test de validation de type de fichier valide."""
        file_info = FileInfo(
            name="test.txt",
            size=1024,
            content_type="text/plain",
            extension=".txt"
        )
        
        allowed_types = ['text/plain', 'text/html']
        
        # Ne doit pas lever d'exception
        self.validator.validate_file_type(file_info, allowed_types)
    
    def test_validate_file_type_invalid(self):
        """Test de validation de type de fichier invalide."""
        file_info = FileInfo(
            name="test.exe",
            size=1024,
            content_type="application/x-executable",
            extension=".exe"
        )
        
        allowed_types = ['text/plain', 'image/jpeg']
        
        with self.assertRaises(FileValidationError) as context:
            self.validator.validate_file_type(file_info, allowed_types)
        
        self.assertIn("type de fichier non autorisé", str(context.exception))
    
    def test_validate_file_extension_valid(self):
        """Test de validation d'extension de fichier valide."""
        file_info = FileInfo(
            name="test.jpg",
            size=1024,
            content_type="image/jpeg",
            extension=".jpg"
        )
        
        allowed_extensions = ['.jpg', '.png', '.gif']
        
        # Ne doit pas lever d'exception
        self.validator.validate_file_extension(file_info, allowed_extensions)
    
    def test_validate_file_extension_invalid(self):
        """Test de validation d'extension de fichier invalide."""
        file_info = FileInfo(
            name="test.exe",
            size=1024,
            content_type="application/x-executable",
            extension=".exe"
        )
        
        allowed_extensions = ['.jpg', '.png', '.gif']
        
        with self.assertRaises(FileValidationError) as context:
            self.validator.validate_file_extension(file_info, allowed_extensions)
        
        self.assertIn("extension de fichier non autorisée", str(context.exception))
    
    def test_validate_image_dimensions_valid(self):
        """Test de validation des dimensions d'image valides."""
        # Création d'une image de test
        image = Image.new('RGB', (800, 600), color='red')
        image_bytes = BytesIO()
        image.save(image_bytes, format='JPEG')
        image_bytes.seek(0)
        
        uploaded_file = InMemoryUploadedFile(
            file=image_bytes,
            field_name='image',
            name='test.jpg',
            content_type='image/jpeg',
            size=len(image_bytes.getvalue()),
            charset=None
        )
        
        # Ne doit pas lever d'exception
        self.validator.validate_image_dimensions(
            uploaded_file, 
            max_width=1024, 
            max_height=768
        )
    
    def test_validate_image_dimensions_invalid(self):
        """Test de validation des dimensions d'image invalides."""
        # Création d'une image de test trop grande
        image = Image.new('RGB', (2000, 1500), color='red')
        image_bytes = BytesIO()
        image.save(image_bytes, format='JPEG')
        image_bytes.seek(0)
        
        uploaded_file = InMemoryUploadedFile(
            file=image_bytes,
            field_name='image',
            name='test.jpg',
            content_type='image/jpeg',
            size=len(image_bytes.getvalue()),
            charset=None
        )
        
        with self.assertRaises(FileValidationError) as context:
            self.validator.validate_image_dimensions(
                uploaded_file, 
                max_width=1024, 
                max_height=768
            )
        
        self.assertIn("dimensions de l'image", str(context.exception))


class FileProcessorTest(TestCase):
    """Tests pour la classe FileProcessor."""
    
    def setUp(self):
        """Configuration des tests."""
        self.settings = GraphQLAutoSettings()
        self.processor = FileProcessor(self.settings)
    
    def test_generate_unique_filename(self):
        """Test de génération de nom de fichier unique."""
        original_name = "test.txt"
        unique_name = self.processor.generate_unique_filename(original_name)
        
        self.assertNotEqual(unique_name, original_name)
        self.assertTrue(unique_name.endswith('.txt'))
        self.assertTrue(len(unique_name) > len(original_name))
    
    def test_sanitize_filename(self):
        """Test de nettoyage de nom de fichier."""
        dangerous_name = "../../../etc/passwd"
        safe_name = self.processor.sanitize_filename(dangerous_name)
        
        self.assertNotIn('..', safe_name)
        self.assertNotIn('/', safe_name)
        self.assertNotIn('\\', safe_name)
    
    def test_optimize_image(self):
        """Test d'optimisation d'image."""
        # Création d'une image de test
        image = Image.new('RGB', (1000, 800), color='blue')
        image_bytes = BytesIO()
        image.save(image_bytes, format='JPEG', quality=100)
        image_bytes.seek(0)
        
        uploaded_file = InMemoryUploadedFile(
            file=image_bytes,
            field_name='image',
            name='test.jpg',
            content_type='image/jpeg',
            size=len(image_bytes.getvalue()),
            charset=None
        )
        
        original_size = uploaded_file.size
        optimized_file = self.processor.optimize_image(uploaded_file, quality=80)
        
        # L'image optimisée devrait être plus petite
        self.assertLess(optimized_file.size, original_size)
        self.assertEqual(optimized_file.content_type, 'image/jpeg')
    
    def test_resize_image(self):
        """Test de redimensionnement d'image."""
        # Création d'une image de test
        image = Image.new('RGB', (1000, 800), color='green')
        image_bytes = BytesIO()
        image.save(image_bytes, format='JPEG')
        image_bytes.seek(0)
        
        uploaded_file = InMemoryUploadedFile(
            file=image_bytes,
            field_name='image',
            name='test.jpg',
            content_type='image/jpeg',
            size=len(image_bytes.getvalue()),
            charset=None
        )
        
        resized_file = self.processor.resize_image(uploaded_file, max_width=500, max_height=400)
        
        # Vérification des nouvelles dimensions
        resized_image = Image.open(resized_file)
        self.assertLessEqual(resized_image.width, 500)
        self.assertLessEqual(resized_image.height, 400)


class VirusScannerTest(TestCase):
    """Tests pour le scanner antivirus."""
    
    def setUp(self):
        """Configuration des tests."""
        self.settings = GraphQLAutoSettings()
        # Configuration pour utiliser le scanner factice
        self.settings.VIRUS_SCANNER_TYPE = 'mock'
        self.settings.MOCK_SCANNER_SIMULATE_THREATS = True
        self.scanner = VirusScanner(self.settings)
    
    def test_scan_clean_file(self):
        """Test de scan d'un fichier propre."""
        content = b"Clean file content"
        uploaded_file = InMemoryUploadedFile(
            file=BytesIO(content),
            field_name='file',
            name='clean.txt',
            content_type='text/plain',
            size=len(content),
            charset=None
        )
        
        result = self.scanner.scan_uploaded_file(uploaded_file)
        
        self.assertTrue(result.is_clean)
        self.assertIsNone(result.threat_name)
    
    def test_scan_infected_file(self):
        """Test de scan d'un fichier infecté."""
        content = b"Virus content"
        uploaded_file = InMemoryUploadedFile(
            file=BytesIO(content),
            field_name='file',
            name='virus.txt',  # Le nom contient 'virus' pour déclencher la détection
            content_type='text/plain',
            size=len(content),
            charset=None
        )
        
        with self.assertRaises(ThreatDetected) as context:
            self.scanner.scan_uploaded_file(uploaded_file)
        
        self.assertIn("Menace détectée", str(context.exception))
    
    def test_scanner_disabled(self):
        """Test avec scanner désactivé."""
        self.settings.VIRUS_SCANNING_ENABLED = False
        scanner = VirusScanner(self.settings)
        
        content = b"Any content"
        uploaded_file = InMemoryUploadedFile(
            file=BytesIO(content),
            field_name='file',
            name='virus.txt',
            content_type='text/plain',
            size=len(content),
            charset=None
        )
        
        result = scanner.scan_uploaded_file(uploaded_file)
        
        self.assertTrue(result.is_clean)
        self.assertEqual(result.scanner_version, "Disabled")


class FileUploadGeneratorTest(TestCase):
    """Tests pour le générateur de téléchargement de fichiers."""
    
    def setUp(self):
        """Configuration des tests."""
        self.settings = GraphQLAutoSettings()
        self.generator = FileUploadGenerator(self.settings)
    
    def test_generate_single_file_upload_mutation(self):
        """Test de génération de mutation pour téléchargement simple."""
        mutation_code = self.generator.generate_single_file_upload_mutation(TestFileModel)
        
        self.assertIn('class UploadTestFileFile', mutation_code)
        self.assertIn('file = Upload()', mutation_code)
        self.assertIn('def mutate', mutation_code)
        self.assertIn('FileUploadResult', mutation_code)
    
    def test_generate_multiple_file_upload_mutation(self):
        """Test de génération de mutation pour téléchargement multiple."""
        mutation_code = self.generator.generate_multiple_file_upload_mutation(TestFileModel)
        
        self.assertIn('class UploadMultipleTestFileFiles', mutation_code)
        self.assertIn('files = List(Upload)', mutation_code)
        self.assertIn('def mutate', mutation_code)
        self.assertIn('MultipleFileUploadResult', mutation_code)
    
    def test_generate_file_upload_types(self):
        """Test de génération des types GraphQL pour téléchargement."""
        types_code = self.generator.generate_file_upload_types()
        
        self.assertIn('class FileInfoType', types_code)
        self.assertIn('class FileUploadResultType', types_code)
        self.assertIn('class MultipleFileUploadResultType', types_code)
    
    @patch('django_graphql_auto.generators.file_uploads.VirusScanner')
    def test_process_single_file_upload_success(self, mock_scanner_class):
        """Test de traitement réussi d'un téléchargement simple."""
        # Configuration du mock scanner
        mock_scanner = Mock()
        mock_scanner.scan_uploaded_file.return_value = ScanResult(is_clean=True)
        mock_scanner_class.return_value = mock_scanner
        
        # Création d'un fichier de test
        content = b"Test file content"
        uploaded_file = InMemoryUploadedFile(
            file=BytesIO(content),
            field_name='file',
            name='test.txt',
            content_type='text/plain',
            size=len(content),
            charset=None
        )
        
        # Création d'un utilisateur de test
        user = User.objects.create_user(username='testuser', password='testpass')
        
        result = self.generator.process_single_file_upload(
            uploaded_file, 
            TestFileModel, 
            user,
            additional_fields={'name': 'Test File'}
        )
        
        self.assertIsInstance(result, FileUploadResult)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.file_info)
        self.assertEqual(result.file_info.name, 'test.txt')
    
    @patch('django_graphql_auto.generators.file_uploads.VirusScanner')
    def test_process_single_file_upload_virus_detected(self, mock_scanner_class):
        """Test de traitement avec virus détecté."""
        # Configuration du mock scanner pour détecter une menace
        mock_scanner = Mock()
        mock_scanner.scan_uploaded_file.side_effect = ThreatDetected("Test virus detected")
        mock_scanner_class.return_value = mock_scanner
        
        # Création d'un fichier de test
        content = b"Virus content"
        uploaded_file = InMemoryUploadedFile(
            file=BytesIO(content),
            field_name='file',
            name='virus.txt',
            content_type='text/plain',
            size=len(content),
            charset=None
        )
        
        # Création d'un utilisateur de test
        user = User.objects.create_user(username='testuser', password='testpass')
        
        result = self.generator.process_single_file_upload(
            uploaded_file, 
            TestFileModel, 
            user,
            additional_fields={'name': 'Virus File'}
        )
        
        self.assertIsInstance(result, FileUploadResult)
        self.assertFalse(result.success)
        self.assertIn("virus", result.error_message.lower())
    
    def test_process_multiple_file_upload(self):
        """Test de traitement de téléchargement multiple."""
        # Création de plusieurs fichiers de test
        files = []
        for i in range(3):
            content = f"Test file content {i}".encode()
            uploaded_file = InMemoryUploadedFile(
                file=BytesIO(content),
                field_name='file',
                name=f'test{i}.txt',
                content_type='text/plain',
                size=len(content),
                charset=None
            )
            files.append(uploaded_file)
        
        # Création d'un utilisateur de test
        user = User.objects.create_user(username='testuser', password='testpass')
        
        with patch('django_graphql_auto.generators.file_uploads.VirusScanner') as mock_scanner_class:
            # Configuration du mock scanner
            mock_scanner = Mock()
            mock_scanner.scan_uploaded_file.return_value = ScanResult(is_clean=True)
            mock_scanner_class.return_value = mock_scanner
            
            result = self.generator.process_multiple_file_upload(
                files, 
                TestFileModel, 
                user,
                additional_fields={'name': 'Multiple Files'}
            )
        
        self.assertIsInstance(result, MultipleFileUploadResult)
        self.assertEqual(len(result.successful_uploads), 3)
        self.assertEqual(len(result.failed_uploads), 0)
        self.assertEqual(result.total_files, 3)


class FileUploadIntegrationTest(TestCase):
    """Tests d'intégration pour le système de téléchargement."""
    
    def setUp(self):
        """Configuration des tests d'intégration."""
        self.settings = GraphQLAutoSettings()
        self.generator = FileUploadGenerator(self.settings)
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_complete_file_upload_workflow(self):
        """Test du workflow complet de téléchargement de fichier."""
        # 1. Création d'un fichier de test
        content = b"Complete workflow test content"
        uploaded_file = InMemoryUploadedFile(
            file=BytesIO(content),
            field_name='file',
            name='workflow_test.txt',
            content_type='text/plain',
            size=len(content),
            charset=None
        )
        
        # 2. Validation du fichier
        validator = FileValidator(self.settings)
        file_info = FileInfo.from_uploaded_file(uploaded_file)
        
        # Ne doit pas lever d'exception
        validator.validate_file_size(file_info, max_size=1024*1024)  # 1MB
        validator.validate_file_type(file_info, ['text/plain'])
        validator.validate_file_extension(file_info, ['.txt'])
        
        # 3. Scan antivirus (avec mock)
        with patch('django_graphql_auto.generators.file_uploads.VirusScanner') as mock_scanner_class:
            mock_scanner = Mock()
            mock_scanner.scan_uploaded_file.return_value = ScanResult(is_clean=True)
            mock_scanner_class.return_value = mock_scanner
            
            # 4. Traitement du fichier
            result = self.generator.process_single_file_upload(
                uploaded_file,
                TestFileModel,
                self.user,
                additional_fields={'name': 'Workflow Test'}
            )
        
        # 5. Vérification du résultat
        self.assertTrue(result.success)
        self.assertIsNotNone(result.file_info)
        self.assertEqual(result.file_info.name, 'workflow_test.txt')
        self.assertIsNone(result.error_message)
    
    def test_file_upload_with_validation_errors(self):
        """Test de téléchargement avec erreurs de validation."""
        # Création d'un fichier trop volumineux
        content = b"x" * (10 * 1024 * 1024)  # 10MB
        uploaded_file = InMemoryUploadedFile(
            file=BytesIO(content),
            field_name='file',
            name='large_file.txt',
            content_type='text/plain',
            size=len(content),
            charset=None
        )
        
        result = self.generator.process_single_file_upload(
            uploaded_file,
            TestFileModel,
            self.user,
            additional_fields={'name': 'Large File'},
            max_file_size=1024*1024  # 1MB limit
        )
        
        self.assertFalse(result.success)
        self.assertIn("trop volumineux", result.error_message)
    
    def test_image_upload_and_processing(self):
        """Test de téléchargement et traitement d'image."""
        # Création d'une image de test
        image = Image.new('RGB', (800, 600), color='red')
        image_bytes = BytesIO()
        image.save(image_bytes, format='JPEG')
        image_bytes.seek(0)
        
        uploaded_file = InMemoryUploadedFile(
            file=image_bytes,
            field_name='image',
            name='test_image.jpg',
            content_type='image/jpeg',
            size=len(image_bytes.getvalue()),
            charset=None
        )
        
        with patch('django_graphql_auto.generators.file_uploads.VirusScanner') as mock_scanner_class:
            mock_scanner = Mock()
            mock_scanner.scan_uploaded_file.return_value = ScanResult(is_clean=True)
            mock_scanner_class.return_value = mock_scanner
            
            result = self.generator.process_single_file_upload(
                uploaded_file,
                TestFileModel,
                self.user,
                additional_fields={'name': 'Test Image'},
                process_images=True,
                max_image_width=1024,
                max_image_height=768
            )
        
        self.assertTrue(result.success)
        self.assertEqual(result.file_info.content_type, 'image/jpeg')


if __name__ == '__main__':
    pytest.main([__file__])