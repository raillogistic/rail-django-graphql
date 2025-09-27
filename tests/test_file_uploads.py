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

# Django imports
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.contrib.auth.models import User
from django.db import models

from django_graphql_auto.generators.file_uploads import (
    FileUploadGenerator,
    FileInfo,
    FileUploadResult,
    MultipleFileUploadResult,
    FileValidator,
    FileProcessor,
    FileValidationError
)
from django_graphql_auto.extensions.media import MediaProcessingError
from django_graphql_auto.extensions.virus_scanner import (
    VirusScanner, ScanResult, ThreatDetected, VirusScanError
)
from django_graphql_auto.core.settings import GraphQLAutoConfig
from tests.models import TestFileModel


# ============================================================================
# TESTS POUR LA CLASSE FILEINFO
# ============================================================================

@pytest.mark.django_db
def test_file_info_creation():
    """Test de création d'un objet FileInfo."""
    file_info = FileInfo(
        name="test.txt",
        size=1024,
        content_type="text/plain",
        extension=".txt"
    )
    
    assert file_info.name == "test.txt"
    assert file_info.size == 1024
    assert file_info.content_type == "text/plain"
    assert file_info.extension == ".txt"


@pytest.mark.django_db
def test_file_info_from_uploaded_file():
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
    
    assert file_info.name == "test.txt"
    assert file_info.size == len(content)
    assert file_info.content_type == "text/plain"
    assert file_info.extension == ".txt"


# ============================================================================
# TESTS POUR LA VALIDATION DE FICHIERS
# ============================================================================

@pytest.mark.django_db
def test_file_validator_creation():
    """Test de création d'un validateur de fichiers."""
    settings = GraphQLAutoConfig()
    validator = FileValidator(settings)
    
    assert validator.settings == settings


@pytest.mark.django_db
def test_validate_file_size_success():
    """Test de validation de taille de fichier réussie."""
    settings = GraphQLAutoConfig()
    validator = FileValidator(settings)
    
    file_info = FileInfo(
        name="small.txt",
        size=100,
        content_type="text/plain",
        extension=".txt"
    )
    
    # Ne doit pas lever d'exception
    validator.validate_file_size(file_info, max_size=1024)


@pytest.mark.django_db
def test_validate_file_size_failure():
    """Test de validation de taille de fichier échouée."""
    settings = GraphQLAutoConfig()
    validator = FileValidator(settings)
    
    file_info = FileInfo(
        name="large.txt",
        size=2048,
        content_type="text/plain",
        extension=".txt"
    )
    
    with pytest.raises(FileValidationError):
        validator.validate_file_size(file_info, max_size=1024)


@pytest.mark.django_db
def test_validate_file_type_success():
    """Test de validation de type de fichier réussie."""
    settings = GraphQLAutoConfig()
    validator = FileValidator(settings)
    
    file_info = FileInfo(
        name="document.txt",
        size=100,
        content_type="text/plain",
        extension=".txt"
    )
    
    # Ne doit pas lever d'exception
    validator.validate_file_type(file_info, allowed_types=['text/plain'])


@pytest.mark.django_db
def test_validate_file_type_failure():
    """Test de validation de type de fichier échouée."""
    settings = GraphQLAutoConfig()
    validator = FileValidator(settings)
    
    file_info = FileInfo(
        name="image.jpg",
        size=100,
        content_type="image/jpeg",
        extension=".jpg"
    )
    
    with pytest.raises(FileValidationError):
        validator.validate_file_type(file_info, allowed_types=['text/plain'])


@pytest.mark.django_db
def test_validate_file_extension_success():
    """Test de validation d'extension de fichier réussie."""
    settings = GraphQLAutoConfig()
    validator = FileValidator(settings)
    
    file_info = FileInfo(
        name="document.txt",
        size=100,
        content_type="text/plain",
        extension=".txt"
    )
    
    # Ne doit pas lever d'exception
    validator.validate_file_extension(file_info, allowed_extensions=['.txt'])


@pytest.mark.django_db
def test_validate_file_extension_failure():
    """Test de validation d'extension de fichier échouée."""
    settings = GraphQLAutoConfig()
    validator = FileValidator(settings)
    
    file_info = FileInfo(
        name="script.py",
        size=100,
        content_type="text/x-python",
        extension=".py"
    )
    
    with pytest.raises(FileValidationError):
        validator.validate_file_extension(file_info, allowed_extensions=['.txt'])


