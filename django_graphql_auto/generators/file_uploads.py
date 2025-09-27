"""
Générateur de mutations pour les téléchargements de fichiers et la gestion des médias.

Ce module fournit des fonctionnalités automatiques pour :
- Génération de mutations de téléchargement de fichiers
- Validation des types et tailles de fichiers
- Intégration avec les systèmes de stockage
- Traitement et optimisation des médias
"""

import os
import mimetypes
from typing import Dict, List, Optional, Type, Any, Union
from pathlib import Path
import hashlib
import uuid
from datetime import datetime

import graphene
from graphene import ObjectType, Mutation, Field, String, Boolean, Int, List as GrapheneList
from graphene_file_upload.scalars import Upload
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.core.files.storage import default_storage
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from ..core.settings import GraphQLAutoSettings


class FileValidationError(Exception):
    """Exception levée lors de la validation des fichiers."""
    pass


class FileInfo(graphene.ObjectType):
    """Informations sur un fichier téléchargé."""
    
    id = graphene.String(description="Identifiant unique du fichier")
    name = graphene.String(description="Nom original du fichier")
    size = graphene.Int(description="Taille du fichier en octets")
    content_type = graphene.String(description="Type MIME du fichier")
    url = graphene.String(description="URL d'accès au fichier")
    path = graphene.String(description="Chemin de stockage du fichier")
    checksum = graphene.String(description="Somme de contrôle MD5 du fichier")
    uploaded_at = graphene.DateTime(description="Date et heure de téléchargement")


class FileUploadResult(graphene.ObjectType):
    """Résultat d'un téléchargement de fichier."""
    
    ok = graphene.Boolean(description="Indique si le téléchargement a réussi")
    file = graphene.Field(FileInfo, description="Informations sur le fichier téléchargé")
    errors = graphene.List(graphene.String, description="Liste des erreurs rencontrées")


class MultipleFileUploadResult(graphene.ObjectType):
    """Résultat d'un téléchargement multiple de fichiers."""
    
    ok = graphene.Boolean(description="Indique si tous les téléchargements ont réussi")
    files = graphene.List(FileInfo, description="Liste des fichiers téléchargés avec succès")
    errors = graphene.List(graphene.String, description="Liste des erreurs rencontrées")
    failed_count = graphene.Int(description="Nombre de fichiers qui ont échoué")
    success_count = graphene.Int(description="Nombre de fichiers téléchargés avec succès")


class FileValidator:
    """Validateur pour les fichiers téléchargés."""
    
    def __init__(self, settings: GraphQLAutoSettings):
        self.settings = settings
        self.allowed_types = getattr(settings, 'ALLOWED_FILE_TYPES', [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ])
        self.max_file_size = getattr(settings, 'MAX_FILE_SIZE', 10 * 1024 * 1024)  # 10MB par défaut
        self.max_total_size = getattr(settings, 'MAX_TOTAL_UPLOAD_SIZE', 100 * 1024 * 1024)  # 100MB par défaut
        
    def validate_file(self, file: Union[InMemoryUploadedFile, TemporaryUploadedFile]) -> None:
        """
        Valide un fichier téléchargé.
        
        Args:
            file: Fichier à valider
            
        Raises:
            FileValidationError: Si le fichier ne respecte pas les critères de validation
        """
        # Validation de la taille
        if file.size > self.max_file_size:
            raise FileValidationError(
                f"Le fichier '{file.name}' est trop volumineux. "
                f"Taille maximale autorisée : {self.max_file_size / (1024*1024):.1f}MB"
            )
        
        # Validation du type MIME
        content_type = file.content_type or mimetypes.guess_type(file.name)[0]
        if content_type not in self.allowed_types:
            raise FileValidationError(
                f"Type de fichier non autorisé : {content_type}. "
                f"Types autorisés : {', '.join(self.allowed_types)}"
            )
        
        # Validation du nom de fichier
        if not file.name or len(file.name) > 255:
            raise FileValidationError("Nom de fichier invalide ou trop long")
        
        # Vérification des caractères dangereux dans le nom
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        if any(char in file.name for char in dangerous_chars):
            raise FileValidationError("Le nom de fichier contient des caractères non autorisés")
    
    def validate_multiple_files(self, files: List[Union[InMemoryUploadedFile, TemporaryUploadedFile]]) -> None:
        """
        Valide une liste de fichiers téléchargés.
        
        Args:
            files: Liste des fichiers à valider
            
        Raises:
            FileValidationError: Si les fichiers ne respectent pas les critères de validation
        """
        if not files:
            raise FileValidationError("Aucun fichier fourni")
        
        total_size = sum(file.size for file in files)
        if total_size > self.max_total_size:
            raise FileValidationError(
                f"Taille totale des fichiers trop importante. "
                f"Taille maximale autorisée : {self.max_total_size / (1024*1024):.1f}MB"
            )
        
        for file in files:
            self.validate_file(file)


