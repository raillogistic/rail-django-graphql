# File Uploads & Media Management

Ce guide détaille le système de téléchargement de fichiers et de gestion des médias de `rail_django_graphql`.

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Configuration](#configuration)
3. [Téléchargement de fichiers](#téléchargement-de-fichiers)
4. [Gestion des médias](#gestion-des-médias)
5. [Sécurité](#sécurité)
6. [Backends de stockage](#backends-de-stockage)
7. [Optimisation des performances](#optimisation-des-performances)
8. [Exemples d'utilisation](#exemples-dutilisation)
9. [API Reference](#api-reference)

## Vue d'ensemble

Le système de téléchargement de fichiers et de gestion des médias fournit :

- **Téléchargement sécurisé** : Validation, scan antivirus, limitations de taille
- **Traitement d'images** : Redimensionnement, optimisation, génération de miniatures
- **Stockage flexible** : Support local, S3, CDN
- **Mutations GraphQL automatiques** : Génération automatique des mutations de téléchargement
- **Gestion des métadonnées** : Extraction et stockage des informations de fichiers

## Configuration

### Settings de base

```python
# settings.py
GRAPHQL_AUTO = {
    # Téléchargement de fichiers
    'FILE_UPLOAD_MAX_SIZE': 10 * 1024 * 1024,  # 10MB
    'FILE_UPLOAD_ALLOWED_TYPES': [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf', 'text/plain'
    ],
    'FILE_UPLOAD_ALLOWED_EXTENSIONS': [
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.txt'
    ],

    # Sécurité
    'VIRUS_SCANNING_ENABLED': True,
    'VIRUS_SCANNER_TYPE': 'clamav',  # 'clamav' ou 'mock'
    'VIRUS_SCAN_TIMEOUT': 30,
    'QUARANTINE_PATH': '/var/quarantine/',

    # Traitement d'images
    'IMAGE_PROCESSING_ENABLED': True,
    'IMAGE_MAX_WIDTH': 2048,
    'IMAGE_MAX_HEIGHT': 2048,
    'IMAGE_QUALITY': 85,
    'GENERATE_THUMBNAILS': True,

    # Stockage
    'STORAGE_BACKEND': 'local',  # 'local', 's3'
    'MEDIA_ROOT': '/media/',

    # CDN
    'CDN_ENABLED': False,
    'CDN_BASE_URL': 'https://cdn.example.com',
}
```

### Configuration S3

```python
# Pour utiliser S3 comme backend de stockage
GRAPHQL_AUTO.update({
    'STORAGE_BACKEND': 's3',
    'AWS_ACCESS_KEY_ID': 'your-access-key',
    'AWS_SECRET_ACCESS_KEY': 'your-secret-key',
    'AWS_STORAGE_BUCKET_NAME': 'your-bucket-name',
    'AWS_S3_REGION_NAME': 'us-east-1',
    'AWS_S3_CUSTOM_DOMAIN': 'your-custom-domain.com',
})
```

### Configuration ClamAV

```bash
# Installation sur Ubuntu/Debian
sudo apt-get install clamav clamav-daemon

# Mise à jour des définitions de virus
sudo freshclam

# Démarrage du daemon
sudo systemctl start clamav-daemon
```

## Téléchargement de fichiers

### Modèles Django

```python
# models.py
from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    title = models.CharField(max_length=255, verbose_name="Titre")
    file = models.FileField(upload_to='documents/', verbose_name="Fichier")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Propriétaire")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"

class Photo(models.Model):
    title = models.CharField(max_length=255, verbose_name="Titre")
    image = models.ImageField(upload_to='photos/', verbose_name="Image")
    thumbnail = models.ImageField(upload_to='thumbnails/', verbose_name="Miniature", blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Propriétaire")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Photo"
        verbose_name_plural = "Photos"
```

### Génération automatique des mutations

```python
# schema.py
from rail_django_graphql.generators.file_uploads import FileUploadGenerator
from rail_django_graphql.core.settings import GraphQLAutoSettings

settings = GraphQLAutoSettings()
file_generator = FileUploadGenerator(settings)

# Génération des mutations pour le modèle Document
document_mutations = file_generator.generate_file_upload_mutations(Document)

# Génération des mutations pour le modèle Photo avec traitement d'image
photo_mutations = file_generator.generate_file_upload_mutations(
    Photo,
    process_images=True,
    generate_thumbnails=True
)
```

### Mutations GraphQL générées

```graphql
# Téléchargement simple
mutation UploadDocument($file: Upload!, $title: String!) {
  uploadDocumentFile(file: $file, title: $title) {
    success
    fileInfo {
      name
      size
      contentType
      url
    }
    errorMessage
  }
}

# Téléchargement multiple
mutation UploadMultipleDocuments($files: [Upload!]!, $title: String!) {
  uploadMultipleDocumentFiles(files: $files, title: $title) {
    totalFiles
    successfulUploads {
      name
      size
      url
    }
    failedUploads {
      filename
      error
    }
  }
}

# Téléchargement d'image avec traitement
mutation UploadPhoto($file: Upload!, $title: String!) {
  uploadPhotoFile(file: $file, title: $title) {
    success
    fileInfo {
      name
      size
      contentType
      url
      width
      height
      thumbnails {
        size
        url
        width
        height
      }
    }
    errorMessage
  }
}
```

## Gestion des médias

### Traitement d'images

```python
from rail_django_graphql.extensions.media import MediaManager, ThumbnailSize

# Initialisation du gestionnaire de médias
media_manager = MediaManager(settings)

# Traitement d'une image téléchargée
media_info = media_manager.process_and_save_image(
    uploaded_file,
    resize_options={
        'max_width': 1920,
        'max_height': 1080
    },
    generate_thumbnails=True,
    optimize_quality=85
)

# Accès aux informations de l'image
print(f"Image sauvegardée : {media_info.filename}")
print(f"Dimensions : {media_info.width}x{media_info.height}")
print(f"URL : {media_info.url}")

# Accès aux miniatures
for thumbnail in media_info.thumbnails:
    print(f"Miniature {thumbnail.size.value} : {thumbnail.url}")
```

### Génération de miniatures

```python
from rail_django_graphql.extensions.media import ImageProcessor, ThumbnailSize

processor = ImageProcessor(settings)

# Génération d'une miniature spécifique
thumbnail_file = processor.generate_thumbnail(uploaded_file, ThumbnailSize.MEDIUM)

# Génération de toutes les miniatures
thumbnails = processor.generate_all_thumbnails(uploaded_file)

# Tailles disponibles
# ThumbnailSize.SMALL: 150x150
# ThumbnailSize.MEDIUM: 300x300
# ThumbnailSize.LARGE: 600x600
```

### Optimisation d'images

```python
# Redimensionnement
resized_file = processor.resize_image(
    uploaded_file,
    max_width=800,
    max_height=600
)

# Optimisation de la qualité
optimized_file = processor.optimize_image(
    uploaded_file,
    quality=75
)

# Conversion de format
converted_file = processor.convert_format(
    uploaded_file,
    target_format='WEBP'
)
```

## Sécurité

### Validation des fichiers

```python
from rail_django_graphql.generators.file_uploads import FileValidator, FileInfo

validator = FileValidator(settings)

# Validation de la taille
file_info = FileInfo.from_uploaded_file(uploaded_file)
validator.validate_file_size(file_info, max_size=5*1024*1024)  # 5MB

# Validation du type
allowed_types = ['image/jpeg', 'image/png']
validator.validate_file_type(file_info, allowed_types)

# Validation de l'extension
allowed_extensions = ['.jpg', '.png']
validator.validate_file_extension(file_info, allowed_extensions)

# Validation des dimensions d'image
validator.validate_image_dimensions(
    uploaded_file,
    max_width=2048,
    max_height=2048
)
```

### Scan antivirus

```python
from rail_django_graphql.extensions.virus_scanner import VirusScanner, ThreatDetected

scanner = VirusScanner(settings)

try:
    result = scanner.scan_uploaded_file(uploaded_file)
    if result.is_clean:
        print("Fichier propre")
    else:
        print(f"Menace détectée : {result.threat_name}")
except ThreatDetected as e:
    print(f"Fichier bloqué : {e}")
```

### Quarantaine

```python
# Récupération des fichiers en quarantaine
quarantine_files = scanner.get_quarantine_files()

for file_info in quarantine_files:
    print(f"Fichier : {file_info['Original filename']}")
    print(f"Menace : {file_info['Threat detected']}")
    print(f"Date : {file_info['quarantine_time']}")

# Suppression d'un fichier en quarantaine
scanner.delete_quarantine_file('/var/quarantine/suspicious_file.bin')
```

## Backends de stockage

### Stockage local

```python
from rail_django_graphql.extensions.media import LocalStorageBackend

backend = LocalStorageBackend(settings)

# Sauvegarde
filename = backend.save_file(uploaded_file, 'uploads/')

# Récupération d'URL
url = backend.get_file_url(filename)

# Vérification d'existence
exists = backend.file_exists(filename)

# Suppression
backend.delete_file(filename)
```

### Stockage S3

```python
from rail_django_graphql.extensions.media import S3StorageBackend

backend = S3StorageBackend(settings)

# Même interface que le stockage local
filename = backend.save_file(uploaded_file, 'uploads/')
url = backend.get_file_url(filename)
```

### CDN

```python
from rail_django_graphql.extensions.media import CDNManager

cdn = CDNManager(settings)

# URL CDN
cdn_url = cdn.get_cdn_url('images/photo.jpg')

# URL optimisée
optimized_url = cdn.get_optimized_url(
    'images/photo.jpg',
    width=300,
    height=200,
    quality=80
)

# Invalidation du cache
cdn.invalidate_cache(['images/photo.jpg'])
```

## Optimisation des performances

### Traitement asynchrone

```python
# tasks.py (avec Celery)
from celery import shared_task
from rail_django_graphql.extensions.media import MediaManager

@shared_task
def process_uploaded_image(file_path, model_id):
    """Traitement asynchrone d'image téléchargée."""
    media_manager = MediaManager(settings)

    # Traitement de l'image
    media_info = media_manager.process_existing_image(
        file_path,
        generate_thumbnails=True,
        optimize_quality=80
    )

    # Mise à jour du modèle
    model_instance = YourModel.objects.get(id=model_id)
    model_instance.processed_image = media_info.filename
    model_instance.save()
```

### Cache des métadonnées

```python
from django.core.cache import cache

def get_media_metadata(file_path):
    """Récupération des métadonnées avec cache."""
    cache_key = f"media_metadata:{file_path}"
    metadata = cache.get(cache_key)

    if metadata is None:
        processor = ImageProcessor(settings)
        metadata = processor.extract_metadata(file_path)
        cache.set(cache_key, metadata, timeout=3600)  # 1 heure

    return metadata
```

## Exemples d'utilisation

### Client JavaScript

```javascript
// Téléchargement simple avec Apollo Client
import { gql, useMutation } from "@apollo/client";

const UPLOAD_DOCUMENT = gql`
  mutation UploadDocument($file: Upload!, $title: String!) {
    uploadDocumentFile(file: $file, title: $title) {
      success
      fileInfo {
        name
        size
        url
      }
      errorMessage
    }
  }
`;

function DocumentUpload() {
  const [uploadDocument] = useMutation(UPLOAD_DOCUMENT);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];

    try {
      const { data } = await uploadDocument({
        variables: {
          file,
          title: "Mon document",
        },
      });

      if (data.uploadDocumentFile.success) {
        console.log("Fichier téléchargé:", data.uploadDocumentFile.fileInfo);
      } else {
        console.error("Erreur:", data.uploadDocumentFile.errorMessage);
      }
    } catch (error) {
      console.error("Erreur de téléchargement:", error);
    }
  };

  return (
    <input
      type="file"
      onChange={handleFileUpload}
      accept=".pdf,.txt,.jpg,.png"
    />
  );
}
```

### Téléchargement multiple

```javascript
const UPLOAD_MULTIPLE_PHOTOS = gql`
  mutation UploadMultiplePhotos($files: [Upload!]!, $title: String!) {
    uploadMultiplePhotoFiles(files: $files, title: $title) {
      totalFiles
      successfulUploads {
        name
        url
        thumbnails {
          size
          url
        }
      }
      failedUploads {
        filename
        error
      }
    }
  }
`;

function MultiplePhotoUpload() {
  const [uploadPhotos] = useMutation(UPLOAD_MULTIPLE_PHOTOS);

  const handleMultipleUpload = async (event) => {
    const files = Array.from(event.target.files);

    try {
      const { data } = await uploadPhotos({
        variables: {
          files,
          title: "Album photos",
        },
      });

      console.log(
        `${data.uploadMultiplePhotoFiles.successfulUploads.length} fichiers téléchargés`
      );
      console.log(
        `${data.uploadMultiplePhotoFiles.failedUploads.length} échecs`
      );
    } catch (error) {
      console.error("Erreur:", error);
    }
  };

  return (
    <input
      type="file"
      multiple
      onChange={handleMultipleUpload}
      accept="image/*"
    />
  );
}
```

### Composant React avec prévisualisation

```javascript
import React, { useState } from "react";

function ImageUploadWithPreview() {
  const [preview, setPreview] = useState(null);
  const [uploadImage] = useMutation(UPLOAD_PHOTO);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];

    if (file) {
      // Prévisualisation
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target.result);
      reader.readAsDataURL(file);

      // Téléchargement
      uploadImage({
        variables: {
          file,
          title: file.name,
        },
      }).then(({ data }) => {
        if (data.uploadPhotoFile.success) {
          console.log(
            "Image téléchargée avec miniatures:",
            data.uploadPhotoFile.fileInfo.thumbnails
          );
        }
      });
    }
  };

  return (
    <div>
      <input type="file" accept="image/*" onChange={handleFileSelect} />
      {preview && (
        <div>
          <h3>Prévisualisation :</h3>
          <img src={preview} alt="Preview" style={{ maxWidth: "300px" }} />
        </div>
      )}
    </div>
  );
}
```

## API Reference

### FileUploadGenerator

```python
class FileUploadGenerator:
    def __init__(self, settings: GraphQLAutoSettings)

    def generate_file_upload_mutations(self, model: Model, **options) -> str
    def generate_single_file_upload_mutation(self, model: Model) -> str
    def generate_multiple_file_upload_mutation(self, model: Model) -> str
    def process_single_file_upload(self, file, model, user, **kwargs) -> FileUploadResult
    def process_multiple_file_upload(self, files, model, user, **kwargs) -> MultipleFileUploadResult
```

### MediaManager

```python
class MediaManager:
    def __init__(self, settings: GraphQLAutoSettings)

    def process_and_save_image(self, file, **options) -> MediaInfo
    def get_media_info(self, file) -> MediaInfo
    def delete_media(self, media_info: MediaInfo) -> bool
    def optimize_existing_media(self, filename: str, **options) -> bool
```

### ImageProcessor

```python
class ImageProcessor:
    def __init__(self, settings: GraphQLAutoSettings)

    def resize_image(self, file, max_width: int, max_height: int) -> InMemoryUploadedFile
    def optimize_image(self, file, quality: int) -> InMemoryUploadedFile
    def generate_thumbnail(self, file, size: ThumbnailSize) -> InMemoryUploadedFile
    def generate_all_thumbnails(self, file) -> List[ThumbnailInfo]
    def convert_format(self, file, target_format: str) -> InMemoryUploadedFile
    def extract_metadata(self, file) -> Dict[str, Any]
```

### VirusScanner

```python
class VirusScanner:
    def __init__(self, settings: GraphQLAutoSettings)

    def scan_file(self, file_path: str) -> ScanResult
    def scan_uploaded_file(self, file) -> ScanResult
    def get_quarantine_files(self) -> List[Dict[str, str]]
    def delete_quarantine_file(self, quarantine_path: str) -> bool
```

### StorageBackend

```python
class StorageBackend:
    def save_file(self, file, path: str) -> str
    def delete_file(self, filename: str) -> bool
    def get_file_url(self, filename: str) -> str
    def file_exists(self, filename: str) -> bool
```

## Dépannage

### Problèmes courants

1. **Erreur de taille de fichier**

   ```
   FileValidationError: Le fichier est trop volumineux
   ```

   - Vérifiez `FILE_UPLOAD_MAX_SIZE` dans les settings
   - Vérifiez les limites du serveur web (nginx, Apache)

2. **Erreur de type de fichier**

   ```
   FileValidationError: Type de fichier non autorisé
   ```

   - Vérifiez `FILE_UPLOAD_ALLOWED_TYPES` et `FILE_UPLOAD_ALLOWED_EXTENSIONS`

3. **Erreur ClamAV**

   ```
   VirusScanError: ClamAV n'est pas disponible
   ```

   - Installez ClamAV : `sudo apt-get install clamav`
   - Ou utilisez le scanner factice : `VIRUS_SCANNER_TYPE = 'mock'`

4. **Erreur S3**
   ```
   S3StorageError: Credentials not found
   ```
   - Vérifiez `AWS_ACCESS_KEY_ID` et `AWS_SECRET_ACCESS_KEY`
   - Vérifiez les permissions du bucket S3

### Logs de débogage

```python
import logging

# Activation des logs pour le système de fichiers
logging.getLogger('rail_django_graphql.generators.file_uploads').setLevel(logging.DEBUG)
logging.getLogger('rail_django_graphql.extensions.media').setLevel(logging.DEBUG)
logging.getLogger('rail_django_graphql.extensions.virus_scanner').setLevel(logging.DEBUG)
```

### Tests de performance

```python
# Benchmark de téléchargement
import time
from django.test import TestCase

class FileUploadPerformanceTest(TestCase):
    def test_large_file_upload(self):
        start_time = time.time()

        # Téléchargement d'un fichier de 10MB
        result = self.upload_large_file()

        end_time = time.time()
        upload_time = end_time - start_time

        self.assertLess(upload_time, 30)  # Moins de 30 secondes
        self.assertTrue(result.success)
```

Ce système de téléchargement de fichiers et de gestion des médias offre une solution complète et sécurisée pour gérer les fichiers dans vos applications Django avec GraphQL.