# ============================================================================
# TESTS POUR LE TRAITEMENT DE FICHIERS
# ============================================================================

@pytest.mark.django_db
def test_file_processor_creation():
    """Test de création d'un processeur de fichiers."""
    settings = GraphQLAutoConfig()
    processor = FileProcessor(settings)
    
    assert processor.settings == settings


@pytest.mark.django_db
def test_process_uploaded_file_success():
    """Test de traitement réussi d'un fichier téléchargé."""
    settings = GraphQLAutoConfig()
    processor = FileProcessor(settings)
    
    # Création d'un fichier de test
    content = b"Test file content for processing"
    uploaded_file = InMemoryUploadedFile(
        file=BytesIO(content),
        field_name='file',
        name='process_test.txt',
        content_type='text/plain',
        size=len(content),
        charset=None
    )
    
    result = processor.process_uploaded_file(uploaded_file)
    
    assert result is not None
    assert hasattr(result, 'name')
    assert result.name == 'process_test.txt'


# ============================================================================
# TESTS POUR LE GÉNÉRATEUR DE TÉLÉCHARGEMENT
# ============================================================================

@pytest.mark.django_db
def test_file_upload_generator_creation():
    """Test de création d'un générateur de téléchargement."""
    settings = GraphQLAutoConfig()
    generator = FileUploadGenerator(settings)
    
    assert generator.settings == settings


@pytest.mark.django_db
def test_generate_single_file_upload_mutation():
    """Test de génération de mutation pour téléchargement simple."""
    settings = GraphQLAutoConfig()
    generator = FileUploadGenerator(settings)
    
    mutation_code = generator.generate_single_file_upload_mutation(TestFileModel)
    
    assert 'class UploadTestFileFile' in mutation_code
    assert 'file = Upload()' in mutation_code
    assert 'def mutate' in mutation_code
    assert 'FileUploadResult' in mutation_code


@pytest.mark.django_db
def test_generate_multiple_file_upload_mutation():
    """Test de génération de mutation pour téléchargement multiple."""
    settings = GraphQLAutoConfig()
    generator = FileUploadGenerator(settings)
    
    mutation_code = generator.generate_multiple_file_upload_mutation(TestFileModel)
    
    assert 'class UploadMultipleTestFileFiles' in mutation_code
    assert 'files = List(Upload)' in mutation_code
    assert 'def mutate' in mutation_code
    assert 'MultipleFileUploadResult' in mutation_code


@pytest.mark.django_db
def test_generate_file_upload_types():
    """Test de génération des types GraphQL pour téléchargement."""
    settings = GraphQLAutoConfig()
    generator = FileUploadGenerator(settings)
    
    types_code = generator.generate_file_upload_types()
    
    assert 'class FileInfoType' in types_code
    assert 'class FileUploadResultType' in types_code
    assert 'class MultipleFileUploadResultType' in types_code


@pytest.mark.django_db
@patch('django_graphql_auto.generators.file_uploads.VirusScanner')
def test_process_single_file_upload_success(mock_scanner_class):
    """Test de traitement réussi d'un téléchargement simple."""
    # Configuration du mock scanner
    mock_scanner = Mock()
    mock_scanner.scan_uploaded_file.return_value = ScanResult(is_clean=True)
    mock_scanner_class.return_value = mock_scanner
    
    settings = GraphQLAutoConfig()
    generator = FileUploadGenerator(settings)
    
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
    
    result = generator.process_single_file_upload(
        uploaded_file,
        TestFileModel,
        user,
        additional_fields={'name': 'Test Upload'}
    )
    
    assert result.success is True
    assert result.file_info is not None
    assert result.file_info.name == 'test.txt'
    assert result.error_message is None


@pytest.mark.django_db
@patch('django_graphql_auto.generators.file_uploads.VirusScanner')
def test_process_single_file_upload_virus_detected(mock_scanner_class):
    """Test de traitement avec virus détecté."""
    # Configuration du mock scanner pour détecter un virus
    mock_scanner = Mock()
    mock_scanner.scan_uploaded_file.side_effect = ThreatDetected("Virus détecté")
    mock_scanner_class.return_value = mock_scanner
    
    settings = GraphQLAutoConfig()
    generator = FileUploadGenerator(settings)
    
    # Création d'un fichier de test
    content = b"Malicious file content"
    uploaded_file = InMemoryUploadedFile(
        file=BytesIO(content),
        field_name='file',
        name='malicious.txt',
        content_type='text/plain',
        size=len(content),
        charset=None
    )
    
    # Création d'un utilisateur de test
    user = User.objects.create_user(username='testuser', password='testpass')
    
    result = generator.process_single_file_upload(
        uploaded_file,
        TestFileModel,
        user,
        additional_fields={'name': 'Malicious Upload'}
    )
    
    assert result.success is False
    assert result.file_info is None
    assert "Virus détecté" in result.error_message