class FileProcessor:
    """Processeur pour les fichiers téléchargés."""
    
    def __init__(self, settings: GraphQLAutoSettings):
        self.settings = settings
        self.upload_path = getattr(settings, 'UPLOAD_PATH', 'uploads/')
        
    def generate_file_path(self, file: Union[InMemoryUploadedFile, TemporaryUploadedFile]) -> str:
        """
        Génère un chemin unique pour le fichier.
        
        Args:
            file: Fichier téléchargé
            
        Returns:
            str: Chemin unique pour le fichier
        """
        # Génération d'un nom unique
        file_extension = Path(file.name).suffix.lower()
        unique_name = f"{uuid.uuid4().hex}{file_extension}"
        
        # Organisation par date
        now = datetime.now()
        date_path = f"{now.year}/{now.month:02d}/{now.day:02d}"
        
        return f"{self.upload_path}{date_path}/{unique_name}"
    
    def calculate_checksum(self, file: Union[InMemoryUploadedFile, TemporaryUploadedFile]) -> str:
        """
        Calcule la somme de contrôle MD5 du fichier.
        
        Args:
            file: Fichier téléchargé
            
        Returns:
            str: Somme de contrôle MD5
        """
        md5_hash = hashlib.md5()
        
        # Lecture du fichier par chunks pour économiser la mémoire
        file.seek(0)
        for chunk in iter(lambda: file.read(4096), b""):
            md5_hash.update(chunk)
        file.seek(0)
        
        return md5_hash.hexdigest()
    
    def save_file(self, file: Union[InMemoryUploadedFile, TemporaryUploadedFile]) -> FileInfo:
        """
        Sauvegarde un fichier et retourne ses informations.
        
        Args:
            file: Fichier à sauvegarder
            
        Returns:
            FileInfo: Informations sur le fichier sauvegardé
        """
        file_path = self.generate_file_path(file)
        checksum = self.calculate_checksum(file)
        
        # Sauvegarde du fichier
        saved_path = default_storage.save(file_path, file)
        file_url = default_storage.url(saved_path)
        
        return FileInfo(
            id=str(uuid.uuid4()),
            name=file.name,
            size=file.size,
            content_type=file.content_type,
            url=file_url,
            path=saved_path,
            checksum=checksum,
            uploaded_at=datetime.now()
        )