@pytest.mark.django_db
@patch('django_graphql_auto.generators.file_uploads.VirusScanner')
def test_process_multiple_file_upload(mock_scanner_class):
    """Test de traitement de téléchargement multiple."""
    # Configuration du mock scanner
    mock_scanner = Mock()
    mock_scanner.scan_uploaded_file.return_value = ScanResult(is_clean=True)
    mock_scanner_class.return_value = mock_scanner
    
    settings = GraphQLAutoConfig()
    generator = FileUploadGenerator(settings)
    
    # Création de plusieurs fichiers de test
    files = []
    for i in range(3):
        content = f"Test file content {i}".encode()
        uploaded_file = InMemoryUploadedFile(
            file=BytesIO(content),
            field_name='files',
            name=f'test_{i}.txt',
            content_type='text/plain',
            size=len(content),
            charset=None
        )
        files.append(uploaded_file)
    
    # Création d'un utilisateur de test
    user = User.objects.create_user(username='testuser', password='testpass')
    
    result = generator.process_multiple_file_upload(
        files,
        TestFileModel,
        user,
        additional_fields={'name': 'Multiple Upload Test'}
    )
    
    assert result.success is True
    assert len(result.file_infos) == 3
    assert result.error_message is None


# ============================================================================
# TESTS D'INTÉGRATION
# ============================================================================

@pytest.mark.django_db
def test_complete_file_upload_workflow():
    """Test du workflow complet de téléchargement de fichier."""
    settings = GraphQLAutoConfig()
    generator = FileUploadGenerator(settings)
    user = User.objects.create_user(username='testuser', password='testpass')
    
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
    validator = FileValidator(settings)
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
        result = generator.process_single_file_upload(
            uploaded_file,
            TestFileModel,
            user,
            additional_fields={'name': 'Workflow Test'}
        )
    
    # 5. Vérification du résultat
    assert result.success is True
    assert result.file_info is not None
    assert result.file_info.name == 'workflow_test.txt'
    assert result.error_message is None


@pytest.mark.django_db
def test_file_upload_with_validation_errors():
    """Test de téléchargement avec erreurs de validation."""
    settings = GraphQLAutoConfig()
    generator = FileUploadGenerator(settings)
    user = User.objects.create_user(username='testuser', password='testpass')
    
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
    
    # Le traitement doit échouer à cause de la taille
    result = generator.process_single_file_upload(
        uploaded_file,
        TestFileModel,
        user,
        additional_fields={'name': 'Large File Test'},
        max_file_size=1024*1024  # 1MB max
    )
    
    assert result.success is False
    assert result.file_info is None
    assert "taille" in result.error_message.lower()


@pytest.mark.django_db
@patch('PIL.Image.open')
def test_image_upload_and_processing(mock_image_open):
    """Test de téléchargement et traitement d'image."""
    # Configuration du mock PIL
    mock_image = Mock()
    mock_image.size = (800, 600)
    mock_image.format = 'JPEG'
    mock_image_open.return_value = mock_image
    
    settings = GraphQLAutoConfig()
    generator = FileUploadGenerator(settings)
    user = User.objects.create_user(username='testuser', password='testpass')
    
    # Création d'un fichier image de test
    content = b"fake jpeg content"
    uploaded_file = InMemoryUploadedFile(
        file=BytesIO(content),
        field_name='file',
        name='test_image.jpg',
        content_type='image/jpeg',
        size=len(content),
        charset=None
    )
    
    with patch('django_graphql_auto.generators.file_uploads.VirusScanner') as mock_scanner_class:
        mock_scanner = Mock()
        mock_scanner.scan_uploaded_file.return_value = ScanResult(is_clean=True)
        mock_scanner_class.return_value = mock_scanner
        
        result = generator.process_single_file_upload(
            uploaded_file,
            TestFileModel,
            user,
            additional_fields={'name': 'Image Test'}
        )
    
    assert result.success is True
    assert result.file_info is not None
    assert result.file_info.name == 'test_image.jpg'
    assert result.error_message is None