class FileUploadGenerator:
    """Générateur de mutations pour les téléchargements de fichiers."""
    
    def __init__(self, settings: GraphQLAutoSettings):
        self.settings = settings
        self.validator = FileValidator(settings)
        self.processor = FileProcessor(settings)
        
    def generate_single_upload_mutation(self) -> Type[Mutation]:
        """
        Génère une mutation pour télécharger un seul fichier.
        
        Returns:
            Type[Mutation]: Classe de mutation pour téléchargement simple
        """
        validator = self.validator
        processor = self.processor
        
        class SingleFileUpload(Mutation):
            """Mutation pour télécharger un seul fichier."""
            
            class Arguments:
                file = Upload(required=True, description="Fichier à télécharger")
                description = String(description="Description optionnelle du fichier")
            
            Output = FileUploadResult
            
            @staticmethod
            def mutate(root, info, file, description=None):
                """
                Exécute le téléchargement d'un fichier.
                
                Args:
                    root: Objet racine GraphQL
                    info: Informations de contexte GraphQL
                    file: Fichier téléchargé
                    description: Description optionnelle
                    
                Returns:
                    FileUploadResult: Résultat du téléchargement
                """
                try:
                    # Validation du fichier
                    validator.validate_file(file)
                    
                    # Traitement et sauvegarde
                    file_info = processor.save_file(file)
                    
                    return FileUploadResult(
                        ok=True,
                        file=file_info,
                        errors=[]
                    )
                    
                except FileValidationError as e:
                    return FileUploadResult(
                        ok=False,
                        file=None,
                        errors=[str(e)]
                    )
                except Exception as e:
                    return FileUploadResult(
                        ok=False,
                        file=None,
                        errors=[f"Erreur lors du téléchargement : {str(e)}"]
                    )
        
        return SingleFileUpload
    
    def generate_multiple_upload_mutation(self) -> Type[Mutation]:
        """
        Génère une mutation pour télécharger plusieurs fichiers.
        
        Returns:
            Type[Mutation]: Classe de mutation pour téléchargement multiple
        """
        validator = self.validator
        processor = self.processor
        
        class MultipleFileUpload(Mutation):
            """Mutation pour télécharger plusieurs fichiers."""
            
            class Arguments:
                files = GrapheneList(Upload, required=True, description="Liste des fichiers à télécharger")
                description = String(description="Description optionnelle des fichiers")
            
            Output = MultipleFileUploadResult
            
            @staticmethod
            def mutate(root, info, files, description=None):
                """
                Exécute le téléchargement de plusieurs fichiers.
                
                Args:
                    root: Objet racine GraphQL
                    info: Informations de contexte GraphQL
                    files: Liste des fichiers téléchargés
                    description: Description optionnelle
                    
                Returns:
                    MultipleFileUploadResult: Résultat du téléchargement multiple
                """
                uploaded_files = []
                errors = []
                
                try:
                    # Validation globale
                    validator.validate_multiple_files(files)
                    
                    # Traitement de chaque fichier
                    for file in files:
                        try:
                            file_info = processor.save_file(file)
                            uploaded_files.append(file_info)
                        except Exception as e:
                            errors.append(f"Erreur pour le fichier '{file.name}': {str(e)}")
                    
                    success_count = len(uploaded_files)
                    failed_count = len(files) - success_count
                    
                    return MultipleFileUploadResult(
                        ok=failed_count == 0,
                        files=uploaded_files,
                        errors=errors,
                        success_count=success_count,
                        failed_count=failed_count
                    )
                    
                except FileValidationError as e:
                    return MultipleFileUploadResult(
                        ok=False,
                        files=[],
                        errors=[str(e)],
                        success_count=0,
                        failed_count=len(files) if files else 0
                    )
                except Exception as e:
                    return MultipleFileUploadResult(
                        ok=False,
                        files=[],
                        errors=[f"Erreur lors du téléchargement multiple : {str(e)}"],
                        success_count=0,
                        failed_count=len(files) if files else 0
                    )
        
        return MultipleFileUpload
    
    def generate_file_mutations(self) -> Dict[str, Type[Mutation]]:
        """
        Génère toutes les mutations de fichiers.
        
        Returns:
            Dict[str, Type[Mutation]]: Dictionnaire des mutations générées
        """
        mutations = {}
        
        # Mutation de téléchargement simple
        mutations['upload_file'] = self.generate_single_upload_mutation()
        
        # Mutation de téléchargement multiple
        mutations['upload_files'] = self.generate_multiple_upload_mutation()
        
        return mutations